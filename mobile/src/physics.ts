import { FruitEntity, FruitHalfEntity, BombEntity, Particle, SliceFlash } from './types';
import { GAME_CONSTANTS } from './config';

export function lineSegmentCircleIntersection(
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  center: { x: number; y: number },
  radius: number
): { hit: boolean; point: { x: number; y: number } | null; distance: number } {
  const dx = p2.x - p1.x;
  const dy = p2.y - p1.y;
  const lenSq = dx * dx + dy * dy;

  if (lenSq <= 0.000001) {
    const d = Math.hypot(center.x - p1.x, center.y - p1.y);
    return { hit: d <= radius, point: p1, distance: d };
  }

  const t = Math.max(
    0.0,
    Math.min(1.0, ((center.x - p1.x) * dx + (center.y - p1.y) * dy) / lenSq)
  );

  const closestX = p1.x + t * dx;
  const closestY = p1.y + t * dy;
  const dist = Math.hypot(center.x - closestX, center.y - closestY);

  return {
    hit: dist <= radius,
    point: { x: closestX, y: closestY },
    distance: dist,
  };
}

export function calculateSliceDynamics(
  p1: { x: number; y: number },
  p2: { x: number; y: number },
  center: { x: number; y: number }
) {
  let dx = p2.x - p1.x;
  let dy = p2.y - p1.y;
  let len = Math.hypot(dx, dy);

  if (len <= 0.0001) {
    dx = 1.0;
    dy = 0.0;
    len = 1.0;
  }

  const cutUnitX = dx / len;
  const cutUnitY = dy / len;

  // Unit normal perpendicular to blade stroke
  const normalX = -cutUnitY;
  const normalY = cutUnitX;

  const cutAngleRad = Math.atan2(dy, dx);
  const cutAngleDeg = (cutAngleRad * 180) / Math.PI;

  const impulseSpeed = 150.0;
  const half1Impulse = {
    x: normalX * impulseSpeed,
    y: normalY * impulseSpeed - 65.0, // Upward pop
  };
  const half2Impulse = {
    x: -normalX * impulseSpeed,
    y: -normalY * impulseSpeed - 65.0,
  };

  const sepDist = 8.0;
  const h1Offset = { x: normalX * sepDist, y: normalY * sepDist };
  const h2Offset = { x: -normalX * sepDist, y: -normalY * sepDist };

  return {
    cutAngleRad,
    cutAngleDeg,
    normal: { x: normalX, y: normalY },
    half1Impulse,
    half2Impulse,
    h1Offset,
    h2Offset,
  };
}
