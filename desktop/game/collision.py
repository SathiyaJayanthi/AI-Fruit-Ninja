"""
Collision detection algorithms for blade strokes and circular hitboxes.
Uses line-segment versus circle intersection to accurately detect slices.
"""

import math
from typing import Tuple, Optional, Dict, Any


def line_segment_circle_intersection(
    p1: Tuple[float, float],
    p2: Tuple[float, float],
    center: Tuple[float, float],
    radius: float
) -> Tuple[bool, Optional[Tuple[float, float]], float]:
    """
    Determines if the line segment from p1 to p2 intersects a circle.

    Args:
        p1: Start point of segment (x1, y1)
        p2: End point of segment (x2, y2)
        center: Circle center (cx, cy)
        radius: Circle radius R

    Returns:
        (intersects: bool, closest_point: Optional[Tuple[float, float]], distance: float)
    """
    x1, y1 = p1
    x2, y2 = p2
    cx, cy = center

    dx = x2 - x1
    dy = y2 - y1
    segment_len_sq = dx * dx + dy * dy

    if segment_len_sq <= 0.000001:
        # Segment is essentially a single point
        dist = math.hypot(cx - x1, cy - y1)
        return (dist <= radius, (x1, y1), dist)

    # Project vector (center - p1) onto segment vector (p2 - p1)
    # t is the normalized position along the segment [0, 1]
    t = ((cx - x1) * dx + (cy - y1) * dy) / segment_len_sq
    t_clamped = max(0.0, min(1.0, t))

    closest_x = x1 + t_clamped * dx
    closest_y = y1 + t_clamped * dy

    dist_x = cx - closest_x
    dist_y = cy - closest_y
    dist = math.hypot(dist_x, dist_y)

    intersects = (dist <= radius)
    return (intersects, (closest_x, closest_y), dist)


def calculate_slice_dynamics(
    blade_start: Tuple[float, float],
    blade_end: Tuple[float, float],
    fruit_center: Tuple[float, float]
) -> Dict[str, Any]:
    """
    Calculates the cut angle, normal vector, and separation impulses for two fruit halves.

    Returns:
        dict containing:
            - cut_angle_rad: angle of slice in radians
            - cut_angle_deg: angle of slice in degrees
            - normal_x, normal_y: unit normal vector perpendicular to slice
            - half1_impulse: (vx, vy) for half 1
            - half2_impulse: (vx, vy) for half 2
    """
    x1, y1 = blade_start
    x2, y2 = blade_end

    dx = x2 - x1
    dy = y2 - y1
    length = math.hypot(dx, dy)

    if length <= 0.0001:
        dx, dy = 1.0, 0.0
        length = 1.0

    # Unit vector along the cut
    unit_cut_x = dx / length
    unit_cut_y = dy / length

    # Unit normal perpendicular to the cut
    normal_x = -unit_cut_y
    normal_y = unit_cut_x

    cut_angle_rad = math.atan2(dy, dx)
    cut_angle_deg = math.degrees(cut_angle_rad)

    # Impulse magnitude for fruit halves separation
    impulse_speed = 130.0

    half1_vx = normal_x * impulse_speed
    half1_vy = normal_y * impulse_speed - 60.0  # slight upward pop

    half2_vx = -normal_x * impulse_speed
    half2_vy = -normal_y * impulse_speed - 60.0

    return {
        "cut_angle_rad": cut_angle_rad,
        "cut_angle_deg": cut_angle_deg,
        "normal": (normal_x, normal_y),
        "half1_impulse": (half1_vx, half1_vy),
        "half2_impulse": (half2_vx, half2_vy),
    }
