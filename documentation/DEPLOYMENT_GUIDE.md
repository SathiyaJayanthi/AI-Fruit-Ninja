# AI Fruit Ninja — Cross-Platform Deployment & Publishing Guide

This guide details the complete publishing lifecycle for both the **Windows Desktop** application and the **Android Mobile** application (Progressive Web App + Google Play Store Trusted Web Activity).

---

## 1. Windows Desktop Deployment

The desktop version is compiled into a standalone Windows 64-bit distribution that runs on any modern Windows 10/11 machine without requiring Python or external dependencies.

### 1.1 Distribution Structure
After building with PyInstaller:
```
desktop/dist/FruitNinja_AI/
├── FruitNinja_AI.exe       # Main Executable launcher
├── models/
│   └── hand_landmarker.task # 7.45 MB MediaPipe float16 model
├── assets/                 # Fruit sprites, sliced halves, bomb sprites, audio WAVs
├── shared/
│   └── config.json         # Canonical game configuration
└── _internal/              # Pygame, OpenCV, LiteRT, NumPy dynamic libraries & Python DLL
```

### 1.2 Running on a Clean Windows PC
1. Copy or extract the entire `FruitNinja_AI` folder to the target machine.
2. Double-click `FruitNinja_AI.exe`.
3. **Camera Requirements**:
   - Integrated laptop webcam or USB webcam.
   - The game utilizes Windows DirectShow (`cv2.CAP_DSHOW`) for zero-latency camera initialization.
   - Ensure camera permissions are enabled in Windows Settings: *Settings > Privacy & Security > Camera > Let desktop apps access your camera*.

### 1.3 Creating an Installer or Single Zip
To distribute to players:
```powershell
Compress-Archive -Path "desktop\dist\FruitNinja_AI\*" -DestinationPath "AI_Fruit_Ninja_Windows.zip"
```
Or package using [Inno Setup](https://jrsoftware.org/isinfo.php) to create an installer with desktop shortcuts and uninstaller.

---

## 2. Mobile PWA Deployment (HTTPS Web)

Mobile browsers require a secure **HTTPS** origin to permit webcam and front-camera hardware access via `navigator.mediaDevices.getUserMedia`.

### 2.1 Deploying to Vercel (Recommended)
1. Install the Vercel CLI or link via GitHub:
   ```bash
   npm install -g vercel
   ```
2. In the `mobile/` directory:
   ```bash
   cd mobile
   npm run build
   vercel deploy --prod
   ```
3. Set the Root Directory to `mobile` and Output Directory to `dist`.

### 2.2 Deploying to Netlify
1. Drag and drop the `mobile/dist/` folder directly into [Netlify Drop](https://app.netlify.com/drop).
2. Or use Netlify CLI:
   ```bash
   npx netlify deploy --dir=mobile/dist --prod
   ```

### 2.3 Testing PWA on an Android Phone
1. Open Chrome on your Android phone and navigate to your deployed HTTPS URL (e.g. `https://ai-fruit-ninja.vercel.app`).
2. Chrome will display the **"Add AI Fruit Ninja to Home screen"** prompt banner.
3. Tap **Install** or tap the 3 dots menu > **Install app**.
4. The game will now launch from your Android home screen as a standalone full-screen application.
5. **Camera Verification**:
   - When prompted, tap **"Allow"** for camera access.
   - The PIP preview badge in the bottom-right corner will show the live front-camera feed.
   - The AI tracking pill will switch to **"Hand Tracked (60 FPS)"** when your hand is detected.

---

## 3. Packaging for Google Play Store (Android TWA / Bubblewrap)

To distribute the app as a native Android app on the **Google Play Store**, use Google's official **Bubblewrap** CLI, which wraps the Progressive Web App in a high-performance **Trusted Web Activity (TWA)** with zero browser address bar.

### 3.1 Prerequisites
- **Node.js**: 18.x or later
- **Java Development Kit (JDK)**: JDK 17 or later
- **Android SDK Platform-Tools**: API level 34+

### 3.2 Step 1: Install Bubblewrap
```bash
npm install -g @bubblewrap/cli
```

### 3.3 Step 2: Initialize Bubblewrap Project
Run Bubblewrap pointing to your live production Web Manifest:
```bash
bubblewrap init --manifest=https://ai-fruit-ninja.vercel.app/manifest.webmanifest
```
Bubblewrap will generate an Android project configured with:
- `packageId`: `com.fruitninja.ai.twa`
- `host`: `ai-fruit-ninja.vercel.app`
- `features`: Fullscreen, orientation lock, splash screen.

### 3.4 Step 3: Generate Android Signing Keystore
If you don't already have an upload keystore:
```bash
keytool -genkey -v -keystore android-keystore.jks -alias fruitninja -keyalg RSA -keysize 2048 -validity 10000
```
Remember your keystore password and alias name.

### 3.5 Step 4: Digital Asset Links Verification
To verify ownership of the domain and remove the Chrome browser URL bar inside the Android app:
1. Extract your keystore's SHA-256 fingerprint:
   ```bash
   keytool -list -v -keystore android-keystore.jks -alias fruitninja
   ```
2. Copy the `SHA256: 14:6D:E9:...` fingerprint.
3. Edit `mobile/public/.well-known/assetlinks.json`:
   ```json
   [
     {
       "relation": ["delegate_permission/common.handle_all_urls"],
       "target": {
         "namespace": "android_app",
         "package_name": "com.fruitninja.ai.twa",
         "sha256_cert_fingerprints": [
           "YOUR_SHA256_FINGERPRINT_HERE"
         ]
       }
     }
   ]
   ```
4. Re-deploy your website so that `https://your-domain.com/.well-known/assetlinks.json` returns HTTP 200 with `Content-Type: application/json`.

### 3.6 Step 5: Build Release AAB & APK
```bash
bubblewrap build
```
This generates:
- `app-release-bundle.aab`: Android App Bundle for Google Play Store upload.
- `app-release-signed.apk`: Standalone testable APK for sideloading on test devices.

---

## 4. Google Play Console Submission Checklist

1. **Create App**:
   - Go to [Google Play Console](https://play.google.com/console).
   - Click **Create app** > Name: *AI Fruit Ninja - Hand Gesture Blade*.
   - Category: *Games / Arcade*.
2. **Privacy Policy**:
   - Provide a public Privacy Policy URL stating:
     > *"AI Fruit Ninja uses device camera feeds strictly for real-time local on-device hand gesture tracking using Google MediaPipe. No video, image, or biometric data is ever recorded, transmitted over the internet, or stored on servers."*
3. **App Content Declarations**:
   - Target Audience: 13+ or All Ages.
   - Ads: No ads.
   - App Access: All features available without credentials.
4. **App Permissions**:
   - `android.permission.CAMERA` (Declared with standard description for gesture input).
5. **Internal Testing Track**:
   - Upload `app-release-bundle.aab`.
   - Add testers' email addresses.
   - Release to testers for immediate download and verification.
