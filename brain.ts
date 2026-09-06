/**
 * WingmanBrain — extension point for future learning / smarter policies.
 * v0 uses intentionally dumb heuristics (WingmanHeuristicBrain).
 */
import type { BalanceConfig } from '../../config/balance';
import type { Container, Enemy, StanceId, Unit, Vec2 } from '../../types/expedition';

export interface WingmanContext {
  self: Unit;
  leader: Unit;
  enemies: Enemy[];
  containers: Container[];
  salvagedContainers: number;
  carrierCapacity: number;
  ammoStock: number;
  dt: number;
  balance: BalanceConfig;
  /** Elapsed time for jittered decisions */
  time: number;
}

export interface WingmanDecision {
  moveTarget: Vec2 | null;
  /** Desire to fire at this enemy id (or null) */
  fireAtEnemyId: string | null;
  /** Desire to interact/salvage nearest container if in range */
  trySalvage: boolean;
}

export interface WingmanBrain {
  readonly id: string;
  decide(ctx: WingmanContext): WingmanDecision;
}

function dist(a: Vec2, b: Vec2): number {
  const dx = a.x - b.x;
  const dy = a.y - b.y;
  return Math.hypot(dx, dy);
}

function nearestAliveEnemy(pos: Vec2, enemies: Enemy[]): Enemy | null {
  let best: Enemy | null = null;
  let bestD = Infinity;
  for (const e of enemies) {
    if (!e.alive) continue;
    const d = dist(pos, e.pos);
    if (d < bestD) {
      bestD = d;
      best = e;
    }
  }
  return best;
}

function nearestContainer(pos: Vec2, containers: Container[], maxR?: number): Container | null {
  let best: Container | null = null;
  let bestD = Infinity;
  for (const c of containers) {
    if (c.salvaged) continue;
    const d = dist(pos, c.pos);
    if (maxR != null && d > maxR) continue;
    if (d < bestD) {
      bestD = d;
      best = c;
    }
  }
  return best;
}

/** Intentionally imperfect heuristics — bad paths, late reactions, ammo waste. */
export class WingmanHeuristicBrain implements WingmanBrain {
  readonly id = 'heuristic-v0';

  decide(ctx: WingmanContext): WingmanDecision {
    const { self, leader, enemies, containers, balance, time } = ctx;
    const stance: StanceId = self.stance;
    const wp = self.waypoint;

    let moveTarget: Vec2 | null = null;
    let fireAtEnemyId: string | null = null;
    let trySalvage = false;

    const enemy = nearestAliveEnemy(self.pos, enemies);
    const enemyDist = enemy ? dist(self.pos, enemy.pos) : Infinity;

    // Delayed / noisy reaction: ignore enemies briefly based on time jitter
    const reactionLag = (self.id === 'wingmanA' ? 0.35 : 0.55);
    const canReact = (time + (self.id === 'wingmanA' ? 0 : 0.7)) % 1.2 > reactionLag;

    switch (stance) {
      case 'patrol': {
        const center = wp ?? { ...leader.pos };
        // Orbit with slight wobble (dumb path)
        const angle = time * 0.7 + (self.id === 'wingmanA' ? 0 : Math.PI);
        const wobble = Math.sin(time * 2.3) * 12;
        moveTarget = {
          x: center.x + Math.cos(angle) * (balance.patrolRadius + wobble),
          y: center.y + Math.sin(angle) * (balance.patrolRadius + wobble),
        };
        if (canReact && enemy && enemyDist < balance.engageRange * 1.1) {
          fireAtEnemyId = enemy.id;
          // Sometimes drift toward enemy instead of holding patrol (wasteful)
          if (enemyDist > balance.weaponRange * 0.6 && Math.sin(time * 3) > 0.2) {
            moveTarget = { ...enemy.pos };
          }
        }
        break;
      }
      case 'escort': {
        // Follow leader with lag offset — often overcrowds / wrong side
        const lag = self.id === 'wingmanA' ? -0.9 : 1.1;
        const ox = Math.cos(leader.facing + lag) * balance.escortFollowDist;
        const oy = Math.sin(leader.facing + lag) * balance.escortFollowDist;
        // Extra delay: chase a slightly stale offset
        moveTarget = {
          x: leader.pos.x + ox + Math.sin(time) * 8,
          y: leader.pos.y + oy + Math.cos(time * 0.8) * 8,
        };
        if (canReact && enemy && enemyDist < balance.engageRange) {
          fireAtEnemyId = enemy.id;
        }
        break;
      }
      case 'recover': {
        const searchOrigin = wp ?? self.pos;
        const capFull = ctx.salvagedContainers >= ctx.carrierCapacity;
        if (capFull) {
          // Misjudge: still wander toward waypoint instead of extract
          moveTarget = wp ?? { ...leader.pos };
        } else {
          const c = nearestContainer(searchOrigin, containers, balance.recoverSearchRadius)
            ?? nearestContainer(self.pos, containers);
          if (c) {
            moveTarget = { ...c.pos };
            if (dist(self.pos, c.pos) < balance.interactRadius) {
              trySalvage = true;
            }
          } else {
            moveTarget = wp ?? { ...leader.pos };
          }
        }
        // Occasional panic fire if very close
        if (enemy && enemyDist < balance.weaponRange * 0.7 && canReact) {
          fireAtEnemyId = enemy.id;
        }
        break;
      }
      case 'raid': {
        if (enemy) {
          // Reckless close-in — often inside ideal range
          const rush = balance.weaponRange * 0.35;
          const dx = enemy.pos.x - self.pos.x;
          const dy = enemy.pos.y - self.pos.y;
          const d = Math.hypot(dx, dy) || 1;
          moveTarget = {
            x: enemy.pos.x - (dx / d) * rush,
            y: enemy.pos.y - (dy / d) * rush,
          };
          if (enemyDist < balance.engageRange * 1.3) {
            fireAtEnemyId = enemy.id; // ammo waste OK
          }
        } else {
          moveTarget = wp ?? {
            x: leader.pos.x + Math.cos(time) * 100,
            y: leader.pos.y + Math.sin(time) * 100,
          };
        }
        break;
      }
    }

    return { moveTarget, fireAtEnemyId, trySalvage };
  }
}

/** Default brain factory — swap implementation later without touching sim. */
let activeBrain: WingmanBrain = new WingmanHeuristicBrain();

export function getWingmanBrain(): WingmanBrain {
  return activeBrain;
}

export function setWingmanBrain(brain: WingmanBrain): void {
  activeBrain = brain;
}
