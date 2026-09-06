import type { BalanceConfig } from '../config/balance';
import type { GameWorld, PlayerExpeditionState } from '../types/expedition';

/**
 * Single boundary for Module 1 → (future) Module 2 handoff.
 * v0: build result object only; no persistence / no Module 2 call.
 */
export function exportExpeditionResult(
  world: GameWorld,
  balance: BalanceConfig,
): PlayerExpeditionState {
  const salvaged = world.isExtracted ? world.salvagedContainers : 0;
  return {
    carrierCapacity: world.carrierCapacity,
    maxOperationTimeSec: balance.maxOperationTimeSec,
    ammoStock: world.ammoStock,
    isExtracted: world.isExtracted,
    salvagedContainers: salvaged,
    totalStockPieces: salvaged * 25,
    remainingTimeSec: Math.max(0, world.timeLeft),
    yield: 0,
    credits: 0,
  };
}
