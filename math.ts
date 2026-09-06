import type { Obstacle, Vec2 } from '../types/expedition';

export function dist(a: Vec2, b: Vec2): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

export function clamp(v: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, v));
}

export function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

export function normalize(dx: number, dy: number): Vec2 {
  const len = Math.hypot(dx, dy) || 1;
  return { x: dx / len, y: dy / len };
}

export function pointInRect(p: Vec2, o: Obstacle, pad = 0): boolean {
  return (
    p.x >= o.x - pad &&
    p.x <= o.x + o.w + pad &&
    p.y >= o.y - pad &&
    p.y <= o.y + o.h + pad
  );
}

/** Circle vs AABB: push out if overlapping. */
export function resolveCircleAabb(
  pos: Vec2,
  radius: number,
  o: Obstacle,
): Vec2 {
  const nearestX = clamp(pos.x, o.x, o.x + o.w);
  const nearestY = clamp(pos.y, o.y, o.y + o.h);
  const dx = pos.x - nearestX;
  const dy = pos.y - nearestY;
  const d2 = dx * dx + dy * dy;
  if (d2 >= radius * radius) return pos;
  if (d2 === 0) {
    // Center inside rect — push along shortest axis
    const left = pos.x - o.x;
    const right = o.x + o.w - pos.x;
    const top = pos.y - o.y;
    const bottom = o.y + o.h - pos.y;
    const m = Math.min(left, right, top, bottom);
    if (m === left) return { x: o.x - radius, y: pos.y };
    if (m === right) return { x: o.x + o.w + radius, y: pos.y };
    if (m === top) return { x: pos.x, y: o.y - radius };
    return { x: pos.x, y: o.y + o.h + radius };
  }
  const d = Math.sqrt(d2);
  const push = (radius - d) / d;
  return { x: pos.x + dx * push, y: pos.y + dy * push };
}

export function moveWithCollision(
  pos: Vec2,
  target: Vec2,
  speed: number,
  dt: number,
  radius: number,
  obstacles: Obstacle[],
  worldW: number,
  worldH: number,
): Vec2 {
  const d = dist(pos, target);
  if (d < 2) return { ...pos };
  const step = Math.min(speed * dt, d);
  const n = normalize(target.x - pos.x, target.y - pos.y);
  let next = { x: pos.x + n.x * step, y: pos.y + n.y * step };

  for (const o of obstacles) {
    next = resolveCircleAabb(next, radius, o);
  }

  next.x = clamp(next.x, radius, worldW - radius);
  next.y = clamp(next.y, radius, worldH - radius);
  return next;
}
