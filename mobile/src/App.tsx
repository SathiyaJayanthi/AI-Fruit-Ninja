import React, { useEffect, useRef, useState, useCallback } from 'react';
import { GameMode, GameState, GameSummary } from './types';
import { MobileGameEngine } from './engine';
import { MobileHandTracker } from './vision';
import { soundManager } from './audio';

const HAND_CONNECTIONS = [
  // Thumb
  [0, 1], [1, 2], [2, 3], [3, 4],
  // Index
  [0, 5], [5, 6], [6, 7], [7, 8],
  // Middle
  [0, 9], [9, 10], [10, 11], [11, 12],
  // Ring
  [0, 13], [13, 14], [14, 15], [15, 16],
  // Pinky
  [0, 17], [17, 18], [18, 19], [19, 20],
  // Palm bridges
  [5, 9], [9, 13], [13, 17],
];

function renderPipYellowNerves(
  pctx: CanvasRenderingContext2D,
  normLm: { x: number; y: number; z: number }[],
  width: number,
  height: number,
  isSlicing: boolean
) {
  // Map normalized coordinates (mirrored horizontally)
  const pts = normLm.map((lm) => ({
    x: (1.0 - lm.x) * width,
    y: lm.y * height,
  }));

  // 1. Draw bright glowing yellow nerve connections
  HAND_CONNECTIONS.forEach(([i, j]) => {
    const p1 = pts[i];
    const p2 = pts[j];
    if (!p1 || !p2) return;

    // Pass 1: Outer glowing golden aura
    pctx.strokeStyle = 'rgba(255, 190, 0, 0.45)';
    pctx.lineWidth = 5;
    pctx.lineCap = 'round';
    pctx.beginPath();
    pctx.moveTo(p1.x, p1.y);
    pctx.lineTo(p2.x, p2.y);
    pctx.stroke();

    // Pass 2: Bright neon yellow nerve fiber
    pctx.strokeStyle = '#ffee00';
    pctx.lineWidth = 2.2;
    pctx.beginPath();
    pctx.moveTo(p1.x, p1.y);
    pctx.lineTo(p2.x, p2.y);
    pctx.stroke();

    // Pass 3: White hot inner core
    pctx.strokeStyle = '#ffffff';
    pctx.lineWidth = 0.8;
    pctx.beginPath();
    pctx.moveTo(p1.x, p1.y);
    pctx.lineTo(p2.x, p2.y);
    pctx.stroke();
  });

  // 2. Draw glowing yellow nerve nodes on all 21 joints
  pts.forEach((pt, idx) => {
    const isTip = [4, 8, 12, 16, 20].includes(idx);
    const isIndexTip = idx === 8;
    const r = isIndexTip ? (isSlicing ? 7 : 5.5) : (isTip ? 3.5 : 2.5);

    // Outer golden glow
    pctx.fillStyle = isIndexTip ? 'rgba(255, 230, 0, 0.7)' : 'rgba(255, 200, 0, 0.45)';
    pctx.beginPath();
    pctx.arc(pt.x, pt.y, r + 3, 0, Math.PI * 2);
    pctx.fill();

    // Bright yellow node
    pctx.fillStyle = isIndexTip ? '#ffee00' : '#ffd000';
    pctx.beginPath();
    pctx.arc(pt.x, pt.y, r, 0, Math.PI * 2);
    pctx.fill();

    // Pure white center spark
    pctx.fillStyle = '#ffffff';
    pctx.beginPath();
    pctx.arc(pt.x, pt.y, Math.max(1, r * 0.45), 0, Math.PI * 2);
    pctx.fill();

    if (isIndexTip) {
      pctx.strokeStyle = '#ffffff';
      pctx.lineWidth = 1.2;
      pctx.beginPath();
      pctx.arc(pt.x, pt.y, r + 4, 0, Math.PI * 2);
      pctx.stroke();
    }
  });

  // Mini HUD badge
  pctx.fillStyle = 'rgba(0, 0, 0, 0.65)';
  pctx.fillRect(4, 4, 82, 16);
  pctx.fillStyle = '#ffee00';
  pctx.font = 'bold 9px sans-serif';
  pctx.fillText('● NERVES ACTIVE', 7, 15);
}

