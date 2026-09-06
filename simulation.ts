import type { BalanceConfig } from '../config/balance';
import type { EndReason, GameWorld, Unit, Vec2 } from '../types/expedition';
import { dist, moveWithCollision, normalize } from './math';
import { getWingmanBrain } from './wingman/brain';
import { allFriendlies } from './world';

let simTime = 0;

export function resetSimTime(): void {
  simTime = 0;
}

function pushLog(world: GameWorld, msg: string): void {
  world.log.push(msg);
  if (world.log.length > 8) world.log.shift();
}

function endSortie(world: GameWorld, reason: EndReason): void {
  if (world.phase === 'result') return;
  world.phase = 'result';
  world.endReason = reason;
  if (reason === 'extracted') {
    world.isExtracted = true;
    pushLog(world, '抽出完了。生還！');
  } else if (reason === 'time_up') {
    pushLog(world, '活動限界。未脱出のため作戦失敗。');
  } else if (reason === 'leader_down') {
    pushLog(world, '隊長撃破。作戦失敗。');
  } else {
    pushLog(world, '分隊行動不能。作戦失敗。');
  }
}

function trySalvage(world: GameWorld, unit: Unit, balance: BalanceConfig): boolean {
  if (world.salvagedContainers >= world.carrierCapacity) return false;
  for (const c of world.containers) {
    if (c.salvaged) continue;
    if (dist(unit.pos, c.pos) <= balance.interactRadius) {
      c.salvaged = true;
      world.salvagedContainers += 1;
      unit.carryingHint += 1;
      pushLog(world, `${unit.name} がコンテナを回収（${world.salvagedContainers}/${world.carrierCapacity}）`);
      return true;
    }
  }
  return false;
}

function tryExtract(world: GameWorld, balance: BalanceConfig): boolean {
  const d = dist(world.leader.pos, world.extract.pos);
  if (d <= world.extract.radius + balance.unitRadius) {
    endSortie(world, 'extracted');
    return true;
  }
  return false;
}

function fireAt(
  world: GameWorld,
  shooter: { pos: Vec2; fireCooldown: number },
  targetPos: Vec2,
  damage: number,
  range: number,
  cooldown: number,
  isFriendlyShooter: boolean,
  onHit: (dmg: number) => void,
): void {
  if (shooter.fireCooldown > 0) return;
  if (dist(shooter.pos, targetPos) > range) return;
  if (isFriendlyShooter) {
    if (world.ammoStock <= 0) return;
    world.ammoStock -= 1;
  }
  shooter.fireCooldown = cooldown;
  onHit(damage);
}

function updateUnitMovement(
  unit: Unit,
  balance: BalanceConfig,
  dt: number,
  world: GameWorld,
): void {
  if (!unit.alive || !unit.moveTarget) return;
  const next = moveWithCollision(
    unit.pos,
    unit.moveTarget,
    balance.moveSpeed,
    dt,
    balance.unitRadius,
    world.obstacles,
    balance.worldWidth,
    balance.worldHeight,
  );
  const dx = next.x - unit.pos.x;
  const dy = next.y - unit.pos.y;
  if (Math.hypot(dx, dy) > 0.1) {
    unit.facing = Math.atan2(dy, dx);
  }
  unit.pos = next;
  if (dist(unit.pos, unit.moveTarget) < 4) {
    unit.moveTarget = null;
  }
}

function updateEnemies(world: GameWorld, balance: BalanceConfig, dt: number): void {
  const friends = allFriendlies(world).filter((u) => u.alive);
  for (const e of world.enemies) {
    if (!e.alive) continue;
    e.fireCooldown = Math.max(0, e.fireCooldown - dt);

    let nearest: Unit | null = null;
    let nearestD = Infinity;
    for (const u of friends) {
      const d = dist(e.pos, u.pos);
      if (d < nearestD) {
        nearestD = d;
        nearest = u;
      }
    }
    if (!nearest) continue;

    // Aggro if within vision-ish of any engagement
    if (nearestD < balance.visionRange * 1.15) {
      e.targetId = nearest.id;
      // Close to weapon range
      if (nearestD > balance.enemyWeaponRange * 0.75) {
        const n = normalize(nearest.pos.x - e.pos.x, nearest.pos.y - e.pos.y);
        const target = {
          x: e.pos.x + n.x * 40,
          y: e.pos.y + n.y * 40,
        };
        e.pos = moveWithCollision(
          e.pos,
          target,
          balance.enemyMoveSpeed,
          dt,
          balance.unitRadius,
          world.obstacles,
          balance.worldWidth,
          balance.worldHeight,
        );
      }
      if (nearestD <= balance.enemyWeaponRange) {
        fireAt(
          world,
          e,
          nearest.pos,
          balance.enemyDamage,
          balance.enemyWeaponRange,
          balance.enemyFireCooldownSec,
          false,
          (dmg) => {
            nearest!.hp -= dmg;
            if (nearest!.hp <= 0) {
              nearest!.hp = 0;
              nearest!.alive = false;
              pushLog(world, `${nearest!.name} が撃破された`);
              if (nearest!.isLeader) {
                endSortie(world, 'leader_down');
              } else if (!world.leader.alive && world.wingmen.every((w) => !w.alive)) {
                endSortie(world, 'squad_wiped');
              }
            }
          },
        );
      }
    }
  }
}

