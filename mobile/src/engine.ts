import {
  GameMode,
  GameState,
  FruitEntity,
  FruitHalfEntity,
  BombEntity,
  Particle,
  SliceFlash,
  FloatingText,
  GameSummary,
} from './types';
import { FRUITS_CONFIG, BOMB_CONFIG, GAME_CONSTANTS } from './config';
import { lineSegmentCircleIntersection, calculateSliceDynamics } from './physics';
import { soundManager } from './audio';

export class MobileGameEngine {
  private canvas: HTMLCanvasElement;
  private ctx: CanvasRenderingContext2D;

  public state: GameState = 'MENU';
  public mode: GameMode = 'CLASSIC';
  public score: number = 0;
  public highScore: number = 0;
  public lives: number = GAME_CONSTANTS.DEFAULT_LIVES;
  public timeRemaining: number = GAME_CONSTANTS.DEFAULT_ROUND_TIME;

  // Stats
  public totalFruitsSliced: number = 0;
  public totalFruitsMissed: number = 0;
  public bombHits: number = 0;
  public highestCombo: number = 0;
  public combosAwarded: number = 0;

  // Entities
  public fruits: FruitEntity[] = [];
  public halves: FruitHalfEntity[] = [];
  public bombs: BombEntity[] = [];
  public particles: Particle[] = [];
  public flashes: SliceFlash[] = [];
  public floatingTexts: FloatingText[] = [];

  // Spawner
  private spawnTimer: number = 0;
  private nextInterval: number = GAME_CONSTANTS.INITIAL_SPAWN_INTERVAL;
  private elapsedGameTime: number = 0;

  // Combo system
  private recentSlices: { time: number; type: string; points: number }[] = [];

  // Touch fallback blade trail
  private touchTrail: { x: number; y: number; time: number }[] = [];
  private isTouching: boolean = false;

  private fruitKeys = Object.keys(FRUITS_CONFIG);
  private fruitWeights = this.fruitKeys.map((k) => FRUITS_CONFIG[k].spawnWeight);

  // Cached sprite images
  private fruitImages: Record<string, HTMLImageElement> = {};
  private half1Images: Record<string, HTMLImageElement> = {};
  private half2Images: Record<string, HTMLImageElement> = {};
  private bombImage: HTMLImageElement | null = null;

  constructor(canvas: HTMLCanvasElement) {
    this.canvas = canvas;
    const context = canvas.getContext('2d');
    if (!context) throw new Error('Could not get 2D rendering context');
    this.ctx = context;

    this.loadHighScore();
    this.preloadAssets();
    this.initTouchHandlers();
  }

  private loadHighScore() {
    try {
      const saved = localStorage.getItem('fruit_ninja_highscore');
      if (saved) this.highScore = parseInt(saved, 10) || 0;
    } catch (_) {}
  }

  private saveHighScore() {
    try {
      localStorage.setItem('fruit_ninja_highscore', this.highScore.toString());
    } catch (_) {}
  }

  private preloadAssets() {
    this.fruitKeys.forEach((key) => {
      const img = new Image();
      img.src = `./assets/fruits/${key}.png`;
      this.fruitImages[key] = img;

      const h1 = new Image();
      h1.src = `./assets/sliced_fruits/${key}_half_1.png`;
      this.half1Images[key] = h1;

      const h2 = new Image();
      h2.src = `./assets/sliced_fruits/${key}_half_2.png`;
      this.half2Images[key] = h2;
    });

    const bImg = new Image();
    bImg.src = './assets/bombs/bomb.png';
    this.bombImage = bImg;
  }

