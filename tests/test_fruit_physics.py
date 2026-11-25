"""
Unit tests for fruit physics simulation, gravity, and slice bifurcation.
"""

import math
import pytest
from config import GRAVITY
from game.collision import calculate_slice_dynamics
from game.fruit import Fruit, FruitHalf, Bomb


class TestFruitPhysics:

    def test_gravity_acceleration(self):
        """Verifies downward velocity increases according to gravity."""
        fruit = Fruit(fruit_type="apple", start_x=200, start_y=600, vx=50, vy=-500)
        initial_vy = fruit.vy
        dt = 0.1
        fruit.update(dt)

        expected_vy = initial_vy + GRAVITY * dt
        assert math.isclose(fruit.vy, expected_vy, abs_tol=1e-3)
        assert fruit.x > 200

    def test_apex_and_fall_trajectory(self):
        """Verifies fruit reaches top of arc and begins downward descent."""
        fruit = Fruit(fruit_type="watermelon", start_x=300, start_y=500, vx=0, vy=-300)
        assert fruit.vy < 0  # Moving up

        # Simulate until apex is passed (e.g., 0.8 seconds: -300 + 720 * 0.8 = +276)
        for _ in range(8):
            fruit.update(0.1)

        assert fruit.vy > 0
        assert fruit.has_peaked is True

    def test_offscreen_detection(self):
        """Fruit is only offscreen when it has passed screen bottom while falling."""
        fruit = Fruit(fruit_type="orange", start_x=300, start_y=750, vx=0, vy=-600)
        # Even though y=750 > 720, vy is negative (spawning upwards), so NOT offscreen yet
        assert fruit.is_offscreen(max_height=720) is False

        # Move far downwards below screen
        fruit.y = 850
        fruit.vy = 400  # falling
        assert fruit.is_offscreen(max_height=720) is True

    def test_slice_bifurcation(self):
        """Slicing a fruit yields exactly two halves with separate velocities."""
        fruit = Fruit(fruit_type="watermelon", start_x=400, start_y=300, vx=0, vy=-200)
        assert fruit.is_sliced is False

        slice_dyn = calculate_slice_dynamics((300, 300), (500, 300), (400, 300))
        halves = fruit.slice(slice_dyn)

        assert fruit.is_sliced is True
        assert len(halves) == 2
        h1, h2 = halves

        assert isinstance(h1, FruitHalf)
        assert isinstance(h2, FruitHalf)
        assert h1.half_index == 1
        assert h2.half_index == 2

        # Second slice attempt must return empty list to prevent double scoring
        second_attempt = fruit.slice(slice_dyn)
        assert len(second_attempt) == 0

    def test_bomb_physics_and_offscreen(self):
        """Bomb follows ballistic trajectory and handles offscreen."""
        bomb = Bomb(start_x=400, start_y=750, vx=10, vy=-500)
        assert bomb.is_offscreen(max_height=720) is False
        bomb.y = 850
        bomb.vy = 200
        assert bomb.is_offscreen(max_height=720) is True
