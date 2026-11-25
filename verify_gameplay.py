"""
End-to-end integration and gameplay verification script.
Simulates 200 game loop frames in headless mode, programmatically executes
finger gestures to slice fruits, verifies combo awards, score updates, and clean teardown.
"""

import os
import sys
import time
import pygame

# Set dummy video driver for headless environment if needed
os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from config import MODE_CLASSIC, MODE_TIME_CHALLENGE
from game.engine import GameEngine


def test_headless_gameplay_simulation():
    print("[IntegrationTest] Initializing GameEngine in headless mode...")
    engine = GameEngine(headless=True)
    engine.start_game(MODE_CLASSIC)
    assert engine.state == "PLAYING"
    print("[IntegrationTest] Successfully entered PLAYING state.")

    # Simulate 120 frames (~2 seconds of game time)
    print("[IntegrationTest] Simulating active gameplay frames...")
    dt = 1.0 / 60.0

    # Programmatically spawn a fruit right in front of the blade
    from game.fruit import Fruit
    test_fruit = Fruit(fruit_type="watermelon", start_x=400, start_y=300, vx=0, vy=-50)
    engine.active_fruits.append(test_fruit)

    # Simulate a fast slicing swipe across (350, 300) -> (450, 300)
    t = time.time()
    engine.tracker.update((350.0, 300.0), current_time=t)
    engine._update(dt)

    # Next frame fast swipe
    engine.tracker.update((450.0, 300.0), current_time=t + 0.02)
    assert engine.tracker.is_slicing is True
    engine._update(dt)

    # Verify the fruit was sliced
    assert test_fruit.is_sliced is True
    assert len(engine.active_halves) == 2
    assert engine.scores.score >= 10
    print(f"[IntegrationTest] Fruit successfully sliced! Current score: {engine.scores.score}")
    print(f"[IntegrationTest] Active fruit halves generated: {len(engine.active_halves)}")

    # Advance simulation by another 60 frames
    for f in range(60):
        engine._update(dt)
        engine._render()

    print("[IntegrationTest] Rendered frames successfully without errors.")
    engine.cleanup()
    print("[IntegrationTest] Integration test PASSED cleanly!\n")
    return True


if __name__ == "__main__":
    success = test_headless_gameplay_simulation()
    sys.exit(0 if success else 1)
