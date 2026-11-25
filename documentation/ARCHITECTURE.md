# AI Hand Gesture Controlled Fruit Ninja — Architecture Specification

## 1. Executive Summary

The **AI Hand Gesture Controlled Fruit Ninja** project is a cross-platform, artificial-intelligence-driven gaming system engineered for both **Windows Desktop** (Python, Pygame, OpenCV, MediaPipe Tasks Vision) and **Android Mobile** (React 18, TypeScript, HTML5 Canvas, MediaPipe Tasks Web, Progressive Web App / Trusted Web Activity).

The project achieves 100% gameplay parity across desktop and mobile while utilizing native hardware and rendering engines best suited for each environment. Slicing is controlled via real-time computer vision tracking of the player's index fingertip (MediaPipe Landmark 8), converting hand velocity into a virtual blade accompanied by dynamic particle bursts, fruit halving physics, and procedural audio.

```
AI_FRUIT_NINJA/
├── desktop/           # Native Windows Python 3.12 + Pygame Application
│   ├── assets/        # Visual sprites (fruits, sliced halves, bombs) & WAV audio
│   ├── game/          # Game engine, collision, entities, particles, spawner
│   ├── hand_tracking/ # OpenCV camera capture & MediaPipe Tasks HandLandmarker
│   ├── models/        # Official hand_landmarker.task (7.45 MB float16)
│   ├── tests/         # Pytest verification suite (35 unit tests)
│   ├── config.py      # Desktop configuration bridge
│   ├── FruitNinja.spec# PyInstaller packaging specification
│   └── main.py        # Desktop application entry point
├── mobile/            # React 18 + TypeScript + Vite PWA Application
│   ├── public/        # PWA Webmanifest, Service Worker, and game assets
│   ├── src/           # Canvas 60 FPS engine, vision tracker, audio synthesizer
│   ├── twa-manifest.json # Android Trusted Web Activity (TWA) configuration
│   ├── package.json   # Node dependencies (@mediapipe/tasks-vision, react, vite)
│   └── vite.config.ts # Vite PWA build configuration
├── shared/            # Single Source of Truth
│   ├── config.json    # Canonical cross-platform game rules, scoring, & physics
│   └── assets/        # Master sprite sheets, halves, bomb models, and sound fx
└── documentation/     # Complete Engineering, Deployment & Testing Guides
    ├── ARCHITECTURE.md    # System design & mathematics specification
    ├── DEPLOYMENT_GUIDE.md# Windows EXE, Vercel PWA, Bubblewrap Android AAB
    └── TESTING_REPORT.md  # Comprehensive test results & benchmarks
```

---

## 2. Technology Stack Comparison

| Component | Windows Desktop | Android Mobile (PWA / TWA) |
| :--- | :--- | :--- |
| **Language** | Python 3.12 (64-bit) | TypeScript 5.2 / JavaScript (ES2022) |
| **Framework / UI** | Pygame 2.6.1 (SDL 2.28) | React 18.2 + HTML5 Canvas 2D |
| **CV Pipeline** | MediaPipe Tasks Python (LiteRT XNNPACK) | MediaPipe Tasks Vision Web (WASM / WebGL) |
| **Camera Access** | OpenCV 4.11 (`cv2.CAP_DSHOW` DirectShow) | WebRTC `navigator.mediaDevices.getUserMedia` |
| **Audio Engine** | `pygame.mixer` (44.1 kHz, 16-bit stereo WAV) | Web Audio API (`AudioContext` procedural synthesis) |
| **Packaging** | PyInstaller 6.22 (Standalone Windows EXE) | Vite 6.4 + PWA Service Worker + Bubblewrap TWA |
| **Distribution** | `FruitNinja_AI.exe` installer / zip | Google Play Store (`.aab` / `.apk`) & HTTPS PWA |
| **Input Controls** | Real-time Webcam (Touch/Mouse debug) | Front Camera AI Gestures + Touch Swipe fallback |

---

## 3. Computer Vision & Fingertip Tracking

### 3.1 Hand Landmark Detection Pipeline
Both platforms track 21 3D hand landmarks using Google's **MediaPipe Hand Landmarker**:
- **Target Landmark**: Landmark 8 (`INDEX_FINGER_TIP`).
- **Base Landmark**: Landmark 0 (`WRIST`) for bounding normalization and confidence checking.
- **Mirrored Coordinates**: To create an intuitive "mirror" interaction, horizontal coordinates are inverted:
  $$\text{Screen}_X = (1.0 - X_{\text{normalized}}) \times W_{\text{screen}}$$
  $$\text{Screen}_Y = Y_{\text{normalized}} \times H_{\text{screen}}$$

### 3.2 Adaptive Exponential Moving Average (EMA) Smoothing
To eliminate camera jitter while preserving responsiveness during rapid slashing movements, an adaptive alpha smoothing filter is applied:
$$\alpha = \text{clamp}\left(0.45 + \frac{v_{\text{raw}}}{1.5 \times v_{\text{slice\_threshold}}} \times 0.43,\ 0.45,\ 0.88\right)$$
$$\vec{P}_t = \alpha \vec{P}_{\text{raw}} + (1 - \alpha) \vec{P}_{t-1}$$

