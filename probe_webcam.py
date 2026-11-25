"""
Diagnostic script to test physical webcam access and capture capabilities.
"""

import cv2
import time
import sys

def probe_webcam():
    print("=== PROBING WEBCAM DEVICES ===")
    working_index = None
    
    # Try indices 0, 1, 2 with DirectShow and default
    for idx in range(3):
        print(f"\nTesting camera index {idx} with cv2.CAP_DSHOW...")
        cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"[SUCCESS] Camera index {idx} opened with DirectShow: {w}x{h}, shape={frame.shape}")
                working_index = idx
                cap.release()
                return working_index, cv2.CAP_DSHOW
            cap.release()
        
        print(f"Testing camera index {idx} with default backend...")
        cap = cv2.VideoCapture(idx)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"[SUCCESS] Camera index {idx} opened with default backend: {w}x{h}, shape={frame.shape}")
                working_index = idx
                cap.release()
                return working_index, cv2.CAP_ANY
            cap.release()
            
    print("\n[RESULT] No physical webcam device was successfully opened or webcam is in use by another application.")
    return None, None

if __name__ == "__main__":
    idx, backend = probe_webcam()
    sys.exit(0 if idx is not None else 1)
