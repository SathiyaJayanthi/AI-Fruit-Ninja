import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';
import { HandTrackingResult } from './types';
import { GAME_CONSTANTS } from './config';

export class MobileHandTracker {
  private landmarker: HandLandmarker | null = null;
  private video: HTMLVideoElement | null = null;
  private isReady: boolean = false;
  private lastTime: number = 0;
  private smoothedPos: { x: number; y: number } | null = null;
  private trail: { x: number; y: number; time: number }[] = [];
  public landmarks: { x: number; y: number; z: number }[] = [];
  public currentSpeed: number = 0;
  public isSlicing: boolean = false;
  private minSliceSpeed: number = GAME_CONSTANTS.BLADE_MIN_SLICE_SPEED;
  private minSliceDistance: number = GAME_CONSTANTS.BLADE_MIN_SLICE_DISTANCE;

  public async initialize(videoElement: HTMLVideoElement): Promise<boolean> {
    this.video = videoElement;
    try {
      console.log('[MobileVision] Initializing MediaPipe Tasks FilesetResolver...');
      const vision = await FilesetResolver.forVisionTasks(
        'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
      );

      console.log('[MobileVision] Creating HandLandmarker with GPU delegate...');
      this.landmarker = await HandLandmarker.createFromOptions(vision, {
        baseOptions: {
          modelAssetPath:
            'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
          delegate: 'GPU',
        },
        runningMode: 'VIDEO',
        numHands: 1,
        minHandDetectionConfidence: 0.55,
        minHandPresenceConfidence: 0.55,
        minTrackingConfidence: 0.55,
      });

      this.isReady = true;
      console.log('[MobileVision] HandLandmarker ready.');
      return true;
    } catch (err) {
      console.warn('[MobileVision] GPU initialization failed, falling back to CPU:', err);
      try {
        const vision = await FilesetResolver.forVisionTasks(
          'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@latest/wasm'
        );
        this.landmarker = await HandLandmarker.createFromOptions(vision, {
          baseOptions: {
            modelAssetPath:
              'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task',
            delegate: 'CPU',
          },
          runningMode: 'VIDEO',
          numHands: 1,
          minHandDetectionConfidence: 0.5,
          minHandPresenceConfidence: 0.5,
          minTrackingConfidence: 0.5,
        });
        this.isReady = true;
        return true;
      } catch (err2) {
        console.error('[MobileVision] Could not initialize HandLandmarker:', err2);
        this.isReady = false;
        return false;
      }
    }
  }

  public processFrame(
    canvasWidth: number,
    canvasHeight: number
  ): HandTrackingResult {
    const emptyResult: HandTrackingResult = {
      detected: false,
      tip: null,
      landmarks: [],
      currentSpeed: 0,
      isSlicing: false,
    };

    if (!this.isReady || !this.landmarker || !this.video || this.video.readyState < 2) {
      this.isSlicing = false;
      this.currentSpeed = 0;
      return emptyResult;
    }

    const now = performance.now();
    let results: ReturnType<HandLandmarker['detectForVideo']> | null = null;

    try {
      results = this.landmarker.detectForVideo(this.video, now);
    } catch (e) {
      return emptyResult;
    }

    if (!results || !results.landmarks || results.landmarks.length === 0) {
      this.isSlicing = false;
      this.currentSpeed = 0;
      this.smoothedPos = null;
      this.landmarks = [];
      return emptyResult;
    }

    const firstHand = results.landmarks[0];
    const rawTip = firstHand[8]; // Landmark 8: Index Fingertip
    if (!rawTip) {
      this.landmarks = [];
      return emptyResult;
    }

    // Map all 21 landmarks to mirrored screen coordinates
    this.landmarks = firstHand.map((lm) => ({
      x: (1.0 - lm.x) * canvasWidth,
      y: lm.y * canvasHeight,
      z: lm.z ?? 0,
    }));

    // Horizontal mirror for natural front-camera interaction
    const screenX = (1.0 - rawTip.x) * canvasWidth;
    const screenY = rawTip.y * canvasHeight;

    const dt = Math.max(0.001, (now - this.lastTime) / 1000.0);
    this.lastTime = now;

    if (!this.smoothedPos) {
      this.smoothedPos = { x: screenX, y: screenY };
      this.trail = [{ x: screenX, y: screenY, time: now }];
      this.currentSpeed = 0;
      this.isSlicing = false;
      return {
        detected: true,
        tip: this.smoothedPos,
        landmarks: this.landmarks,
        currentSpeed: 0,
        isSlicing: false,
      };
    }

    // Adaptive smoothing: higher responsiveness during high-velocity swipes
    const rawDist = Math.hypot(screenX - this.smoothedPos.x, screenY - this.smoothedPos.y);
    const rawSpeed = rawDist / dt;
    const alpha = Math.min(0.88, Math.max(0.45, 0.45 + (rawSpeed / (this.minSliceSpeed * 1.5)) * 0.43));

    const smoothX = alpha * screenX + (1.0 - alpha) * this.smoothedPos.x;
    const smoothY = alpha * screenY + (1.0 - alpha) * this.smoothedPos.y;

    const dist = Math.hypot(smoothX - this.smoothedPos.x, smoothY - this.smoothedPos.y);
    const speed = dist / dt;

    this.smoothedPos = { x: smoothX, y: smoothY };
    this.currentSpeed = speed;
    this.isSlicing = speed >= this.minSliceSpeed && dist >= this.minSliceDistance;

    this.trail.push({ x: smoothX, y: smoothY, time: now });
    if (this.trail.length > GAME_CONSTANTS.BLADE_TRAIL_LENGTH) {
      this.trail.shift();
    }

    return {
      detected: true,
      tip: this.smoothedPos,
      landmarks: this.landmarks,
      currentSpeed: speed,
      isSlicing: this.isSlicing,
    };
  }

  public getTrail() {
    return this.trail;
  }

  public getLandmarks() {
    return this.landmarks;
  }

  public clear() {
    this.smoothedPos = null;
    this.trail = [];
    this.landmarks = [];
    this.currentSpeed = 0;
    this.isSlicing = false;
  }

  public close() {
    if (this.landmarker) {
      try {
        this.landmarker.close();
      } catch (_) {}
      this.landmarker = null;
    }
    this.isReady = false;
  }
}
