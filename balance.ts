/**
 * Module 1 v0 — balance constants (single source of truth).
 * Provisional values; tweak here after playtests.
 */
export interface BalanceConfig {
  worldWidth: number;
  worldHeight: number;
  moveSpeed: number;
  visionRange: number;
  weaponRange: number;
  engageRange: number;
  maxOperationTimeSec: number;
  carrierCapacity: number;
  ammoStock: number;
  weaponDamage: number;
  fireCooldownSec: number;
  enemyHp: number;
  enemyMoveSpeed: number;
  enemyWeaponRange: number;
  enemyDamage: number;
  enemyFireCooldownSec: number;
  unitHp: number;
  unitRadius: number;
  interactRadius: number;
  obstaclePadding: number;
  escortFollowDist: number;
  patrolRadius: number;
  recoverSearchRadius: number;
  cameraLerp: number;
  showDebug: boolean;
}

export const BALANCE: BalanceConfig = {
  worldWidth: 1200,
  worldHeight: 900,
  moveSpeed: 80,
  visionRange: 180,
  weaponRange: 140,
  engageRange: 130,
  maxOperationTimeSec: 180,
  carrierCapacity: 2,
  ammoStock: 28,
  weaponDamage: 18,
  fireCooldownSec: 0.45,
  enemyHp: 40,
  enemyMoveSpeed: 45,
  enemyWeaponRange: 120,
  enemyDamage: 8,
  enemyFireCooldownSec: 0.9,
  unitHp: 100,
  unitRadius: 14,
  interactRadius: 36,
  obstaclePadding: 4,
  escortFollowDist: 55,
  patrolRadius: 70,
  recoverSearchRadius: 220,
  cameraLerp: 6,
  showDebug: false,
};

/** Mutable copy for debug sliders (runtime only). */
export function createRuntimeBalance(): BalanceConfig {
  return { ...BALANCE };
}