  private initTouchHandlers() {
    const getPos = (e: PointerEvent) => {
      const rect = this.canvas.getBoundingClientRect();
      return {
        x: (e.clientX - rect.left) * (this.canvas.width / rect.width),
        y: (e.clientY - rect.top) * (this.canvas.height / rect.height),
      };
    };

    this.canvas.addEventListener('pointerdown', (e) => {
      this.isTouching = true;
      const p = getPos(e);
      this.touchTrail = [{ x: p.x, y: p.y, time: performance.now() }];
    });

    this.canvas.addEventListener('pointermove', (e) => {
      if (!this.isTouching) return;
      const p = getPos(e);
      const now = performance.now();
      this.touchTrail.push({ x: p.x, y: p.y, time: now });
      if (this.touchTrail.length > GAME_CONSTANTS.BLADE_TRAIL_LENGTH) {
        this.touchTrail.shift();
      }
    });

    const endTouch = () => {
      this.isTouching = false;
      this.touchTrail = [];
    };

    this.canvas.addEventListener('pointerup', endTouch);
    this.canvas.addEventListener('pointercancel', endTouch);
    this.canvas.addEventListener('pointerleave', endTouch);
  }

  public startGame(mode: GameMode = 'CLASSIC') {
    this.mode = mode;
    this.score = 0;
    this.lives = mode === 'CLASSIC' ? GAME_CONSTANTS.DEFAULT_LIVES : 999;
    this.timeRemaining = GAME_CONSTANTS.DEFAULT_ROUND_TIME;
    this.totalFruitsSliced = 0;
    this.totalFruitsMissed = 0;
    this.bombHits = 0;
    this.highestCombo = 0;
    this.combosAwarded = 0;

    this.fruits = [];
    this.halves = [];
    this.bombs = [];
    this.particles = [];
    this.flashes = [];
    this.floatingTexts = [];
    this.recentSlices = [];

    this.spawnTimer = 0;
    this.nextInterval = GAME_CONSTANTS.INITIAL_SPAWN_INTERVAL;
    this.elapsedGameTime = 0;

    this.state = 'PLAYING';
    soundManager.playSwoosh();
  }

  public resetToMenu() {
    this.state = 'MENU';
    this.fruits = [];
    this.halves = [];
    this.bombs = [];
    this.particles = [];
    this.flashes = [];
    this.floatingTexts = [];
    this.recentSlices = [];
    this.touchTrail = [];
    this.spawnTimer = 0;
  }

  public update(dt: number, bladeTrail: { x: number; y: number; time: number }[], isBladeSlicing: boolean) {
    if (this.state !== 'PLAYING') {
      this.updateParticles(dt);
      return;
    }

    this.elapsedGameTime += dt;

    // Timer mode
    if (this.mode === 'TIME_CHALLENGE') {
      this.timeRemaining -= dt;
      if (this.timeRemaining <= 0) {
        this.timeRemaining = 0;
        this.state = 'GAME_OVER';
        soundManager.playGameOver();
        return;
      }
    }

    // Check lives
    if (this.lives <= 0) {
      this.lives = 0;
      this.state = 'GAME_OVER';
      soundManager.playGameOver();
      return;
    }

    // Spawning
    this.updateSpawner(dt);

    // Update active fruits
    this.fruits = this.fruits.filter((f) => {
      f.vy += GAME_CONSTANTS.GRAVITY * dt;
      f.x += f.vx * dt;
      f.y += f.vy * dt;
      f.angle += f.angularVelocity * dt;

      if (f.vy > 0 && !f.hasPeaked) f.hasPeaked = true;

      const isOff = f.y > this.canvas.height + f.radius + 30 && f.vy > 0;
      if (isOff && !f.isSliced && this.mode === 'CLASSIC') {
        this.totalFruitsMissed++;
        this.lives--;
      }
      return !isOff && !f.isSliced;
    });

    // Update bombs
    this.bombs = this.bombs.filter((b) => {
      b.vy += GAME_CONSTANTS.GRAVITY * dt;
      b.x += b.vx * dt;
      b.y += b.vy * dt;
      b.angle += b.angularVelocity * dt;
      b.fuseTimer += dt;
      return !(b.y > this.canvas.height + b.radius + 30 && b.vy > 0) && !b.isSliced;
    });

    // Update halves
    this.halves = this.halves.filter((h) => {
      h.vy += GAME_CONSTANTS.GRAVITY * dt;
      h.x += h.vx * dt;
      h.y += h.vy * dt;
      h.angle += h.angularVelocity * dt;
      return !(h.y > this.canvas.height + h.radius + 40 && h.vy > 0);
    });

    // Collision Detection: use hand blade trail OR touch fallback trail
    const activeTrail = isBladeSlicing && bladeTrail.length >= 2 ? bladeTrail : this.touchTrail;
    const isSlicingActive = isBladeSlicing || (this.isTouching && this.touchTrail.length >= 2);

    if (isSlicingActive && activeTrail.length >= 2) {
      this.checkCollisions(activeTrail);
    }

    this.updateParticles(dt);
  }

