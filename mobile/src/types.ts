export type GameMode = 'CLASSIC' | 'TIME_CHALLENGE' | 'PRACTICE';
export type GameState = 'MENU' | 'PLAYING' | 'PAUSED' | 'GAME_OVER';

export interface FruitConfig {
  name: string;
  radius: number;
  points: number;
  colorOuter: string;
  colorInner: string;
  juiceColor: string;
  seedColor: string;
  mass: number;
  spawnWeight: number;
}

export interface FruitEntity {
  id: string;
  type: string;
  config: FruitConfig;
  x: number;
  y: number;
  vx: number;
  vy: number;
  angle: number;
  angularVelocity: number;
  isSliced: boolean;
  hasPeaked: boolean;
  radius: number;
}

export interface FruitHalfEntity {
  id: string;
  type: string;
  config: FruitConfig;
  x: number;
  y: number;
  vx: number;
  vy: number;
  angle: number;
  angularVelocity: number;
  halfIndex: 1 | 2;
  radius: number;
}

export interface BombEntity {
  id: string;
  x: number;
  y: number;
  vx: number;
  vy: number;
  angle: number;
  angularVelocity: number;
  radius: number;
  isSliced: boolean;
  fuseTimer: number;
}

export interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  color: string;
  radius: number;
  initialRadius: number;
  lifetime: number;
  maxLifetime: number;
  gravity: number;
}

export interface SliceFlash {
  p1: { x: number; y: number };
  p2: { x: number; y: number };
  lifetime: number;
  maxLifetime: number;
}

export interface FloatingText {
  id: string;
  text: string;
  x: number;
  y: number;
  color: string;
  lifetime: number;
  maxLifetime: number;
  vy: number;
}

export interface HandTrackingResult {
  detected: boolean;
  tip: { x: number; y: number } | null;
  landmarks: { x: number; y: number; z: number }[];
  currentSpeed: number;
  isSlicing: boolean;
}

export interface GameSummary {
  mode: GameMode;
  finalScore: number;
  highScore: number;
  fruitsSliced: number;
  fruitsMissed: number;
  bombHits: number;
  highestCombo: number;
  combosAwarded: number;
  accuracyPct: number;
  livesLeft: number;
  timeRemaining: number;
}
