"""
Fingertip motion tracker and virtual blade velocity calculator.
Smooths coordinate jitter using an adaptive velocity-dependent filter,
computes real-time velocity, manages blade trail history,
and classifies deliberate slicing motions versus stationary/slow drifts.
"""

import math
import time
from collections import deque
from typing import Optional, Tuple, List, Deque


class FingertipTracker:
    """
    Tracks the smoothed index fingertip position, calculates movement velocity,
    maintains blade trail points, and flags valid slice gestures.
    Uses adaptive velocity-based smoothing for rock-solid stability when stationary
    and zero-lag responsiveness during rapid slicing strokes.
    """

    def __init__(
        self,
        smoothing_alpha: float = 0.65,
        min_slice_speed: float = 320.0,
        min_slice_distance: float = 14.0,
        max_trail_points: int = 18,
        use_adaptive: bool = True,
        min_alpha: float = 0.45,
        max_alpha: float = 0.88,
    ):
        self.smoothing_alpha = smoothing_alpha
        self.use_adaptive = use_adaptive
        self.min_alpha = min_alpha
        self.max_alpha = max_alpha
        self.min_slice_speed = min_slice_speed
        self.min_slice_distance = min_slice_distance
        self.max_trail_points = max_trail_points

        # Current smoothed state
        self.current_pos: Optional[Tuple[float, float]] = None
        self.prev_pos: Optional[Tuple[float, float]] = None
        self.last_update_time: Optional[float] = None

        # Velocity metrics
        self.current_speed: float = 0.0  # px / sec
        self.last_distance: float = 0.0  # px moved in last update
        self.is_slicing: bool = False
        self.is_hand_present: bool = False

        # Trail history: deque of (x, y, timestamp)
        self.trail: Deque[Tuple[float, float, float]] = deque(maxlen=max_trail_points)

    def update(
        self,
        raw_pos: Optional[Tuple[float, float]],
        current_time: Optional[float] = None
    ) -> Tuple[Optional[Tuple[float, float]], bool]:
        """
        Updates the tracker with a new raw fingertip position.
        Returns:
            (smoothed_pos, is_slicing)
        """
        now = current_time if current_time is not None else time.time()

        if raw_pos is None:
            # Hand disappeared or not detected
            self.is_hand_present = False
            self.is_slicing = False
            self.current_speed = 0.0
            self.last_distance = 0.0
            self.prev_pos = None
            self.current_pos = None
            self.last_update_time = None
            return None, False

        self.is_hand_present = True
        rx, ry = raw_pos

        # Initialize if first detection or reappearance
        if self.current_pos is None or self.last_update_time is None:
            self.current_pos = (float(rx), float(ry))
            self.prev_pos = (float(rx), float(ry))
            self.last_update_time = now
            self.current_speed = 0.0
            self.last_distance = 0.0
            self.is_slicing = False
            self.trail.clear()
            self.trail.append((rx, ry, now))
            return self.current_pos, False

        dt = now - self.last_update_time
        # Prevent division by zero or large dt after pause
        if dt <= 0.0001:
            dt = 0.001
        elif dt > 0.25:
            # Reconnected after lag; reset tracking baseline
            self.current_pos = (float(rx), float(ry))
            self.prev_pos = (float(rx), float(ry))
            self.last_update_time = now
            self.current_speed = 0.0
            self.last_distance = 0.0
            self.is_slicing = False
            self.trail.clear()
            self.trail.append((rx, ry, now))
            return self.current_pos, False

        curr_x, curr_y = self.current_pos

        # Calculate effective smoothing alpha
        if not self.use_adaptive:
            effective_alpha = self.smoothing_alpha
        else:
            # Raw velocity estimate
            raw_dist = math.hypot(rx - curr_x, ry - curr_y)
            raw_speed = raw_dist / dt
            # Scale alpha from min_alpha (stationary) to max_alpha (fast swipe)
            speed_factor = min(1.0, raw_speed / max(1.0, self.min_slice_speed * 1.5))
            effective_alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * speed_factor

        # Exponential Moving Average Smoothing
        smooth_x = effective_alpha * rx + (1.0 - effective_alpha) * curr_x
        smooth_y = effective_alpha * ry + (1.0 - effective_alpha) * curr_y
        new_smoothed = (smooth_x, smooth_y)

        # Distance moved from previous smoothed pos
        dx = smooth_x - curr_x
        dy = smooth_y - curr_y
        dist = math.hypot(dx, dy)

        # Speed in pixels per second
        speed = dist / dt

        # Update historical state
        self.prev_pos = self.current_pos
        self.current_pos = new_smoothed
        self.last_update_time = now
        self.last_distance = dist
        self.current_speed = speed

        # Slicing condition: must exceed both speed and minimum step distance
        self.is_slicing = (speed >= self.min_slice_speed) and (dist >= self.min_slice_distance)

        # Append to trail deque
        self.trail.append((smooth_x, smooth_y, now))

        return self.current_pos, self.is_slicing

    def get_slice_segment(self) -> Optional[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Returns the active blade segment ((x1, y1), (x2, y2)) if slicing is active.
        """
        if self.is_slicing and self.prev_pos and self.current_pos:
            return (self.prev_pos, self.current_pos)
        return None

    def get_active_slice_segments(self) -> List[Tuple[Tuple[float, float], Tuple[float, float]]]:
        """
        Returns all active stroke segments from recent trail points during the slicing gesture.
        Ensures continuous, unbroken collision coverage even during high-velocity swipes.
        """
        if not self.is_slicing or len(self.trail) < 2:
            return []
        pts = [(p[0], p[1]) for p in self.trail]
        recent = pts[-4:]  # Up to 3 recent segments
        segments = []
        for i in range(len(recent) - 1):
            segments.append((recent[i], recent[i + 1]))
        return segments

    def get_trail_points(self) -> List[Tuple[float, float, float]]:
        """
        Returns list of (x, y, timestamp) points in chronological order.
        """
        return list(self.trail)

    def clear(self):
        """Reset tracker state."""
        self.current_pos = None
        self.prev_pos = None
        self.last_update_time = None
        self.current_speed = 0.0
        self.last_distance = 0.0
        self.is_slicing = False
        self.is_hand_present = False
        self.trail.clear()