  private checkCollisions(trail: { x: number; y: number }[]) {
    // Generate recent stroke segments
    const segments: [{ x: number; y: number }, { x: number; y: number }][] = [];
    const pts = trail.slice(-4);
    for (let i = 0; i < pts.length - 1; i++) {
      segments.push([pts[i], pts[i + 1]]);
    }

    if (segments.length === 0) return;

    // Test fruits
    this.fruits.forEach((fruit) => {
      if (fruit.isSliced) return;

      for (const [p1, p2] of segments) {
        const { hit, point } = lineSegmentCircleIntersection(p1, p2, fruit, fruit.radius);
        if (hit) {
          fruit.isSliced = true;
          this.totalFruitsSliced++;

          const dyn = calculateSliceDynamics(p1, p2, fruit);

          // Halves
          const h1: FruitHalfEntity = {
            id: Math.random().toString(),
            type: fruit.type,
            config: fruit.config,
            x: fruit.x + dyn.h1Offset.x,
            y: fruit.y + dyn.h1Offset.y,
            vx: fruit.vx + dyn.half1Impulse.x,
            vy: fruit.vy + dyn.half1Impulse.y,
            angle: dyn.cutAngleDeg,
            angularVelocity: -(160 + Math.random() * 200),
            halfIndex: 1,
            radius: fruit.radius,
          };

          const h2: FruitHalfEntity = {
            id: Math.random().toString(),
            type: fruit.type,
            config: fruit.config,
            x: fruit.x + dyn.h2Offset.x,
            y: fruit.y + dyn.h2Offset.y,
            vx: fruit.vx + dyn.half2Impulse.x,
            vy: fruit.vy + dyn.half2Impulse.y,
            angle: dyn.cutAngleDeg,
            angularVelocity: 160 + Math.random() * 200,
            halfIndex: 2,
            radius: fruit.radius,
          };

          this.halves.push(h1, h2);

          // Particles
          const hitX = point ? point.x : fruit.x;
          const hitY = point ? point.y : fruit.y;
          this.emitJuice(hitX, hitY, fruit.config.juiceColor, dyn.normal);
          this.flashes.push({ p1, p2, lifetime: 0.16, maxLifetime: 0.16 });

          // Scoring and Combos
          const now = performance.now();
          this.recentSlices.push({ time: now, type: fruit.type, points: fruit.config.points });
          this.recentSlices = this.recentSlices.filter((s) => (now - s.time) / 1000 <= GAME_CONSTANTS.COMBO_TIME_WINDOW);

          let ptsAwarded = fruit.config.points;
          const comboCount = this.recentSlices.length;

          if (comboCount >= GAME_CONSTANTS.COMBO_MIN_FRUITS) {
            const bonus = comboCount * 3;
            ptsAwarded += bonus;
            this.combosAwarded++;
            if (comboCount > this.highestCombo) this.highestCombo = comboCount;
            soundManager.playCombo();
            this.floatingTexts.push({
              id: Math.random().toString(),
              text: `${comboCount}x COMBO! +${bonus}`,
              x: hitX,
              y: hitY - 30,
              color: '#ffe12d',
              lifetime: 1.1,
              maxLifetime: 1.1,
              vy: -60,
            });
          } else {
            soundManager.playSlice();
            soundManager.playSplat();
            this.floatingTexts.push({
              id: Math.random().toString(),
              text: `+${ptsAwarded}`,
              x: hitX,
              y: hitY - 20,
              color: '#ffffff',
              lifetime: 0.8,
              maxLifetime: 0.8,
              vy: -50,
            });
          }

          this.score += ptsAwarded;
          if (this.score > this.highScore) {
            this.highScore = this.score;
            this.saveHighScore();
          }

          break;
        }
      }
    });

    // Test bombs
    this.bombs.forEach((bomb) => {
      if (bomb.isSliced) return;

      for (const [p1, p2] of segments) {
        const { hit } = lineSegmentCircleIntersection(p1, p2, bomb, bomb.radius);
        if (hit) {
          bomb.isSliced = true;
          this.bombHits++;
          soundManager.playExplosion();
          this.emitExplosion(bomb.x, bomb.y);

          if (this.mode === 'CLASSIC') {
            this.lives = 0;
            this.state = 'GAME_OVER';
            soundManager.playGameOver();
          } else if (this.mode === 'TIME_CHALLENGE') {
            this.score = Math.max(0, this.score - BOMB_CONFIG.penaltyScore);
            this.timeRemaining = Math.max(0, this.timeRemaining - 3.0);
            this.floatingTexts.push({
              id: Math.random().toString(),
              text: 'BOMB HIT! -15',
              x: bomb.x,
              y: bomb.y - 30,
              color: '#ff4155',
              lifetime: 1.2,
              maxLifetime: 1.2,
              vy: -60,
            });
          }
          break;
        }
      }
    });
  }

