import type { BalanceConfig } from '../config/balance';
import type { GameWorld, Vec2 } from '../types/expedition';
import { dist } from './math';
import { isVisible } from './simulation';
import { allFriendlies } from './world';

let fogCanvas: HTMLCanvasElement | null = null;

function getFogCanvas(w: number, h: number): HTMLCanvasElement {
  if (!fogCanvas) fogCanvas = document.createElement('canvas');
  if (fogCanvas.width !== w || fogCanvas.height !== h) {
    fogCanvas.width = w;
    fogCanvas.height = h;
  }
  return fogCanvas;
}

export interface Camera {
  x: number;
  y: number;
  zoom: number;
}

export function createCamera(): Camera {
  return { x: 0, y: 0, zoom: 1 };
}

export function updateCamera(
  cam: Camera,
  follow: Vec2,
  canvasW: number,
  canvasH: number,
  worldW: number,
  worldH: number,
  dt: number,
  lerpSpeed: number,
): void {
  const targetX = follow.x - canvasW / (2 * cam.zoom);
  const targetY = follow.y - canvasH / (2 * cam.zoom);
  const t = 1 - Math.exp(-lerpSpeed * dt);
  cam.x += (targetX - cam.x) * t;
  cam.y += (targetY - cam.y) * t;
  const maxX = Math.max(0, worldW - canvasW / cam.zoom);
  const maxY = Math.max(0, worldH - canvasH / cam.zoom);
  cam.x = Math.max(0, Math.min(maxX, cam.x));
  cam.y = Math.max(0, Math.min(maxY, cam.y));
}

function worldToScreen(cam: Camera, x: number, y: number): Vec2 {
  return { x: (x - cam.x) * cam.zoom, y: (y - cam.y) * cam.zoom };
}

function drawGrid(
  ctx: CanvasRenderingContext2D,
  cam: Camera,
  canvasW: number,
  canvasH: number,
  worldW: number,
  worldH: number,
): void {
  const step = 50;
  ctx.save();
  ctx.strokeStyle = 'rgba(80, 100, 120, 0.15)';
  ctx.lineWidth = 1;
  const x0 = Math.floor(cam.x / step) * step;
  const y0 = Math.floor(cam.y / step) * step;
  for (let x = x0; x < cam.x + canvasW / cam.zoom + step; x += step) {
    if (x < 0 || x > worldW) continue;
    const s = worldToScreen(cam, x, 0);
    ctx.beginPath();
    ctx.moveTo(s.x, 0);
    ctx.lineTo(s.x, canvasH);
    ctx.stroke();
  }
  for (let y = y0; y < cam.y + canvasH / cam.zoom + step; y += step) {
    if (y < 0 || y > worldH) continue;
    const s = worldToScreen(cam, 0, y);
    ctx.beginPath();
    ctx.moveTo(0, s.y);
    ctx.lineTo(canvasW, s.y);
    ctx.stroke();
  }
  ctx.restore();
}