- **Slow / Hovering Hand**: $\alpha \approx 0.45 \implies$ Maximum jitter suppression and trail stability.
- **Fast Slash**: $\alpha \approx 0.88 \implies$ Near-instantaneous responsiveness with zero perceptible lag.

---

## 4. Physics, Collision Detection & Anti-Tunneling

### 4.1 Continuous Collision Detection (CCD)
In fast-paced slicing games, a high-velocity swipe can move 150–300 pixels within a single 16.6ms frame. Simple point-in-circle tests cause **tunneling** (passing through fruits without collision).

To solve this, both platforms maintain a sliding history of the last 4 fingertip positions, forming 3 consecutive line segments:
$$S_i = (\vec{P}_{i}, \vec{P}_{i+1})$$

### 4.2 Segment-Circle Intersection
For each active fruit with center $C = (c_x, c_y)$ and collision radius $R$, the closest point $Q$ on segment $AB$ is computed:
$$t = \text{clamp}\left(\frac{(C - A) \cdot (B - A)}{\|B - A\|^2},\ 0,\ 1\right)$$
$$Q = A + t(B - A)$$
$$\text{Collision} \iff \|C - Q\| \le R$$

### 4.3 Slicing Dynamics & Halves Separation
When a valid collision occurs with velocity $v \ge v_{\text{threshold}}$:
1. Slicing angle $\theta = \text{atan2}(\Delta y, \Delta x)$.
2. Unit normal vector perpendicular to slice:
   $$\hat{n} = (-\sin \theta,\ \cos \theta)$$
3. **Instantaneous Separation Offset**: To prevent sliced halves from visually overlapping on frame 0, an initial 8-pixel normal offset is applied:
   $$P_{\text{half1}} = C + \hat{n} \times 8, \quad P_{\text{half2}} = C - \hat{n} \times 8$$
4. **Impulse Velocities**:
   $$\vec{v}_{\text{half1}} = \vec{v}_{\text{parent}} + \hat{n} \times v_{\text{kick}} + \vec{u}_1$$
   $$\vec{v}_{\text{half2}} = \vec{v}_{\text{parent}} - \hat{n} \times v_{\text{kick}} + \vec{u}_2$$
   where $v_{\text{kick}} \in [180, 240] \text{ px/s}$ and angular velocities $\omega_1 \in [-300, -120]^\circ/\text{s}, \omega_2 \in [120, 300]^\circ/\text{s}$.

---

## 5. Game Modes & Rules Specification

The canonical rules in `shared/config.json` govern both desktop and mobile engines identically:

### 5.1 Classic Mode
- **Lives**: 3 lives.
- **Missed Fruits**: Deducts 1 life when a whole fruit falls below the bottom of the screen.
- **Bombs**: Exploding a bomb deducts 1 life and resets active combos. Game ends when lives reach 0.
- **Scoring**: Regular fruits award +10 points each.

### 5.2 Time Challenge Mode
- **Duration**: 60.0-second countdown timer.
- **Missed Fruits**: No life penalty.
- **Bombs**: Slicing a bomb deducts -10 points and subtracts 3 seconds from the clock.
- **Objective**: Maximize score through aggressive combos before the timer expires.

### 5.3 Practice Mode (Zen)
- **Lives / Timer**: Infinite lives, no timer.
- **Bombs**: Bombs do not spawn.
- **Objective**: Pure skill honing, combo practice, and gesture calibration.

### 5.4 Combo Multiplier System
Any multiple fruit slices occurring within a **350 millisecond** time window are grouped into a combo:
- **3 Fruits**: +3 Bonus Points ("3x COMBO!")
- **4 Fruits**: +5 Bonus Points ("4x MEGA COMBO!")
- **5 Fruits**: +8 Bonus Points ("5x ULTRA COMBO!")
- **6+ Fruits**: +12 Bonus Points ("UNSTOPPABLE NINJA!")

---

## 6. Mobile PWA & Android TWA Architecture

The mobile application is packaged as an installable **Progressive Web App (PWA)** and **Trusted Web Activity (TWA)**:
1. **PWA Manifest (`manifest.webmanifest`)**:
   - `display: "standalone"`, `orientation: "any"`.
   - Android adaptive icons (192x192, 512x512 maskable).
2. **Service Worker (`sw.js`)**:
   - Cache-first strategy for local assets (sprites, sounds, WASM binaries).
   - Network-first fallback for updates.
3. **Digital Asset Links (`.well-known/assetlinks.json`)**:
   - Authenticates SHA-256 certificate fingerprints for Google Play Store integration, eliminating the Chrome address bar to provide a native full-screen app experience.
4. **Google Bubblewrap CLI**:
   - Generates production-ready Android App Bundles (`.aab`) and signed APKs ready for Google Play Console submission.