  private updateSpawner(dt: number) {
    this.spawnTimer += dt;
    const progress = Math.min(1.0, this.elapsedGameTime / GAME_CONSTANTS.DIFFICULTY_RAMP_DURATION);
    const targetInterval =
      GAME_CONSTANTS.INITIAL_SPAWN_INTERVAL -
      progress * (GAME_CONSTANTS.INITIAL_SPAWN_INTERVAL - GAME_CONSTANTS.MIN_SPAWN_INTERVAL);

    if (this.spawnTimer >= this.nextInterval) {
      this.spawnTimer = 0;
      this.nextInterval = targetInterval * (0.85 + Math.random() * 0.3);

      if (this.fruits.length >= GAME_CONSTANTS.MAX_CONCURRENT_FRUITS) return;

      const waveSize = progress < 0.3 ? 1 : progress < 0.7 ? 2 : Math.random() < 0.6 ? 2 : 3;
      const spawnBomb = this.mode === 'CLASSIC' && Math.random() < (0.15 + progress * 0.2);

      for (let i = 0; i < waveSize; i++) {
        const startX = 60 + Math.random() * (this.canvas.width - 120);
        const startY = this.canvas.height + 40;
        const centerOffset = this.canvas.width / 2 - startX;
        const vx = centerOffset * 0.4 + (Math.random() * 260 - 130);
        const vy = -(680 + Math.random() * 220);

        if (spawnBomb && i === 0) {
          this.bombs.push({
            id: Math.random().toString(),
            x: startX,
            y: startY,
            vx: vx * 0.85,
            vy: vy * 0.95,
            angle: 0,
            angularVelocity: (Math.random() - 0.5) * 120,
            radius: BOMB_CONFIG.radius,
            isSliced: false,
            fuseTimer: 0,
          });
        } else {
          // Weighted random fruit
          let rnd = Math.random() * this.fruitWeights.reduce((a, b) => a + b, 0);
          let chosenKey = this.fruitKeys[0];
          for (let k = 0; k < this.fruitKeys.length; k++) {
            rnd -= this.fruitWeights[k];
            if (rnd <= 0) {
              chosenKey = this.fruitKeys[k];
              break;
            }
          }

          const cfg = FRUITS_CONFIG[chosenKey];
          this.fruits.push({
            id: Math.random().toString(),
            type: chosenKey,
            config: cfg,
            x: startX,
            y: startY,
            vx,
            vy,
            angle: Math.random() * 360,
            angularVelocity: (Math.random() - 0.5) * 200,
            isSliced: false,
            hasPeaked: false,
            radius: cfg.radius,
          });
        }
      }
    }
  }

