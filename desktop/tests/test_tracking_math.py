"""
Unit tests for coordinate smoothing, velocity calculations, and slicing thresholds.
"""

import math
import pytest
from hand_tracking.tracker import FingertipTracker


class TestTrackingMath:

    def test_smoothing_convergence(self):
        """Verifies exponential moving average converges toward target position."""
        alpha = 0.5
        tracker = FingertipTracker(smoothing_alpha=alpha, use_adaptive=False)

        # First position initializes baseline
        pos, is_slicing = tracker.update((100.0, 100.0), current_time=1.0)
        assert pos == (100.0, 100.0)

        # Step towards (200.0, 200.0)
        pos2, _ = tracker.update((200.0, 200.0), current_time=1.033)
        # Expected: 0.5 * 200 + 0.5 * 100 = 150.0
        assert math.isclose(pos2[0], 150.0, abs_tol=1e-3)
        assert math.isclose(pos2[1], 150.0, abs_tol=1e-3)

    def test_adaptive_smoothing(self):
        """Verifies adaptive smoothing applies stronger smoothing when slow and responsive when fast."""
        tracker = FingertipTracker(use_adaptive=True, min_alpha=0.45, max_alpha=0.90)
        # Start at (100, 100)
        tracker.update((100.0, 100.0), current_time=1.0)
        # Small slow movement (2 px in 0.1s -> speed = 20 px/s)
        pos_slow, _ = tracker.update((102.0, 100.0), current_time=1.1)
        # Should be smoothed with near min_alpha ~0.45: 100 + 0.45 * 2 = 100.9
        assert pos_slow[0] < 101.5

    def test_slow_movement_does_not_slice(self):
        """Slow finger drift must not be classified as a deliberate slice."""
        tracker = FingertipTracker(min_slice_speed=300.0, min_slice_distance=15.0)

        # Initialize at (100, 100)
        tracker.update((100.0, 100.0), current_time=1.0)

        # Move 5 pixels over 0.1s -> speed = 50 px/s (well below 300 px/s)
        pos, is_slicing = tracker.update((105.0, 100.0), current_time=1.1)

        assert is_slicing is False
        assert tracker.current_speed < 100.0

    def test_fast_swipe_triggers_slicing(self):
        """Fast swipe exceeding speed and distance thresholds activates slicing."""
        tracker = FingertipTracker(min_slice_speed=300.0, min_slice_distance=15.0, smoothing_alpha=1.0)

        # Initialize at (100, 100)
        tracker.update((100.0, 100.0), current_time=1.0)

        # Swipe 100 pixels in 0.05s -> speed = 2000 px/s
        pos, is_slicing = tracker.update((200.0, 100.0), current_time=1.05)

        assert is_slicing is True
        assert tracker.current_speed >= 300.0
        assert tracker.last_distance >= 15.0

    def test_hand_disappearance_and_recovery(self):
        """Tracker properly resets when hand disappears and re-enters view."""
        tracker = FingertipTracker()

        tracker.update((100.0, 100.0), current_time=1.0)
        assert tracker.is_hand_present is True

        # Hand lost
        pos, is_slicing = tracker.update(None, current_time=1.1)
        assert pos is None
        assert is_slicing is False
        assert tracker.is_hand_present is False

        # Hand reappears at a completely new location
        pos_rec, _ = tracker.update((500.0, 500.0), current_time=1.5)
        assert pos_rec == (500.0, 500.0)
        assert tracker.is_hand_present is True
        assert tracker.is_slicing is False

    def test_trail_buffer_limit(self):
        """Verifies trail deque preserves max_trail_points limit."""
        tracker = FingertipTracker(max_trail_points=5)

        for i in range(10):
            tracker.update((float(i * 10), float(i * 10)), current_time=1.0 + i * 0.03)

        trail = tracker.get_trail_points()
        assert len(trail) <= 5