export function renderWorld(
  ctx: CanvasRenderingContext2D,
  world: GameWorld,
  balance: BalanceConfig,
  cam: Camera,
  revealAll: boolean,
): void {
  const { width: canvasW, height: canvasH } = ctx.canvas;

  // Ground
  ctx.fillStyle = '#1a1e24';
  ctx.fillRect(0, 0, canvasW, canvasH);
  drawGrid(ctx, cam, canvasW, canvasH, balance.worldWidth, balance.worldHeight);

  // Obstacles
  for (const o of world.obstacles) {
    const center = { x: o.x + o.w / 2, y: o.y + o.h / 2 };
    if (!isVisible(center, world, balance, revealAll)) continue;
    const s = worldToScreen(cam, o.x, o.y);
    ctx.fillStyle = '#2c333c';
    ctx.strokeStyle = '#4a5562';
    ctx.lineWidth = 2;
    ctx.fillRect(s.x, s.y, o.w * cam.zoom, o.h * cam.zoom);
    ctx.strokeRect(s.x, s.y, o.w * cam.zoom, o.h * cam.zoom);
  }

  // Extract
  if (isVisible(world.extract.pos, world, balance, revealAll)) {
    const s = worldToScreen(cam, world.extract.pos.x, world.extract.pos.y);
    const r = world.extract.radius * cam.zoom;
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.fillStyle = 'rgba(40, 180, 120, 0.25)';
    ctx.fill();
    ctx.strokeStyle = '#3dd68c';
    ctx.lineWidth = 2;
    ctx.setLineDash([6, 4]);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = '#3dd68c';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('抽出', s.x, s.y + 4);
  }

  // Containers
  for (const c of world.containers) {
    if (c.salvaged) continue;
    if (!isVisible(c.pos, world, balance, revealAll)) continue;
    const s = worldToScreen(cam, c.pos.x, c.pos.y);
    const size = 18 * cam.zoom;
    ctx.fillStyle = '#c4a35a';
    ctx.fillRect(s.x - size / 2, s.y - size / 2, size, size);
    ctx.strokeStyle = '#e8d5a3';
    ctx.lineWidth = 1.5;
    ctx.strokeRect(s.x - size / 2, s.y - size / 2, size, size);
    ctx.fillStyle = '#1a1e24';
    ctx.font = `${10 * cam.zoom}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('箱', s.x, s.y + 3 * cam.zoom);
  }

  // Enemies
  for (const e of world.enemies) {
    if (!e.alive) continue;
    if (!isVisible(e.pos, world, balance, revealAll)) continue;
    const s = worldToScreen(cam, e.pos.x, e.pos.y);
    const r = balance.unitRadius * cam.zoom;
    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.fillStyle = '#8b2e2e';
    ctx.fill();
    ctx.strokeStyle = '#ff6b6b';
    ctx.lineWidth = 2;
    ctx.stroke();
    // HP bar
    const pct = e.hp / e.maxHp;
    ctx.fillStyle = '#333';
    ctx.fillRect(s.x - r, s.y - r - 10, r * 2, 4);
    ctx.fillStyle = '#ff4444';
    ctx.fillRect(s.x - r, s.y - r - 10, r * 2 * pct, 4);
  }

  // Wingmen waypoints
  for (const w of world.wingmen) {
    if (!w.alive || !w.waypoint) continue;
    if (!isVisible(w.waypoint, world, balance, revealAll) && !revealAll) {
      // still show if we set it recently — always show own waypoints
    }
    const s = worldToScreen(cam, w.waypoint.x, w.waypoint.y);
    ctx.beginPath();
    ctx.arc(s.x, s.y, 8, 0, Math.PI * 2);
    ctx.strokeStyle = w.id === 'wingmanA' ? '#6cb6ff' : '#c9a0ff';
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = ctx.strokeStyle;
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(w.id === 'wingmanA' ? 'A' : 'B', s.x, s.y - 12);
  }

  // Friendlies
  for (const u of allFriendlies(world)) {
    if (!u.alive) continue;
    const s = worldToScreen(cam, u.pos.x, u.pos.y);
    const r = balance.unitRadius * cam.zoom;

    // Vision circle (subtle)
    if (u.isLeader) {
      ctx.beginPath();
      ctx.arc(s.x, s.y, balance.visionRange * cam.zoom, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(100, 160, 220, 0.12)';
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(s.x, s.y, balance.weaponRange * cam.zoom, 0, Math.PI * 2);
      ctx.strokeStyle = 'rgba(220, 180, 80, 0.15)';
      ctx.stroke();
    }

    // Move target line
    if (u.moveTarget) {
      const t = worldToScreen(cam, u.moveTarget.x, u.moveTarget.y);
      ctx.beginPath();
      ctx.moveTo(s.x, s.y);
      ctx.lineTo(t.x, t.y);
      ctx.strokeStyle = u.isLeader ? 'rgba(255,255,255,0.35)' : 'rgba(150,180,255,0.25)';
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    }

    ctx.beginPath();
    ctx.arc(s.x, s.y, r, 0, Math.PI * 2);
    ctx.fillStyle = u.isLeader ? '#2d6cdf' : '#3a8f6e';
    ctx.fill();
    ctx.strokeStyle = u.isLeader ? '#9ec1ff' : '#7dcea0';
    ctx.lineWidth = u.isLeader ? 3 : 2;
    ctx.stroke();

    // Facing
    ctx.beginPath();
    ctx.moveTo(s.x, s.y);
    ctx.lineTo(s.x + Math.cos(u.facing) * r * 1.4, s.y + Math.sin(u.facing) * r * 1.4);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 2;
    ctx.stroke();

    // Label
    ctx.fillStyle = '#e8eef5';
    ctx.font = `bold ${11 * cam.zoom}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText(u.isLeader ? '長' : u.id === 'wingmanA' ? 'A' : 'B', s.x, s.y + 4);

    // HP
    const pct = u.hp / u.maxHp;
    ctx.fillStyle = '#222';
    ctx.fillRect(s.x - r, s.y - r - 10, r * 2, 4);
    ctx.fillStyle = pct > 0.4 ? '#3dd68c' : '#e8a838';
    ctx.fillRect(s.x - r, s.y - r - 10, r * 2 * pct, 4);
  }

  // Fog of war overlay (simple: darken outside vision via radial punches)
  if (!revealAll) {
    const fog = getFogCanvas(canvasW, canvasH);
    const fctx = fog.getContext('2d');
    if (fctx) {
      fctx.globalCompositeOperation = 'source-over';
      fctx.clearRect(0, 0, canvasW, canvasH);
      fctx.fillStyle = 'rgba(6, 8, 12, 0.82)';
      fctx.fillRect(0, 0, canvasW, canvasH);
      fctx.globalCompositeOperation = 'destination-out';
      for (const u of allFriendlies(world)) {
        if (!u.alive) continue;
        const s = worldToScreen(cam, u.pos.x, u.pos.y);
        const grd = fctx.createRadialGradient(
          s.x,
          s.y,
          balance.visionRange * cam.zoom * 0.55,
          s.x,
          s.y,
          balance.visionRange * cam.zoom,
        );
        grd.addColorStop(0, 'rgba(0,0,0,1)');
        grd.addColorStop(1, 'rgba(0,0,0,0)');
        fctx.fillStyle = grd;
        fctx.beginPath();
        fctx.arc(s.x, s.y, balance.visionRange * cam.zoom, 0, Math.PI * 2);
        fctx.fill();
      }
      ctx.drawImage(fog, 0, 0);
    }
  }

  // World border hint
  const origin = worldToScreen(cam, 0, 0);
  const corner = worldToScreen(cam, balance.worldWidth, balance.worldHeight);
  ctx.strokeStyle = 'rgba(120,140,160,0.4)';
  ctx.lineWidth = 2;
  ctx.strokeRect(origin.x, origin.y, corner.x - origin.x, corner.y - origin.y);
}

export function screenToWorld(cam: Camera, sx: number, sy: number): Vec2 {
  return { x: sx / cam.zoom + cam.x, y: sy / cam.zoom + cam.y };
}

/** Quick LOS helper for UI hints */
export function anyHostileInWeaponRange(world: GameWorld, balance: BalanceConfig): boolean {
  if (!world.leader.alive) return false;
  return world.enemies.some(
    (e) => e.alive && dist(world.leader.pos, e.pos) <= balance.weaponRange,
  );
}