export const App: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const pipCanvasRef = useRef<HTMLCanvasElement | null>(null);

  const engineRef = useRef<MobileGameEngine | null>(null);
  const trackerRef = useRef<MobileHandTracker | null>(null);

  const [gameState, setGameState] = useState<GameState>('MENU');
  const [selectedMode, setSelectedMode] = useState<GameMode>('CLASSIC');
  const [score, setScore] = useState<number>(0);
  const [highScore, setHighScore] = useState<number>(0);
  const [lives, setLives] = useState<number>(3);
  const [timeRemaining, setTimeRemaining] = useState<number>(60);
  const [summary, setSummary] = useState<GameSummary | null>(null);

  // Vision & Camera state
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [isModelLoaded, setIsModelLoaded] = useState<boolean>(false);
  const [handDetected, setHandDetected] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [showPip, setShowPip] = useState<boolean>(true);

  // Audio & PWA Install
  const [isMuted, setIsMuted] = useState<boolean>(false);
  const [deferredPrompt, setDeferredPrompt] = useState<any>(null);

  // PWA Install prompt listener
  useEffect(() => {
    const handleBeforeInstall = (e: Event) => {
      e.preventDefault();
      setDeferredPrompt(e);
    };
    window.addEventListener('beforeinstallprompt', handleBeforeInstall);
    return () => window.removeEventListener('beforeinstallprompt', handleBeforeInstall);
  }, []);

  const handleInstallClick = async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
      setDeferredPrompt(null);
    }
  };

  // Initialize Game Engine & Hand Tracker
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set canvas dimensions
    const resizeCanvas = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    const engine = new MobileGameEngine(canvas);
    engineRef.current = engine;
    setHighScore(engine.highScore);

    const tracker = new MobileHandTracker();
    trackerRef.current = tracker;

    // Start Camera & MediaPipe
    const initCamera = async () => {
      try {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
          throw new Error('Camera API is not supported in this browser.');
        }

        const stream = await navigator.mediaDevices.getUserMedia({
          video: {
            facingMode: 'user',
            width: { ideal: 640 },
            height: { ideal: 480 },
          },
          audio: false,
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          await videoRef.current.play();
          setIsCameraActive(true);

          // Initialize Vision Tracker
          const ready = await tracker.initialize(videoRef.current);
          setIsModelLoaded(ready);
        }
      } catch (err: any) {
        console.warn('[Camera] Failed to initialize camera:', err.message);
        setCameraError(
          'Camera access not granted or unavailable. Touch / swipe mode is active!'
        );
      }
    };

    initCamera();

    // Main 60 FPS Game Loop
    let animId: number;
    let lastTime = performance.now();

    const loop = (time: number) => {
      const dt = Math.min((time - lastTime) / 1000.0, 0.1);
      lastTime = time;

      if (engine && tracker) {
        // Hand tracking inference
        const result = tracker.processFrame(canvas.width, canvas.height);
        setHandDetected(result.detected);

        // Update physics, slicing, collisions
        const trail = tracker.getTrail();
        engine.update(dt, trail, tracker.isSlicing);

        // Render main game screen: ONLY fruit slicing blade trail & entities
        engine.render(trail, tracker.isSlicing);

        // Render front camera PIP feed with bright glowing yellow nerves
        const pipCanvas = pipCanvasRef.current;
        const video = videoRef.current;
        if (pipCanvas && video && video.readyState >= 2 && showPip) {
          const pctx = pipCanvas.getContext('2d');
          if (pctx) {
            pctx.save();
            pctx.translate(pipCanvas.width, 0);
            pctx.scale(-1, 1);
            pctx.drawImage(video, 0, 0, pipCanvas.width, pipCanvas.height);
            pctx.restore();

            const normLm = tracker.getNormalizedLandmarks();
            if (normLm && normLm.length >= 21) {
              renderPipYellowNerves(pctx, normLm, pipCanvas.width, pipCanvas.height, tracker.isSlicing);
            }
          }
        }

        // Sync local React state
        setScore(engine.score);
        setHighScore(engine.highScore);
        setLives(engine.lives);
        setTimeRemaining(Math.ceil(engine.timeRemaining));

        if (engine.state !== gameState) {
          setGameState(engine.state);
          if (engine.state === 'GAME_OVER') {
            setSummary(engine.getSummary());
          }
        }
      }

      animId = requestAnimationFrame(loop);
    };

    animId = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resizeCanvas);
      if (videoRef.current && videoRef.current.srcObject) {
        const stream = videoRef.current.srcObject as MediaStream;
        stream.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  const handleStartGame = (mode: GameMode) => {
    soundManager.resumeAudioContext();
    if (engineRef.current) {
      engineRef.current.startGame(mode);
      setGameState('PLAYING');
      setSummary(null);
    }
  };

  const handlePauseToggle = () => {
    if (!engineRef.current) return;
    if (gameState === 'PLAYING') {
      engineRef.current.state = 'PAUSED';
      setGameState('PAUSED');
    } else if (gameState === 'PAUSED') {
      engineRef.current.state = 'PLAYING';
      setGameState('PLAYING');
    }
  };

  const handleToggleMute = () => {
    const next = !isMuted;
    setIsMuted(next);
    soundManager.setMuted(next);
  };

  const handleReturnToMenu = () => {
    if (engineRef.current) {
      engineRef.current.resetToMenu();
    }
    setGameState('MENU');
    setSummary(null);
  };

  return (
    <div className="game-container">
      {/* Background Interactive Game Canvas */}
      <canvas ref={canvasRef} className="game-canvas" />

      {/* Front Camera Video Source (Hidden, feeds MediaPipe model) */}
      <video
        ref={videoRef}
        style={{ display: 'none' }}
        playsInline
        muted
      />

      {/* Front Camera PIP Window with Bright Glowing Yellow Nerves */}
      <canvas
        ref={pipCanvasRef}
        className="camera-pip"
        width={160}
        height={120}
        style={{ display: isCameraActive && showPip ? 'block' : 'none' }}
      />

      {/* In-Game HUD Overlay */}
      {gameState === 'PLAYING' && (
        <div className="hud-overlay">
          {/* Top Left: Score & High Score */}
          <div className="hud-left">
            <div className="hud-score-card">
              <div className="score-label">Score</div>
              <div className="score-value">{score}</div>
              <div className="high-score-small">BEST: {highScore}</div>
            </div>
            <div className="hud-status-badge">
              <div
                className="status-dot"
                style={{
                  background: handDetected ? '#00e5ff' : '#ffb703',
                  boxShadow: handDetected
                    ? '0 0 8px #00e5ff'
                    : '0 0 8px #ffb703',
                }}
              />
              <span>
                {handDetected
                  ? 'Hand Tracked'
                  : isCameraActive
                  ? 'Looking for Hand...'
                  : 'Touch Mode'}
              </span>
            </div>
          </div>

          {/* Top Center: Mode-specific info */}
          <div className="hud-center">
            {selectedMode === 'CLASSIC' && (
              <div className="hud-lives">
                {[0, 1, 2].map((idx) => (
                  <span
                    key={idx}
                    className={`heart-icon ${idx >= lives ? 'lost' : ''}`}
                  >
                    ❤️
                  </span>
                ))}
              </div>
            )}
            {selectedMode === 'TIME_CHALLENGE' && (
              <div className="hud-timer">⏱️ {timeRemaining}s</div>
            )}
            {selectedMode === 'PRACTICE' && (
              <div className="hud-status-badge" style={{ color: '#a78bfa' }}>
                🧘 ZEN PRACTICE
              </div>
            )}
          </div>

          {/* Top Right: Action Controls */}
          <div className="hud-right" style={{ flexDirection: 'row' }}>
            <button className="hud-btn" onClick={() => setShowPip(!showPip)}>
              📷 {showPip ? 'Hide PIP' : 'Show PIP'}
            </button>
            <button className="hud-btn" onClick={handleToggleMute}>
              {isMuted ? '🔇' : '🔊'}
            </button>
            <button className="hud-btn" onClick={handlePauseToggle}>
              ⏸️
            </button>
          </div>
        </div>
      )}

      {/* Main Menu Modal */}
      {gameState === 'MENU' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h1 className="game-title">FRUIT NINJA AI</h1>
            <p className="game-subtitle">
              Wave your index finger at the camera or swipe to slice!
            </p>

            <div className="mode-selector">
              <button
                className={`mode-card-btn ${
                  selectedMode === 'CLASSIC' ? 'selected' : ''
                }`}
                onClick={() => setSelectedMode('CLASSIC')}
              >
                <div>
                  <div className="mode-card-title">🍉 Classic Mode</div>
                  <div className="mode-card-desc">
                    3 Lives • Bombs deduct lives • Infinite high-score run
                  </div>
                </div>
                <span>➔</span>
              </button>

              <button
                className={`mode-card-btn ${
                  selectedMode === 'TIME_CHALLENGE' ? 'selected' : ''
                }`}
                onClick={() => setSelectedMode('TIME_CHALLENGE')}
              >
                <div>
                  <div className="mode-card-title">⏱️ Time Challenge</div>
                  <div className="mode-card-desc">
                    60 Seconds • Bombs deduct -10 pts • Slice furiously!
                  </div>
                </div>
                <span>➔</span>
              </button>

              <button
                className={`mode-card-btn ${
                  selectedMode === 'PRACTICE' ? 'selected' : ''
                }`}
                onClick={() => setSelectedMode('PRACTICE')}
              >
                <div>
                  <div className="mode-card-title">🧘 Practice Mode</div>
                  <div className="mode-card-desc">
                    Zero bombs • Infinite lives • Relaxed slicing flow
                  </div>
                </div>
                <span>➔</span>
              </button>
            </div>

            <button
              className="btn-primary"
              onClick={() => handleStartGame(selectedMode)}
            >
              START GAME
            </button>

            {deferredPrompt && (
              <div className="install-pwa-banner">
                <span>📱 Install app on your phone</span>
                <button className="install-btn" onClick={handleInstallClick}>
                  INSTALL
                </button>
              </div>
            )}

            {cameraError && (
              <p
                style={{
                  fontSize: '11px',
                  color: '#fbbf24',
                  marginTop: '12px',
                }}
              >
                ℹ️ {cameraError}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Paused Modal */}
      {gameState === 'PAUSED' && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2 className="game-title">GAME PAUSED</h2>
            <p className="game-subtitle">Take a breather, Ninja!</p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button className="btn-primary" onClick={handlePauseToggle}>
                RESUME
              </button>
              <button
                className="hud-btn"
                style={{ padding: '12px' }}
                onClick={handleReturnToMenu}
              >
                QUIT TO MENU
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Game Over Modal */}
      {gameState === 'GAME_OVER' && summary && (
        <div className="modal-overlay">
          <div className="modal-card">
            <h2
              className="game-title"
              style={{
                background: 'linear-gradient(135deg, #ef476f 0%, #ff5c8a 100%)',
                WebkitBackgroundClip: 'text',
              }}
            >
              GAME OVER
            </h2>
            <div style={{ margin: '10px 0' }}>
              <span className="score-label">FINAL SCORE</span>
              <div className="score-value" style={{ fontSize: '42px' }}>
                {summary.finalScore}
              </div>
              {summary.finalScore >= summary.highScore && summary.finalScore > 0 && (
                <div style={{ color: '#ffd166', fontWeight: 800, fontSize: '13px' }}>
                  🏆 NEW HIGH SCORE!
                </div>
              )}
            </div>

            <div className="stats-grid">
              <div className="stat-item">
                <div className="stat-val">{summary.fruitsSliced}</div>
                <div className="stat-key">Sliced</div>
              </div>
              <div className="stat-item">
                <div className="stat-val">{summary.fruitsMissed}</div>
                <div className="stat-key">Missed</div>
              </div>
              <div className="stat-item">
                <div className="stat-val">{summary.highestCombo}x</div>
                <div className="stat-key">Max Combo</div>
              </div>
              <div className="stat-item">
                <div className="stat-val">{summary.accuracyPct}%</div>
                <div className="stat-key">Accuracy</div>
              </div>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
              <button
                className="btn-primary"
                onClick={() => handleStartGame(selectedMode)}
              >
                PLAY AGAIN
              </button>
              <button
                className="hud-btn"
                style={{ padding: '12px' }}
                onClick={handleReturnToMenu}
              >
                MAIN MENU
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default App;
