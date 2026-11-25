"""
MediaPipe Hand Landmarker and Hand Tracking Module.
Uses the official Google MediaPipe Hand Landmarker Task (with classic Solutions fallback).
Extracts, verifies, and annotates all 21 landmarks with special focus on Landmark 8 (Index Fingertip).
"""

import os
import sys
import time
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import cv2

try:
    import mediapipe as mp
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False


# Official MediaPipe 21 Hand Landmarks
HAND_LANDMARK_NAMES = [
    "WRIST",              # 0
    "THUMB_CMC",          # 1
    "THUMB_MCP",          # 2
    "THUMB_IP",           # 3
    "THUMB_TIP",          # 4
    "INDEX_FINGER_MCP",   # 5
    "INDEX_FINGER_PIP",   # 6
    "INDEX_FINGER_DIP",   # 7
    "INDEX_FINGER_TIP",   # 8
    "MIDDLE_FINGER_MCP",  # 9
    "MIDDLE_FINGER_PIP",  # 10
    "MIDDLE_FINGER_DIP",  # 11
    "MIDDLE_FINGER_TIP",  # 12
    "RING_FINGER_MCP",    # 13
    "RING_FINGER_PIP",    # 14
    "RING_FINGER_DIP",    # 15
    "RING_FINGER_TIP",    # 16
    "PINKY_MCP",          # 17
    "PINKY_PIP",          # 18
    "PINKY_DIP",          # 19
    "PINKY_TIP"           # 20
]

# Official Hand Skeleton Connections (Bone Pairs)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
    (0, 5), (5, 6), (6, 7), (7, 8),        # Index Finger
    (0, 9), (9, 10), (10, 11), (11, 12),   # Middle Finger
    (0, 13), (13, 14), (14, 15), (15, 16), # Ring Finger
    (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
    (5, 9), (9, 13), (13, 17)              # Palm knuckle bridge
]


