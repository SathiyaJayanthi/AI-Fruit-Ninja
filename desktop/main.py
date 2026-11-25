"""
AI Hand Gesture Controlled Fruit Ninja Game - Entry Point.
Launches the full interactive game with real-time MediaPipe hand tracking.
"""

import argparse
import os
import sys

# Suppress noisy C++ LiteRT / TensorFlow / absl logging
os.environ["GLOG_minloglevel"] = "2"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from config import (
    HAND_LANDMARKER_MODEL_PATH,
    MODE_CLASSIC,
    MODE_TIME_CHALLENGE,
    MODE_PRACTICE,
)
from download_model import download_model
from game.engine import GameEngine


def parse_args():
    parser = argparse.ArgumentParser(
        description="AI Hand Gesture Controlled Fruit Ninja - MediaPipe Index Fingertip Slicing Game"
    )
    parser.add_argument(
        "--mode",
        choices=[MODE_CLASSIC, MODE_TIME_CHALLENGE, MODE_PRACTICE],
        default=MODE_CLASSIC,
        help="Initial game mode (CLASSIC, TIME_CHALLENGE, or PRACTICE)",
    )
    parser.add_argument(
        "--camera-index",
        type=int,
        default=0,
        help="Webcam camera index (default: 0)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run without displaying a graphical window (for automated verification)",
    )
    parser.add_argument(
        "--no-sound",
        action="store_true",
        help="Disable audio output",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    print("=" * 60)
    print("  AI HAND GESTURE CONTROLLED FRUIT NINJA GAME")
    print("  Framework: MediaPipe Tasks + OpenCV + Pygame")
    print("=" * 60)

    # Verify official MediaPipe model asset exists
    if not os.path.exists(HAND_LANDMARKER_MODEL_PATH):
        print(f"\n[Main] Official model asset not found at {HAND_LANDMARKER_MODEL_PATH}.")
        print("[Main] Attempting automatic download from official Google MediaPipe storage...")
        if not download_model():
            print("[Main] Error: Could not download model asset. Falling back to classic solutions if available.")

    print(f"\n[Main] Launching game in {args.mode} mode...")
    print("[Main] Controls:")
    print("  - Index Finger: Move in front of webcam to swing virtual blade!")
    print("  - Fast swipe: Slices fruit and triggers combos.")
    print("  - [SPACE]: Start / Restart game round.")
    print("  - [1, 2, 3]: Select game mode in menu.")
    print("  - [P]: Pause / Resume.")
    print("  - [C]: Toggle Webcam PIP preview.")
    print("  - [R]: Restart current match.")
    print("  - [ESC]: Return to Main Menu or Exit.\n")

    engine = GameEngine(headless=args.headless)
    if args.no_sound:
        engine.sounds.enabled = False

    try:
        engine.run()
    except KeyboardInterrupt:
        print("\n[Main] Gracefully shutting down...")
    finally:
        engine.cleanup()
        print("[Main] Game exited cleanly.")


if __name__ == "__main__":
    main()
