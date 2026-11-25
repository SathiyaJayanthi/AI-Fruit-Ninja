"""
Captures a rendered screenshot of active gameplay for documentation and verification.
"""

import os
import time
import pygame
import numpy as np
import cv2

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from config import SCREEN_WIDTH, SCREEN_HEIGHT, MODE_CLASSIC
from game.engine import GameEngine
from game.fruit import Fruit, Bomb


def capture_screenshot():
    engine = GameEngine(headless=True)
    engine.start_game(MODE_CLASSIC)

    # Spawn several fruits in attractive positions
    f1 = Fruit("watermelon", start_x=380, start_y=320, vx=20, vy=-120)
    f2 = Fruit("orange", start_x=760, start_y=280, vx=-30, vy=-90)
    f3 = Fruit("banana", start_x=950, start_y=390, vx=-50, vy=-160)
    b1 = Bomb(start_x=540, start_y=420, vx=10, vy=-110)

    engine.active_fruits.extend([f1, f2, f3])
    engine.active_bombs.append(b1)

    # Perform a slice on watermelon
    from game.collision import calculate_slice_dynamics
    dyn = calculate_slice_dynamics((280, 260), (460, 360), (380, 320))
    halves = f1.slice(dyn)
    engine.active_halves.extend(halves)
    engine.active_fruits.remove(f1)

    # Emit juice splatter & text
    engine.particles.emit_juice_splatter(380, 320, f1.juice_color, count=36)
    engine.particles.add_floating_text("+10", 380, 270, (255, 255, 255), engine.ui.font_medium)
    engine.scores.score = 140
    engine.scores.high_score = 320

    # Blade trail
    t = time.time()
    pts = [
        (260.0 + i * 20.0, 250.0 + i * 11.0, t - (10 - i) * 0.015)
        for i in range(11)
    ]
    for pt in pts:
        engine.tracker.trail.append(pt)
    engine.tracker.is_slicing = True
    engine.tracker.is_hand_present = True

    # Dummy PIP frame with hand visual
    dummy_cam = np.zeros((240, 320, 3), dtype=np.uint8)
    dummy_cam[:] = (20, 24, 35)
    cv2.putText(dummy_cam, "WEBCAM PREVIEW", (30, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 230, 255), 2)
    cv2.circle(dummy_cam, (160, 130), 10, (0, 255, 255), -1)
    cv2.circle(dummy_cam, (160, 130), 18, (255, 255, 0), 2)
    engine.ui.update_pip_frame(dummy_cam)

    # Render scene
    engine._render()

    output_path = os.path.join(os.path.dirname(__file__), "screenshot_gameplay.png")
    pygame.image.save(engine.screen, output_path)
    print(f"Gameplay screenshot saved to {output_path}")

    # Also capture menu screenshot
    engine.state = "MENU"
    engine._render()
    menu_path = os.path.join(os.path.dirname(__file__), "screenshot_menu.png")
    pygame.image.save(engine.screen, menu_path)
    print(f"Menu screenshot saved to {menu_path}")

    engine.cleanup()


if __name__ == "__main__":
    capture_screenshot()