function updateWingmen(world: GameWorld, balance: BalanceConfig, dt: number): void {
  const brain = getWingmanBrain();
  for (const w of world.wingmen) {
    if (!w.alive) continue;
    w.fireCooldown = Math.max(0, w.fireCooldown - dt);

    const decision = brain.decide({
      self: w,
      leader: world.leader,
      enemies: world.enemies,
      containers: world.containers,
      salvagedContainers: world.salvagedContainers,
      carrierCapacity: world.carrierCapacity,
      ammoStock: world.ammoStock,
      dt,
      balance,
      time: simTime,
    });

    w.moveTarget = decision.moveTarget;
    updateUnitMovement(w, balance, dt, world);

    if (decision.trySalvage) {
      trySalvage(world, w, balance);
    }

    if (decision.fireAtEnemyId) {
      const enemy = world.enemies.find((e) => e.id === decision.fireAtEnemyId && e.alive);
      if (enemy) {
        fireAt(
          world,
          w,
          enemy.pos,
          balance.weaponDamage,
          balance.weaponRange,
          balance.fireCooldownSec,
          true,
          (dmg) => {
            enemy.hp -= dmg;
            if (enemy.hp <= 0) {
              enemy.hp = 0;
              enemy.alive = false;
              pushLog(world, `${w.name} が敵を撃破`);
            }
          },
        );
      }
    }
  }
}

export function leaderFireNearest(world: GameWorld, balance: BalanceConfig): void {
  if (!world.leader.alive || world.phase !== 'playing') return;
  let best = null as (typeof world.enemies)[0] | null;
  let bestD = Infinity;
  for (const e of world.enemies) {
    if (!e.alive) continue;
    const d = dist(world.leader.pos, e.pos);
    if (d < bestD && d <= balance.weaponRange) {
      bestD = d;
      best = e;
    }
  }
  if (!best) return;
  fireAt(
    world,
    world.leader,
    best.pos,
    balance.weaponDamage,
    balance.weaponRange,
    balance.fireCooldownSec,
    true,
    (dmg) => {
      best!.hp -= dmg;
      if (best!.hp <= 0) {
        best!.hp = 0;
        best!.alive = false;
        pushLog(world, `隊長が敵を撃破`);
      }
    },
  );
}

export function leaderInteract(world: GameWorld, balance: BalanceConfig): void {
  if (!world.leader.alive || world.phase !== 'playing') return;
  if (trySalvage(world, world.leader, balance)) return;
  tryExtract(world, balance);
}

export function setLeaderMoveTarget(world: GameWorld, pos: Vec2): void {
  if (!world.leader.alive || world.phase !== 'playing') return;
  world.leader.moveTarget = { ...pos };
}

export function setWingmanWaypoint(
  world: GameWorld,
  which: 'wingmanA' | 'wingmanB',
  pos: Vec2,
): void {
  const w = world.wingmen.find((u) => u.id === which);
  if (!w || !w.alive) return;
  w.waypoint = { ...pos };
  pushLog(world, `${w.name} にウェイポイント設定`);
}

/** Main dt tick. */
export function tick(world: GameWorld, balance: BalanceConfig, dt: number): void {
  if (world.phase !== 'playing' || world.paused) return;

  const capped = Math.min(dt, 0.05);
  simTime += capped;

  world.timeLeft -= capped;
  if (world.timeLeft <= 0) {
    world.timeLeft = 0;
    endSortie(world, 'time_up');
    return;
  }

  world.leader.fireCooldown = Math.max(0, world.leader.fireCooldown - capped);
  updateUnitMovement(world.leader, balance, capped, world);
  updateWingmen(world, balance, capped);
  updateEnemies(world, balance, capped);

  if (world.phase === 'playing' && !world.leader.alive) {
    endSortie(world, 'leader_down');
  }
}

/** Visibility: any alive friendly within visionRange. */
export function isVisible(
  pos: Vec2,
  world: GameWorld,
  balance: BalanceConfig,
  revealAll: boolean,
): boolean {
  if (revealAll) return true;
  for (const u of allFriendlies(world)) {
    if (!u.alive) continue;
    if (dist(u.pos, pos) <= balance.visionRange) return true;
  }
  return false;
}

export function getSimTime(): number {
  return simTime;
}
