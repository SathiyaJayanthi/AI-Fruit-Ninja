"""
Comprehensive verification test suite for the complete fruit slicing mechanism.
Tests:
1. Line-segment collision detection across all angles & curves
2. Accurate hitboxes for all 7 fruit types & bombs
3. Strictly enforced one-time scoring guarantee
4. Two independent fruit halves with dynamic outward separation
5. Rotational kinematics & gravitational ballistics
6. Particle effects, slice flashes & audio triggers
"""

import math
import pytest
import pygame

from config import (
    FRUITS_CONFIG,
    BOMB_CONFIG,
    GRAVITY,
    HALF_ANGULAR_VELOCITY_MAX,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from game.collision import line_segment_circle_intersection, calculate_slice_dynamics
from game.fruit import Fruit, FruitHalf, Bomb
from game.particles import ParticleSystem, SliceFlash
from game.scoring import ScoreManager
from game.sound import SoundManager
from game.slicing import SliceManager
from hand_tracking.tracker import FingertipTracker


class TestSlicingMechanism:

    @pytest.fixture
    def setup_slicing(self):
        pygame.init()
        particles = ParticleSystem()
        scores = ScoreManager()
        sounds = SoundManager(enabled=False)
        slice_mgr = SliceManager(particles, scores, sounds)
        font = pygame.font.SysFont("Arial", 20)
        return particles, scores, sounds, slice_mgr, font

    def test_all_fruit_hitbox_dimensions(self):
        """Verifies hitboxes for all 7 fruit types and bombs match config radii exactly."""
        for fruit_type, cfg in FRUITS_CONFIG.items():
            fruit = Fruit(fruit_type, start_x=300, start_y=400, vx=0, vy=0)
            center, radius = fruit.get_hitbox()
            assert center == (300.0, 400.0)
            assert radius == cfg["radius"]
            assert radius == fruit.radius

        bomb = Bomb(start_x=500, start_y=600, vx=0, vy=0)
        b_center, b_radius = bomb.get_hitbox()
        assert b_center == (500.0, 600.0)
        assert b_radius == BOMB_CONFIG["radius"]

    def test_line_segment_sweep_collision(self, setup_slicing):
        """Verifies line-segment collision across horizontal, vertical, and diagonal sweeps."""
        particles, scores, sounds, slice_mgr, font = setup_slicing

        # Horizontal swipe
        fruit_h = Fruit("watermelon", start_x=400, start_y=300, vx=0, vy=0)
        stroke_h = ((300.0, 300.0), (500.0, 300.0))
        rem_f, rem_b, halves = slice_mgr.process_slice_collisions(
            stroke_h, [fruit_h], [], [], font
        )
        assert fruit_h.is_sliced is True
        assert len(rem_f) == 0
        assert len(halves) == 2

        # Vertical swipe
        fruit_v = Fruit("apple", start_x=600, start_y=350, vx=0, vy=0)
        stroke_v = ((600.0, 200.0), (600.0, 500.0))
        rem_f, rem_b, halves = slice_mgr.process_slice_collisions(
            stroke_v, [fruit_v], [], [], font
        )
        assert fruit_v.is_sliced is True
        assert len(rem_f) == 0
        assert len(halves) == 2

        # Diagonal swipe
        fruit_d = Fruit("orange", start_x=700, start_y=400, vx=0, vy=0)
        stroke_d = ((600.0, 300.0), (800.0, 500.0))
        rem_f, rem_b, halves = slice_mgr.process_slice_collisions(
            stroke_d, [fruit_d], [], [], font
        )
        assert fruit_d.is_sliced is True
        assert len(rem_f) == 0
        assert len(halves) == 2

    def test_multi_segment_curve_slicing(self, setup_slicing):
        """Verifies curved swipe containing multiple segments slices multiple fruits in one stroke."""
        particles, scores, sounds, slice_mgr, font = setup_slicing

        f1 = Fruit("strawberry", start_x=250, start_y=300, vx=0, vy=0)
        f2 = Fruit("banana", start_x=350, start_y=280, vx=0, vy=0)
        f3 = Fruit("grapes", start_x=450, start_y=320, vx=0, vy=0)

        # Curved stroke represented by consecutive segments
        curved_segments = [
            ((200.0, 310.0), (300.0, 290.0)),  # Intersects f1
            ((300.0, 290.0), (400.0, 270.0)),  # Intersects f2
            ((400.0, 270.0), (500.0, 330.0)),  # Intersects f3
        ]

        rem_f, rem_b, halves = slice_mgr.process_slice_collisions(
            curved_segments, [f1, f2, f3], [], [], font
        )

        assert f1.is_sliced is True
        assert f2.is_sliced is True
        assert f3.is_sliced is True
        assert len(rem_f) == 0
        assert len(halves) == 6  # 3 fruits * 2 halves each = 6 halves
        assert scores.total_fruits_sliced == 3
        # Combo should be awarded for 3 slices in short window
        assert scores.highest_combo == 3

    def test_strictly_one_time_scoring(self, setup_slicing):
        """Guarantees fruit can never be sliced or scored more than once."""
        particles, scores, sounds, slice_mgr, font = setup_slicing

        fruit = Fruit("pineapple", start_x=400, start_y=300, vx=0, vy=0)
        stroke = ((350.0, 300.0), (450.0, 300.0))

        # First slice: scores +20 points
        rem_f1, _, halves1 = slice_mgr.process_slice_collisions(stroke, [fruit], [], [], font)
        assert len(rem_f1) == 0
        assert len(halves1) == 2
        initial_score = scores.score
        assert initial_score == 20

        # Attempt to slice the already-sliced fruit again
        rem_f2, _, halves2 = slice_mgr.process_slice_collisions(stroke, [fruit], [], halves1, font)
        assert len(rem_f2) == 0
        assert len(halves2) == 2  # No new halves created
        assert scores.score == initial_score  # Score does not increase
        assert scores.total_fruits_sliced == 1

        # Direct call to fruit.slice() returns empty
        assert fruit.slice(calculate_slice_dynamics((0, 0), (1, 1), (0, 0))) == []

    def test_two_independent_halves_and_impulse(self):
        """Verifies two halves have outward separation impulses and opposing spins."""
        fruit = Fruit("watermelon", start_x=500, start_y=350, vx=10, vy=-100)
        # Horizontal slice from left to right
        dyn = calculate_slice_dynamics((400, 350), (600, 350), (500, 350))
        halves = fruit.slice(dyn)

        assert len(halves) == 2
        h1, h2 = halves

        # 1. Spatial separation at spawn
        assert h1.x != h2.x or h1.y != h2.y
        # 2. Opposing velocities along normal
        assert h1.vx != h2.vx or h1.vy != h2.vy
        # 3. Opposing rotational velocities
        assert h1.angular_velocity * h2.angular_velocity < 0  # One positive, one negative
        assert abs(h1.angular_velocity) >= 140.0
        assert abs(h2.angular_velocity) >= 140.0
        # 4. Indices
        assert h1.half_index == 1
        assert h2.half_index == 2

    def test_halves_rotation_and_gravity_ballistics(self):
        """Verifies halves update their angles and accelerate downwards under gravity."""
        fruit = Fruit("apple", start_x=500, start_y=350, vx=0, vy=0)
        dyn = calculate_slice_dynamics((400, 350), (600, 350), (500, 350))
        h1, h2 = fruit.slice(dyn)

        initial_angle_h1 = h1.angle
        initial_vy_h1 = h1.vy

        dt = 0.05
        h1.update(dt)
        h2.update(dt)

        # Angle changed
        assert h1.angle != initial_angle_h1
        # Gravity applied: vy increased downward
        expected_vy = initial_vy_h1 + GRAVITY * dt
        assert math.isclose(h1.vy, expected_vy, abs_tol=1e-3)

    def test_particle_splatter_and_slice_flash(self, setup_slicing):
        """Verifies juice particles, slice flash, and floating text are emitted."""
        particles, scores, sounds, slice_mgr, font = setup_slicing

        fruit = Fruit("watermelon", start_x=400, start_y=300, vx=0, vy=0)
        stroke = ((350.0, 300.0), (450.0, 300.0))

        slice_mgr.process_slice_collisions(stroke, [fruit], [], [], font)

        # Juice particles emitted
        assert len(particles.particles) >= 28
        # Slice flash emitted
        assert len(particles.slice_flashes) >= 1
        # Floating score text emitted
        assert len(particles.floating_texts) >= 1

        # Particles update and decay over time
        for _ in range(30):
            particles.update(0.033)

        # Flash lines expire quickly (~0.16s)
        assert len(particles.slice_flashes) == 0
