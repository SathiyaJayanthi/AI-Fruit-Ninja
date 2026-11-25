"""
Script to download the official Google MediaPipe Hand Landmarker model.
Model: hand_landmarker.task (Float16)
Source: Google Cloud Storage official MediaPipe repository
URL: https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task
"""

import os
import sys
import urllib.request

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task"
DEST_PATH = os.path.join(os.path.dirname(__file__), "models", "hand_landmarker.task")

def download_model(force: bool = False):
    os.makedirs(os.path.dirname(DEST_PATH), exist_ok=True)
    if os.path.exists(DEST_PATH) and not force:
        size = os.path.getsize(DEST_PATH)
        if size > 1_000_000: # ~8-10MB
            print(f"Model already exists at {DEST_PATH} ({size:,} bytes). Skipping download.")
            return True
        else:
            print(f"Existing model file seems incomplete ({size} bytes). Re-downloading...")

    print(f"Downloading official MediaPipe Hand Landmarker model from:\n  {MODEL_URL}")
    print(f"Saving to:\n  {DEST_PATH}")
    
    def report_hook(block_num, block_size, total_size):
        downloaded = block_num * block_size
        if total_size > 0:
            percent = min(100, downloaded * 100 // total_size)
            if block_num % 50 == 0 or downloaded >= total_size:
                print(f"Progress: {percent}% ({downloaded // 1024} KB / {total_size // 1024} KB)")

    try:
        urllib.request.urlretrieve(MODEL_URL, DEST_PATH, reporthook=report_hook)
        file_size = os.path.getsize(DEST_PATH)
        print(f"\nSuccessfully downloaded model! Size: {file_size:,} bytes.")
        return True
    except Exception as e:
        print(f"\nError downloading model: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = download_model()
    sys.exit(0 if success else 1)