  private emitJuice(x: number, y: number, color: string, normal?: { x: number; y: number }) {
    for (let i = 0; i < 30; i++) {
      let angle = Math.random() * Math.PI * 2;
      if (normal && Math.random() < 0.65) {
        const sign = Math.random() < 0.5 ? 1 : -1;
        angle = Math.atan2(normal.y * sign, normal.x * sign) + (Math.random() - 0.5);
      }
      const speed = 120 + Math.random() * 320;
      this.particles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 50,
        color,
        radius: 3 + Math.random() * 5,
        initialRadius: 3 + Math.random() * 5,
        lifetime: 0.4 + Math.random() * 0.5,
        maxLifetime: 0.4 + Math.random() * 0.5,
        gravity: 600,
      });
    }
  }

  private emitExplosion(x: number, y: number) {
    const colors = ['#ffe12d', '#ff8c00', '#ff3228', '#e6e6fa'];
    for (let i = 0; i < 60; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 140 + Math.random() * 450;
      this.particles.push({
        x,
        y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        color: colors[Math.floor(Math.random() * colors.length)],
        radius: 4 + Math.random() * 6,
        initialRadius: 4 + Math.random() * 6,
        lifetime: 0.4 + Math.random() * 0.4,
        maxLifetime: 0.4 + Math.random() * 0.4,
        gravity: 250,
      });
    }
  }

  private updateParticles(dt: number) {
    this.particles = this.particles.filter((p) => {
      p.lifetime -= dt;
      if (p.lifetime <= 0) return false;
      p.vy += p.gravity * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.radius = Math.max(1, p.initialRadius * (p.lifetime / p.maxLifetime));
      return true;
    });

    this.flashes = this.flashes.filter((f) => {
      f.lifetime -= dt;
      return f.lifetime > 0;
    });

    this.floatingTexts = this.floatingTexts.filter((t) => {
      t.lifetime -= dt;
      t.y += t.vy * dt;
      return t.lifetime > 0;
    });
  }

  public render(
    bladeTrail: { x: number; y: number; time?: number }[],
    isBladeSlicing: boolean
  ) {
    const ctx = this.ctx;
    ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

    // 1. Render Halves
    this.halves.forEach((h) => {
      ctx.save();
      ctx.translate(h.x, h.y);
      ctx.rotate((h.angle * Math.PI) / 180);

      const cached = h.halfIndex === 1 ? this.half1Images[h.type] : this.half2Images[h.type];
      if (cached && cached.complete && cached.naturalWidth > 0) {
        ctx.drawImage(cached, -h.radius, -h.radius, h.radius * 2, h.radius * 2);
      } else {
        // Procedural half fallback
        ctx.fillStyle = h.config.colorOuter;
        ctx.beginPath();
        const start = h.halfIndex === 1 ? Math.PI : 0;
        const end = h.halfIndex === 1 ? Math.PI * 2 : Math.PI;
        ctx.arc(0, 0, h.radius, start, end);
        ctx.fill();

        ctx.fillStyle = h.config.colorInner;
        ctx.beginPath();
        ctx.arc(0, 0, h.radius * 0.88, start, end);
        ctx.fill();

        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.moveTo(-h.radius, 0);
        ctx.lineTo(h.radius, 0);
        ctx.stroke();
      }
      ctx.restore();
    });

    // 2. Render Whole Fruits
    this.fruits.forEach((f) => {
      ctx.save();
      ctx.translate(f.x, f.y);
      ctx.rotate((f.angle * Math.PI) / 180);

      const cached = this.fruitImages[f.type];
      if (cached && cached.complete && cached.naturalWidth > 0) {
        ctx.drawImage(cached, -f.radius, -f.radius, f.radius * 2, f.radius * 2);
      } else {
        // Procedural fruit fallback
        ctx.fillStyle = f.config.colorOuter;
        ctx.beginPath();
        ctx.arc(0, 0, f.radius, 0, Math.PI * 2);
        ctx.fill();

        ctx.fillStyle = f.config.colorInner;
        ctx.beginPath();
        ctx.arc(0, 0, f.radius * 0.88, 0, Math.PI * 2);
        ctx.fill();

        // 3D Highlight
        ctx.fillStyle = 'rgba(255, 255, 255, 0.45)';
        ctx.beginPath();
        ctx.arc(-f.radius * 0.35, -f.radius * 0.35, f.radius * 0.22, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.restore();
    });

    // 3. Render Bombs
    this.bombs.forEach((b) => {
      ctx.save();
      ctx.translate(b.x, b.y);
      ctx.rotate((b.angle * Math.PI) / 180);

      if (this.bombImage && this.bombImage.complete && this.bombImage.naturalWidth > 0) {
        ctx.drawImage(this.bombImage, -b.radius, -b.radius, b.radius * 2, b.radius * 2);
      } else {
        ctx.fillStyle = BOMB_CONFIG.colorBody;
        ctx.strokeStyle = BOMB_CONFIG.colorRim;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(0, 0, b.radius, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
      }

      // Spark animation on fuse
      const sparkR = 4 + Math.random() * 4;
      ctx.fillStyle = BOMB_CONFIG.fuseSparkColor;
      ctx.beginPath();
      ctx.arc(14, -b.radius - 12, sparkR, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    // 4. Slice Flashes
    this.flashes.forEach((f) => {
      const alpha = f.lifetime / f.maxLifetime;
      ctx.strokeStyle = `rgba(0, 230, 255, ${alpha * 0.8})`;
      ctx.lineWidth = 5 * alpha;
      ctx.beginPath();
      ctx.moveTo(f.p1.x, f.p1.y);
      ctx.lineTo(f.p2.x, f.p2.y);
      ctx.stroke();

      ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
      ctx.lineWidth = 2 * alpha;
      ctx.beginPath();
      ctx.moveTo(f.p1.x, f.p1.y);
      ctx.lineTo(f.p2.x, f.p2.y);
      ctx.stroke();
    });

    // 5. Particles
    this.particles.forEach((p) => {
      const alpha = p.lifetime / p.maxLifetime;
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    });

    // 6. Floating Text
    this.floatingTexts.forEach((t) => {
      const alpha = Math.max(0, t.lifetime / t.maxLifetime);
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.font = 'bold 22px -apple-system, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillStyle = t.color;
      ctx.fillText(t.text, t.x, t.y);
      ctx.restore();
    });

    // 7. Blade Glowing Trail (Hand or Touch)
    const activeTrail = isBladeSlicing && bladeTrail.length >= 2 ? bladeTrail : this.touchTrail;
    const isSlicingActive = isBladeSlicing || (this.isTouching && this.touchTrail.length >= 2);

    if (activeTrail.length >= 2) {
      for (let i = 0; i < activeTrail.length - 1; i++) {
        const p1 = activeTrail[i];
        const p2 = activeTrail[i + 1];
        const progress = (i + 1) / activeTrail.length;
        const width = 14 * progress * (isSlicingActive ? 1.3 : 1.0);

        // Glow
        ctx.strokeStyle = 'rgba(0, 225, 255, 0.45)';
        ctx.lineWidth = width + 6;
        ctx.lineCap = 'round';
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();

        // Core
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = Math.max(2, width * 0.4);
        ctx.beginPath();
        ctx.moveTo(p1.x, p1.y);
        ctx.lineTo(p2.x, p2.y);
        ctx.stroke();
      }

      const tip = activeTrail[activeTrail.length - 1];
      ctx.fillStyle = '#00e6ff';
      ctx.beginPath();
      ctx.arc(tip.x, tip.y, 10, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = '#ffffff';
      ctx.beginPath();
      ctx.arc(tip.x, tip.y, 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  public getSummary(): GameSummary {
    const total = this.totalFruitsSliced + this.totalFruitsMissed;
    const acc = total > 0 ? Math.round((this.totalFruitsSliced / total) * 1000) / 10 : 100.0;
    return {
      mode: this.mode,
      finalScore: this.score,
      highScore: this.highScore,
      fruitsSliced: this.totalFruitsSliced,
      fruitsMissed: this.totalFruitsMissed,
      bombHits: this.bombHits,
      highestCombo: this.highestCombo,
      combosAwarded: this.combosAwarded,
      accuracyPct: acc,
      livesLeft: this.lives,
      timeRemaining: Math.round(this.timeRemaining * 10) / 10,
    };
  }
}
