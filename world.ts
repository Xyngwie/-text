import type { BalanceConfig } from '../config/balance';
import type {
  Container,
  Enemy,
  GameWorld,
  Obstacle,
  Unit,
} from '../types/expedition';

function makeUnit(
  id: Unit['id'],
  name: string,
  x: number,
  y: number,
  hp: number,
  isLeader: boolean,
): Unit {
  return {
    id,
    name,
    pos: { x, y },
    hp,
    maxHp: hp,
    alive: true,
    moveTarget: null,
    fireCooldown: 0,
    facing: -Math.PI / 2,
    isLeader,
    stance: isLeader ? 'escort' : 'escort',
    waypoint: null,
    carryingHint: 0,
  };
}

/** Small wreck-field layout: open areas, rubble corridors, containers, light hostiles. */
export function createWorld(balance: BalanceConfig): GameWorld {
  const spawn = { x: 140, y: balance.worldHeight - 140 };

  const obstacles: Obstacle[] = [
    // Central wreck piles
    { x: 320, y: 280, w: 140, h: 50 },
    { x: 520, y: 420, w: 60, h: 180 },
    { x: 700, y: 200, w: 160, h: 45 },
    { x: 880, y: 480, w: 50, h: 200 },
    { x: 400, y: 620, w: 200, h: 40 },
    { x: 200, y: 400, w: 80, h: 80 },
    { x: 980, y: 280, w: 120, h: 55 },
    { x: 600, y: 700, w: 90, h: 70 },
    // Edge rubble
    { x: 50, y: 50, w: 180, h: 35 },
    { x: 1000, y: 750, w: 150, h: 40 },
  ];

  const containers: Container[] = [
    { id: 'c1', pos: { x: 380, y: 180 }, salvaged: false },
    { id: 'c2', pos: { x: 640, y: 340 }, salvaged: false },
    { id: 'c3', pos: { x: 860, y: 160 }, salvaged: false },
    { id: 'c4', pos: { x: 480, y: 760 }, salvaged: false },
    { id: 'c5', pos: { x: 1050, y: 520 }, salvaged: false },
  ];

  const enemies: Enemy[] = [
    { id: 'e1', pos: { x: 450, y: 250 }, hp: balance.enemyHp, maxHp: balance.enemyHp, alive: true, fireCooldown: 0, targetId: null },
    { id: 'e2', pos: { x: 750, y: 380 }, hp: balance.enemyHp, maxHp: balance.enemyHp, alive: true, fireCooldown: 0, targetId: null },
    { id: 'e3', pos: { x: 920, y: 620 }, hp: balance.enemyHp, maxHp: balance.enemyHp, alive: true, fireCooldown: 0, targetId: null },
    { id: 'e4', pos: { x: 580, y: 560 }, hp: balance.enemyHp, maxHp: balance.enemyHp, alive: true, fireCooldown: 0, targetId: null },
  ];

  const leader = makeUnit('leader', 'ハヤテ', spawn.x, spawn.y, balance.unitHp, true);
  const wingA = makeUnit('wingmanA', 'カゲ', spawn.x - 40, spawn.y + 20, balance.unitHp, false);
  wingA.stance = 'escort';
  wingA.waypoint = { x: spawn.x, y: spawn.y };
  const wingB = makeUnit('wingmanB', 'レン', spawn.x + 40, spawn.y + 20, balance.unitHp, false);
  wingB.stance = 'patrol';
  wingB.waypoint = { x: spawn.x + 80, y: spawn.y - 40 };

  return {
    leader,
    wingmen: [wingA, wingB],
    enemies,
    containers,
    obstacles,
    extract: {
      pos: { x: balance.worldWidth - 120, y: 120 },
      radius: 48,
    },
    spawn,
    timeLeft: balance.maxOperationTimeSec,
    ammoStock: balance.ammoStock,
    salvagedContainers: 0,
    carrierCapacity: balance.carrierCapacity,
    isExtracted: false,
    phase: 'briefing',
    endReason: null,
    paused: false,
    log: ['ブリーフィング完了。残骸フィールドへ出撃せよ。', '隊長のみ直接操作。僚機は方針と地点を指示。'],
    selectedWingman: null,
    clickMode: 'move',
  };
}

export function allFriendlies(world: GameWorld): Unit[] {
  return [world.leader, ...world.wingmen];
}
