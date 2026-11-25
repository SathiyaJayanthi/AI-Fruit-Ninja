"""
Unit tests for line-segment circle collision detection and slice dynamics.
"""

import math
import pytest
from game.collision import line_segment_circle_intersection, calculate_slice_dynamics


class TestCollisionDetection:

    def test_direct_horizontal_slice(self):
        """Slice cutting straight through the center of a circle."""
        p1 = (100.0, 300.0)
        p2 = (300.0, 300.0)
        center = (200.0, 300.0)
        radius = 40.0

        hit, closest_pt, dist = line_segment_circle_intersection(p1, p2, center, radius)
        assert hit is True
        assert closest_pt is not None
        assert math.isclose(closest_pt[0], 200.0, abs_tol=1e-3)
        assert math.isclose(closest_pt[1], 300.0, abs_tol=1e-3)
        assert math.isclose(dist, 0.0, abs_tol=1e-3)

    def test_glancing_slice(self):
        """Slice that passes within the radius but not through center."""
        p1 = (100.0, 270.0)
        p2 = (300.0, 270.0)
        center = (200.0, 300.0)
        radius = 40.0

        hit, closest_pt, dist = line_segment_circle_intersection(p1, p2, center, radius)
        assert hit is True
        assert math.isclose(dist, 30.0, abs_tol=1e-3)

    def test_near_miss_slice(self):
        """Slice passing just outside the collision radius."""
        p1 = (100.0, 250.0)
        p2 = (300.0, 250.0)
        center = (200.0, 300.0)
        radius = 40.0

        hit, closest_pt, dist = line_segment_circle_intersection(p1, p2, center, radius)
        assert hit is False
        assert math.isclose(dist, 50.0, abs_tol=1e-3)

    def test_diagonal_slice(self):
        """Diagonal swipe intersecting a circular hitbox."""
        p1 = (100.0, 100.0)
        p2 = (300.0, 300.0)
        center = (200.0, 200.0)
        radius = 35.0

        hit, closest_pt, dist = line_segment_circle_intersection(p1, p2, center, radius)
        assert hit is True
        assert math.isclose(closest_pt[0], 200.0, abs_tol=1e-3)
        assert math.isclose(closest_pt[1], 200.0, abs_tol=1e-3)
        assert math.isclose(dist, 0.0, abs_tol=1e-3)

    def test_stationary_point_inside(self):
        """Degenerate segment (point) inside circle."""
        p1 = (210.0, 300.0)
        p2 = (210.0, 300.0)
        center = (200.0, 300.0)
        radius = 40.0

        hit, closest_pt, dist = line_segment_circle_intersection(p1, p2, center, radius)
        assert hit is True
        assert math.isclose(dist, 10.0, abs_tol=1e-3)

    def test_stationary_point_outside(self):
        """Degenerate segment (point) outside circle."""
        p1 = (300.0, 300.0)
        p2 = (300.0, 300.0)
        center = (200.0, 300.0)
        radius = 40.0

        hit, closest_pt, dist = line_segment_circle_intersection(p1, p2, center, radius)
        assert hit is False
        assert math.isclose(dist, 100.0, abs_tol=1e-3)


class TestSliceDynamics:

    def test_horizontal_cut_impulse_opposition(self):
        """Verifies that halves fly in opposite directions perpendicular to cut."""
        blade_start = (100.0, 300.0)
        blade_end = (300.0, 300.0)
        fruit_center = (200.0, 300.0)

        dyn = calculate_slice_dynamics(blade_start, blade_end, fruit_center)
        h1 = dyn["half1_impulse"]
        h2 = dyn["half2_impulse"]

        # Horizontal cut (dy=0): normal is vertical (x=0, y=+-1)
        assert math.isclose(dyn["normal"][0], 0.0, abs_tol=1e-3)
        # Halves must have opposite horizontal or vertical outward velocities
        assert math.isclose(h1[0], -h2[0], abs_tol=1e-3)

    def test_cut_angle_calculation(self):
        """Verifies accurate angle determination in degrees."""
        # Horizontal cut rightwards
        dyn = calculate_slice_dynamics((0, 0), (100, 0), (50, 0))
        assert math.isclose(dyn["cut_angle_deg"], 0.0, abs_tol=1e-3)

        # Vertical cut downwards
        dyn_down = calculate_slice_dynamics((0, 0), (0, 100), (0, 50))
        assert math.isclose(dyn_down["cut_angle_deg"], 90.0, abs_tol=1e-3)
