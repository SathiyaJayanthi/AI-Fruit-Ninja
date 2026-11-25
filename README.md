# AI Hand Gesture Controlled Fruit Ninja — Monorepo

[![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Android%20%7C%20Web-blue.svg)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.12-brightgreen.svg)](https://www.python.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Tasks%20Vision-orange.svg)](https://ai.google.dev/edge/mediapipe)
[![React](https://img.shields.io/badge/React-18.2%20%2B%20TypeScript-61dafb.svg)](https://react.dev/)
[![PWA](https://img.shields.io/badge/PWA-Installable-purple.svg)](https://web.dev/progressive-web-apps/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An advanced, cross-platform artificial intelligence arcade game powered by **Google MediaPipe**, **OpenCV**, **Pygame**, and **React + HTML5 Canvas**. 

The game transforms the player's physical index fingertip into a virtual samurai sword through real-time camera tracking, letting players slice dynamic fruits, trigger explosive bomb hazards, and chain multipliers with physical hand swipes.

---

## 1. Monorepo Architecture

```
AI_FRUIT_NINJA/
├── desktop/                  # Windows Desktop Engine (Python 3.12 + Pygame + OpenCV)
│   ├── assets/               # Visual sprites & 44.1 kHz WAV sound effects
│   ├── game/                 # Game loop, collision math, entities, particles
│   ├── hand_tracking/        # DirectShow webcam capture & MediaPipe Tasks
│   ├── models/               # Official float16 hand_landmarker.task (7.45 MB)
│   ├── dist/FruitNinja_AI/   # Standalone Windows Executable distribution
│   ├── tests/                # 35 Pytest unit tests (100% passing)
│   ├── FruitNinja.spec       # PyInstaller bundling specification
│   └── main.py               # Desktop entry point
├── mobile/                   # Android Mobile & PWA Engine (React 18 + TypeScript + Vite)
│   ├── public/               # Webmanifest, Service Worker, and game assets
│   ├── src/                  # 60 FPS HTML5 Canvas engine & Web Vision tracker
│   ├── dist/                 # Production-ready static PWA distribution
│   ├── twa-manifest.json     # Android Trusted Web Activity (TWA) configuration
│   └── package.json          # Dependencies & build scripts
├── shared/                   # Cross-Platform Source of Truth
│   ├── config.json           # Canonical game constants, scoring, and fruit configs
│   └── assets/               # Canonical sprites, sliced halves, and audio WAVs
└── documentation/            # Technical & Publishing Documentation
    ├── ARCHITECTURE.md       # Math, computer vision & collision specifications
    ├── DEPLOYMENT_GUIDE.md   # Windows EXE, Vercel PWA, and Bubblewrap Android AAB
    └── TESTING_REPORT.md     # Automated test suite execution & benchmarks
```

---

## 2. Platform Comparison

| Feature | Windows Desktop (`desktop/`) | Android Mobile (`mobile/`) |
| :--- | :--- | :--- |
| **Core Engine** | Pygame 2.6.1 + SDL 2.28 | React 18 + HTML5 Canvas 2D |
| **AI Vision Engine** | MediaPipe Tasks Python (LiteRT XNNPACK) | MediaPipe Tasks Web (WASM / WebGL) |
| **Camera Feed** | Windows DirectShow (`cv2.CAP_DSHOW`) | WebRTC `navigator.mediaDevices.getUserMedia` |
| **Audio System** | `pygame.mixer` (Stereo 44.1 kHz WAV) | Web Audio API (`AudioContext` synthesizer) |
| **Distribution** | Standalone `FruitNinja_AI.exe` | Google Play Store (`.aab`) & Installable PWA |
| **Primary Control** | Webcam index fingertip gesture | Front-camera index finger gesture |
| **Fallback Control** | Mouse drag slicing | High-precision touch swipe |

---

## 3. Quick Start — Windows Desktop

### Option A: Run Standalone Executable (No Python Required)
1. Navigate to `desktop/dist/FruitNinja_AI/`.
2. Double-click `FruitNinja_AI.exe`.
3. Stand 1.5–3 feet from your laptop webcam and raise your index finger to slice!

### Option B: Run from Source
```bash
# 1. Activate Python virtual environment
cd desktop
..\venv\Scripts\activate

# 2. Run the desktop application
python main.py
```

### Controls (Desktop)
- **Index Fingertip (Camera)**: Primary slicing blade.
- **`[SPACE]`**: Pause / Resume gameplay.
- **`[R]`**: Restart / Play Again.
- **`[C]`**: Toggle Picture-in-Picture webcam overlay.
- **`[M]`**: Mute / Unmute sound effects.
- **`[1] / [2] / [3]`**: Select Classic / Time Challenge / Practice mode.
- **`[ESC]`**: Exit to Menu / Quit.

---

## 4. Quick Start — Android Mobile (PWA & Web)

### Option A: Local Development Server
```bash
cd mobile
npm install
npm run dev
```
Open `http://localhost:5173` on your computer or mobile browser.

### Option B: Build Production PWA Bundle
```bash
cd mobile
npm run build
```
Output is compiled to `mobile/dist/`, ready for 1-click deployment to **Vercel**, **Netlify**, or **GitHub Pages**.

### Deploying to Vercel (HTTPS Required for Camera)
```bash
cd mobile
npx vercel --prod
```

### Installing on Android Device
1. Open the deployed HTTPS URL in **Chrome** or **Brave** on your Android phone.
2. Tap **"Install App"** on the menu card or Chrome's install banner.
3. Grant camera permission when prompted.
4. The game will run in true full-screen mode with front-camera gesture tracking!

---

## 5. Publishing to Google Play Store (Android TWA)

The mobile PWA is pre-configured for Google's **Bubblewrap CLI** to produce an official **Android App Bundle (`.aab`)** for the Google Play Store:

```bash
# 1. Install Google Bubblewrap CLI
npm install -g @bubblewrap/cli

# 2. Build signed Android Application Bundle (AAB) & APK
cd mobile
bubblewrap build
```

See [documentation/DEPLOYMENT_GUIDE.md](file:///e:/deeplearning/documentation/DEPLOYMENT_GUIDE.md) for complete step-by-step instructions on keystore generation, Digital Asset Links (`.well-known/assetlinks.json`), and Google Play Console submission.

---

## 6. Testing & Quality Assurance

Run the comprehensive desktop test suite:
```bash
cd desktop
..\venv\Scripts\pytest tests/ -v
```
All **35 automated tests** pass covering continuous collision detection (CCD), segment-circle intersection, impulse bifurcation physics, combo thresholds, and adaptive exponential moving average (EMA) smoothing.

See [documentation/TESTING_REPORT.md](file:///e:/deeplearning/documentation/TESTING_REPORT.md) for full test output and benchmarks.

---

## 7. Documentation Index

- [System Architecture Specification](file:///e:/deeplearning/documentation/ARCHITECTURE.md)
- [Deployment & Publishing Guide](file:///e:/deeplearning/documentation/DEPLOYMENT_GUIDE.md)
- [Automated Testing & Benchmark Report](file:///e:/deeplearning/documentation/TESTING_REPORT.md)
- [Canonical Shared Configuration](file:///e:/deeplearning/shared/config.json)

---

## 8. License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