class HandDetector:
    """
    Encapsulates MediaPipe Hand Landmarker for real-time video/webcam processing.
    Extracts all 21 hand landmarks, converts normalized coordinates to game coordinates,
    ensures strictly monotonic timestamps for MediaPipe Tasks, and provides rich skeleton visualization.
    """

    INDEX_FINGER_TIP_ID = 8
    INDEX_FINGER_DIP_ID = 7
    INDEX_FINGER_PIP_ID = 6
    INDEX_FINGER_MCP_ID = 5
    WRIST_ID = 0

    def __init__(
        self,
        model_path: str,
        num_hands: int = 1,
        min_detection_confidence: float = 0.55,
        min_tracking_confidence: float = 0.55,
        target_width: int = 1280,
        target_height: int = 720,
    ):
        self.model_path = model_path
        self.num_hands = num_hands
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.target_width = target_width
        self.target_height = target_height

        self.landmarker = None
        self.use_legacy_solution = False
        self.legacy_hands = None
        self._last_timestamp_ms = -1
        self._last_error = None
        self._init_detector()

    def _init_detector(self):
        """Initializes the MediaPipe detector, preferring Tasks API and falling back if needed."""
        if not MEDIAPIPE_AVAILABLE:
            print("[HandDetector] Warning: mediapipe not installed.")
            return

        # Try Tasks API first if model file exists
        if os.path.exists(self.model_path):
            try:
                base_options = mp_python.BaseOptions(model_asset_path=self.model_path)
                options = mp_vision.HandLandmarkerOptions(
                    base_options=base_options,
                    running_mode=mp_vision.RunningMode.VIDEO,
                    num_hands=self.num_hands,
                    min_hand_detection_confidence=self.min_detection_confidence,
                    min_hand_presence_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence,
                )
                self.landmarker = mp_vision.HandLandmarker.create_from_options(options)
                print(f"[HandDetector] Successfully initialized MediaPipe Tasks HandLandmarker with {self.model_path}")
                return
            except Exception as e:
                self._last_error = str(e)
                print(f"[HandDetector] MediaPipe Tasks note: {e}. Trying legacy solutions...")

        # Fallback to mp.solutions.hands if available
        try:
            if hasattr(mp, "solutions") and hasattr(mp.solutions, "hands"):
                self.legacy_hands = mp.solutions.hands.Hands(
                    static_image_mode=False,
                    max_num_hands=self.num_hands,
                    min_detection_confidence=self.min_detection_confidence,
                    min_tracking_confidence=self.min_tracking_confidence,
                )
                self.use_legacy_solution = True
                print("[HandDetector] Initialized MediaPipe Solutions Hands fallback.")
        except Exception as e2:
            self._last_error = str(e2)
            print(f"[HandDetector] Could not initialize fallback: {e2}")

    def process_frame(
        self,
        bgr_frame: np.ndarray,
        timestamp_ms: Optional[int] = None,
        mirror: bool = True
    ) -> Dict[str, Any]:
        """
        Process a BGR webcam frame:
        1. Optionally mirror horizontally (essential for intuitive gesture control).
        2. Convert BGR to RGB.
        3. Enforce strictly monotonic timestamp for MediaPipe Tasks.
        4. Detect hand landmarks and extract all 21 keypoints.
        5. Map index fingertip (landmark 8) to screen pixel coordinates.
        6. Render skeleton overlay on camera preview.
        """
        if bgr_frame is None:
            return {
                "detected": False,
                "index_tip": None,
                "landmarks": [],
                "landmarks_norm": [],
                "all_21_valid": False,
                "annotated_frame": None,
                "raw_frame": None,
            }

        # 1. Horizontal Mirroring (Natural webcam mirror interaction)
        if mirror:
            bgr_frame = cv2.flip(bgr_frame, 1)

        rgb_frame = np.ascontiguousarray(cv2.cvtColor(bgr_frame, cv2.COLOR_BGR2RGB))
        h, w = bgr_frame.shape[:2]

        # 2. Strictly Monotonic Timestamp Enforcement
        if timestamp_ms is None:
            now_ms = int(time.time() * 1000)
            if now_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1
            else:
                timestamp_ms = now_ms
        else:
            if timestamp_ms <= self._last_timestamp_ms:
                timestamp_ms = self._last_timestamp_ms + 1

        self._last_timestamp_ms = timestamp_ms

        landmarks_pixel: List[Tuple[int, int, float]] = []
        landmarks_norm: List[Tuple[float, float, float]] = []
        index_tip_screen: Optional[Tuple[float, float]] = None
        hand_detected = False

        # 3. MediaPipe Tasks Inference
        if self.landmarker and not self.use_legacy_solution:
            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                result = self.landmarker.detect_for_video(mp_image, timestamp_ms)

                if result and result.hand_landmarks and len(result.hand_landmarks) > 0:
                    hand_detected = True
                    first_hand = result.hand_landmarks[0]
                    for lm in first_hand:
                        landmarks_norm.append((float(lm.x), float(lm.y), float(lm.z)))
                        px = int(lm.x * self.target_width)
                        py = int(lm.y * self.target_height)
                        landmarks_pixel.append((px, py, float(lm.z)))

                    if len(first_hand) > self.INDEX_FINGER_TIP_ID:
                        tip_lm = first_hand[self.INDEX_FINGER_TIP_ID]
                        index_tip_screen = (
                            float(tip_lm.x * self.target_width),
                            float(tip_lm.y * self.target_height)
                        )
            except Exception as e:
                self._last_error = str(e)

        elif self.use_legacy_solution and self.legacy_hands:
            try:
                result = self.legacy_hands.process(rgb_frame)
                if result and result.multi_hand_landmarks:
                    hand_detected = True
                    first_hand = result.multi_hand_landmarks[0]
                    for lm in first_hand.landmark:
                        landmarks_norm.append((float(lm.x), float(lm.y), float(lm.z)))
                        px = int(lm.x * self.target_width)
                        py = int(lm.y * self.target_height)
                        landmarks_pixel.append((px, py, float(lm.z)))

                    if len(first_hand.landmark) > self.INDEX_FINGER_TIP_ID:
                        tip_lm = first_hand.landmark[self.INDEX_FINGER_TIP_ID]
                        index_tip_screen = (
                            float(tip_lm.x * self.target_width),
                            float(tip_lm.y * self.target_height)
                        )
            except Exception as e:
                self._last_error = str(e)

        all_21_valid = hand_detected and (len(landmarks_pixel) == 21)

        # 4. Generate Comprehensive Skeleton Visualization for PIP Preview
        annotated_bgr = bgr_frame.copy()
        if hand_detected and len(landmarks_pixel) == 21:
            cam_points = []
            for px, py, _ in landmarks_pixel:
                cx = int(px * (w / self.target_width))
                cy = int(py * (h / self.target_height))
                cam_points.append((cx, cy))

            # Draw bone connections
            for p1_idx, p2_idx in HAND_CONNECTIONS:
                pt1 = cam_points[p1_idx]
                pt2 = cam_points[p2_idx]
                cv2.line(annotated_bgr, pt1, pt2, (0, 200, 255), 2)

            # Draw joints (0-20)
            for idx, pt in enumerate(cam_points):
                if idx == self.INDEX_FINGER_TIP_ID:
                    # Highlight Index Fingertip (Landmark 8) with prominent cyan/white marker
                    cv2.circle(annotated_bgr, pt, 8, (0, 255, 255), -1)
                    cv2.circle(annotated_bgr, pt, 12, (255, 255, 255), 2)
                    cv2.putText(
                        annotated_bgr, "8 (BLADE)", (pt[0] + 10, pt[1] - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1, cv2.LINE_AA
                    )
                else:
                    cv2.circle(annotated_bgr, pt, 4, (0, 165, 255), -1)

            # Draw HUD status text on camera frame
            tip_pos_text = f"Tip (8): ({int(index_tip_screen[0])}, {int(index_tip_screen[1])})"
            cv2.putText(
                annotated_bgr, tip_pos_text, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 120), 2, cv2.LINE_AA
            )
            cv2.putText(
                annotated_bgr, "21 Landmarks: OK", (10, 50),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1, cv2.LINE_AA
            )

        return {
            "detected": hand_detected,
            "index_tip": index_tip_screen,
            "landmarks": landmarks_pixel,
            "landmarks_norm": landmarks_norm,
            "all_21_valid": all_21_valid,
            "annotated_frame": annotated_bgr,
            "raw_frame": bgr_frame,
            "error": self._last_error,
        }

    def close(self):
        """Release detector resources."""
        if self.landmarker:
            try:
                self.landmarker.close()
            except Exception:
                pass
            self.landmarker = None
        if self.legacy_hands:
            try:
                self.legacy_hands.close()
            except Exception:
                pass
            self.legacy_hands = None
