/** Shared expedition result / state fields Module 1 owns (v0). */
export interface PlayerExpeditionState {
  carrierCapacity: number;
  maxOperationTimeSec: number;
  ammoStock: number;
  isExtracted: boolean;
  salvagedContainers: number;
  /** containers * 25 — display only in v0 */
  totalStockPieces: number;
  /** Remaining operation time at end (sec) */
  remainingTimeSec: number;
  /** Stub fields for Module 2/3 */
  yield: number;
  credits: number;
}

export type StanceId = 'patrol' | 'escort' | 'recover' | 'raid';

export const STANCE_LABELS: Record<StanceId, string> = {
  patrol: '哨戒',
  escort: '帯同',
  recover: '回収',
  raid: '遊撃',
};

export type UnitId = 'leader' | 'wingmanA' | 'wingmanB';

export interface Vec2 {
  x: number;
  y: number;
}

export interface Unit {
  id: UnitId;
  name: string;
  pos: Vec2;
  hp: number;
  maxHp: number;
  alive: boolean;
  moveTarget: Vec2 | null;
  fireCooldown: number;
  facing: number;
  isLeader: boolean;
  stance: StanceId;
  waypoint: Vec2 | null;
  carryingHint: number;
}

export interface Enemy {
  id: string;
  pos: Vec2;
  hp: number;
  maxHp: number;
  alive: boolean;
  fireCooldown: number;
  targetId: UnitId | null;
}

export interface Container {
  id: string;
  pos: Vec2;
  salvaged: boolean;
}

export interface Obstacle {
  x: number;
  y: number;
  w: number;
  h: number;
}

export interface ExtractPoint {
  pos: Vec2;
  radius: number;
}

export type GamePhase = 'briefing' | 'playing' | 'paused' | 'result';

export type EndReason =
  | 'extracted'
  | 'leader_down'
  | 'time_up'
  | 'squad_wiped';

export interface GameWorld {
  leader: Unit;
  wingmen: [Unit, Unit];
  enemies: Enemy[];
  containers: Container[];
  obstacles: Obstacle[];
  extract: ExtractPoint;
  spawn: Vec2;
  timeLeft: number;
  ammoStock: number;
  salvagedContainers: number;
  carrierCapacity: number;
  isExtracted: boolean;
  phase: GamePhase;
  endReason: EndReason | null;
  paused: boolean;
  log: string[];
  selectedWingman: 'wingmanA' | 'wingmanB' | null;
  clickMode: 'move' | 'waypointA' | 'waypointB';
}
