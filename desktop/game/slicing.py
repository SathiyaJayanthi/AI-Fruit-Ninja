"""
Virtual slicing blade manager and visual trail renderer.
Renders multi-layered glowing neon blade trails, computes slice stroke segment,
and executes collision resolution with active fruits and bombs.
"""

import math
import time
from typing import List, Tuple, Optional, Dict, Any
import pygame

from config import (
    BLADE_COLOR_CORE,
    BLADE_COLOR_GLOW,
    BLADE_COLOR_OUTER,
    BLADE_WIDTH_BASE,
)
from game.collision import line_segment_circle_intersection, calculate_slice_dynamics
from game.fruit import Fruit, FruitHalf, Bomb
from game.particles import ParticleSystem
from game.scoring import ScoreManager
from game.sound import SoundManager


class BladeRenderer:
    """
    Renders an arcade-style glowing neon blade trail following the fingertip.
    Uses multi-pass alpha blending for inner core and outer glow, tapering with age.
    """

    def __init__(
        self,
        color_core: Tuple[int, int, int] = BLADE_COLOR_CORE,
        color_glow: Tuple[int, int, int] = BLADE_COLOR_GLOW,
        color_outer: Tuple[int, int, int] = BLADE_COLOR_OUTER,
        base_width: float = BLADE_WIDTH_BASE,
    ):
        self.color_core = color_core
        self.color_glow = color_glow
        self.color_outer = color_outer
        self.base_width = base_width

    def render(
        self,
        surface: pygame.Surface,
        trail_points: List[Tuple[float, float, float]],
        is_slicing: bool,
    ):
        """
        Renders the blade trail onto the target surface.
        trail_points: list of (x, y, timestamp) ordered oldest to newest.
        """
        if len(trail_points) < 2:
            if len(trail_points) == 1:
                # Single tip point
                x, y, _ = trail_points[0]
                pygame.draw.circle(surface, self.color_glow, (int(x), int(y)), 8)
                pygame.draw.circle(surface, self.color_core, (int(x), int(y)), 4)
            return

        now = time.time()
        n = len(trail_points)

        # Multi-segment tapered render
        for i in range(n - 1):
            p1_x, p1_y, t1 = trail_points[i]
            p2_x, p2_y, t2 = trail_points[i + 1]

            # Progress from tail (0.0) to fingertip (1.0)
            progress = (i + 1) / n
            alpha_factor = progress ** 1.3

            # Width tapers: thin at tail, thick near tip
            outer_w = max(2, int(self.base_width * progress))
            glow_w = max(2, int(self.base_width * 0.65 * progress))
            core_w = max(1, int(self.base_width * 0.3 * progress))

            # Alpha fade for outer glow
            alpha = int(220 * alpha_factor)
            if is_slicing:
                # Extra brightness and thickness when actively slicing
                outer_w = int(outer_w * 1.35)
                alpha = min(255, int(alpha * 1.2))

            # Pass 1: Outer soft glow
            pygame.draw.line(
                surface,
                self.color_outer,
                (int(p1_x), int(p1_y)),
                (int(p2_x), int(p2_y)),
                outer_w
            )

            # Pass 2: Vibrant cyan glow
            pygame.draw.line(
                surface,
                self.color_glow,
                (int(p1_x), int(p1_y)),
                (int(p2_x), int(p2_y)),
                glow_w
            )

            # Pass 3: Brilliant white core
            pygame.draw.line(
                surface,
                self.color_core,
                (int(p1_x), int(p1_y)),
                (int(p2_x), int(p2_y)),
                core_w
            )

        # Render brilliant flare at active fingertip
        tip_x, tip_y, _ = trail_points[-1]
        flare_radius = 12 if is_slicing else 8
        pygame.draw.circle(surface, self.color_outer, (int(tip_x), int(tip_y)), flare_radius + 4)
        pygame.draw.circle(surface, self.color_glow, (int(tip_x), int(tip_y)), flare_radius)
        pygame.draw.circle(surface, self.color_core, (int(tip_x), int(tip_y)), max(3, flare_radius // 2))

    def render_hand_skeleton(
        self,
        surface: pygame.Surface,
        landmarks: List[Tuple[int, int, float]],
        is_slicing: bool = False,
    ):
        """
        Renders an arcade glowing cybernetic hand skeleton with bright light beams
        connecting all 21 finger joints directly onto the main game display.
        """
        if not landmarks or len(landmarks) < 21:
            return

        connections = [
            (0, 1), (1, 2), (2, 3), (3, 4),        # Thumb
            (0, 5), (5, 6), (6, 7), (7, 8),        # Index Finger
            (0, 9), (9, 10), (10, 11), (11, 12),   # Middle Finger
            (0, 13), (13, 14), (14, 15), (15, 16), # Ring Finger
            (0, 17), (17, 18), (18, 19), (19, 20), # Pinky
            (5, 9), (9, 13), (13, 17),             # Knuckle bridge
        ]

        # 1. Draw bright light beams connecting finger joints
        for idx1, idx2 in connections:
            if idx1 >= len(landmarks) or idx2 >= len(landmarks):
                continue
            p1 = (int(landmarks[idx1][0]), int(landmarks[idx1][1]))
            p2 = (int(landmarks[idx2][0]), int(landmarks[idx2][1]))

            # Outer glow
            pygame.draw.line(surface, self.color_outer, p1, p2, 7)
            # Vivid neon beam
            pygame.draw.line(surface, self.color_glow, p1, p2, 3)
            # Pure white laser core
            pygame.draw.line(surface, (255, 255, 255), p1, p2, 1)

        # 2. Draw bright radiant light nodes on all joints
        tips = {4, 8, 12, 16, 20}
        for idx, lm in enumerate(landmarks):
            x, y = int(lm[0]), int(lm[1])
            is_index_tip = (idx == 8)
            base_r = 12 if is_index_tip else (7 if idx in tips else 5)

            # Outer soft halo
            pygame.draw.circle(surface, self.color_outer, (x, y), base_r + 4)
            # Radiant neon sphere
            pygame.draw.circle(surface, self.color_glow, (x, y), base_r)
            # Brilliant white center light
            pygame.draw.circle(surface, (255, 255, 255), (x, y), max(2, int(base_r * 0.45)))

            if is_index_tip:
                # Pulsing energy ring for blade emitter
                ring_r = base_r + 6 if not is_slicing else base_r + 10
                pygame.draw.circle(surface, (255, 255, 255), (x, y), ring_r, 2)


class SliceManager:
    """
    Coordinates collision detection between the blade stroke and active game entities.
    Executes slicing mechanics, particle generation, sound triggers, and scoring.
    """

    def __init__(
        self,
        particle_system: ParticleSystem,
        score_manager: ScoreManager,
        sound_manager: SoundManager,
    ):
        self.particles = particle_system
        self.scores = score_manager
        self.sounds = sound_manager
        self.blade_renderer = BladeRenderer()

    def process_slice_collisions(
        self,
        slice_segment: Any,
        active_fruits: List[Fruit],
        active_bombs: List[Bomb],
        active_halves: List[FruitHalf],
        font: pygame.font.Font,
    ) -> Tuple[List[Fruit], List[Bomb], List[FruitHalf]]:
        """
        Tests active slice segment(s) against all fruits and bombs.
        Splits hit fruits into halves, triggers particles/audio, and scores points.
        Supports both single segment and multi-segment continuous strokes.
        """
        if slice_segment is None:
            return active_fruits, active_bombs, active_halves

        # Normalize to list of segments
        segments = []
        if isinstance(slice_segment, list):
            segments = slice_segment
        elif isinstance(slice_segment, tuple):
            if len(slice_segment) == 2 and isinstance(slice_segment[0], tuple):
                segments = [slice_segment]

        if not segments:
            return active_fruits, active_bombs, active_halves

        remaining_fruits: List[Fruit] = []
        remaining_bombs: List[Bomb] = []
        new_halves: List[FruitHalf] = []

        # 1. Test Fruits
        for fruit in active_fruits:
            if fruit.is_sliced:
                continue

            center, radius = fruit.get_hitbox()
            hit = False
            hit_pt = None
            cut_seg = None

            for seg in segments:
                p1, p2 = seg
                is_hit, pt, _ = line_segment_circle_intersection(p1, p2, center, radius)
                if is_hit:
                    hit = True
                    hit_pt = pt
                    cut_seg = seg
                    break

            if hit and cut_seg:
                # Calculate cut physics and create 2 halves
                slice_dyn = calculate_slice_dynamics(cut_seg[0], cut_seg[1], center)
                halves = fruit.slice(slice_dyn)
                new_halves.extend(halves)

                # Particles & Slice Cut Flash
                hx, hy = hit_pt if hit_pt else center
                normal = slice_dyn.get("normal")
                self.particles.emit_juice_splatter(hx, hy, fruit.juice_color, count=32, normal=normal)
                self.particles.emit_slice_flash(cut_seg[0], cut_seg[1])

                # Sound effects
                self.sounds.play("slice")
                self.sounds.play("splat")

                # Scoring and combo evaluation
                score_event = self.scores.register_fruit_slice(fruit.fruit_type, fruit.points)

                # Floating score popup
                pts_awarded = score_event["base_points"]
                combo_count = score_event["combo_count"]

                if combo_count >= 2:
                    combo_bonus = score_event["combo_bonus"]
                    self.sounds.play("combo")
                    msg = f"{combo_count}x COMBO! +{combo_bonus}"
                    self.particles.add_floating_text(msg, hx, hy - 25, (255, 220, 40), font, lifetime=1.2)
                else:
                    msg = f"+{pts_awarded}"
                    self.particles.add_floating_text(msg, hx, hy - 15, (255, 255, 255), font, lifetime=0.8)
            else:
                remaining_fruits.append(fruit)

        # 2. Test Bombs
        for bomb in active_bombs:
            if bomb.is_sliced:
                continue

            center, radius = bomb.get_hitbox()
            hit = False
            for seg in segments:
                p1, p2 = seg
                is_hit, _, _ = line_segment_circle_intersection(p1, p2, center, radius)
                if is_hit:
                    hit = True
                    break

            if hit:
                bomb.is_sliced = True
                bx, by = center
                self.particles.emit_bomb_explosion(bx, by)
                self.sounds.play("explosion")
                self.scores.register_bomb_hit()
                self.particles.add_floating_text(
                    "BOMB HIT!", bx, by - 30, (255, 60, 60), font, lifetime=1.4
                )
            else:
                remaining_bombs.append(bomb)

        # Combine existing and new halves
        all_halves = active_halves + new_halves

        return remaining_fruits, remaining_bombs, all_halves
