"""
Fruit, FruitHalf, and Bomb game entity representations.
Includes procedural graphic generation with realistic fruit skins, pulp, seeds,
and sliced halves with dynamic rotational physics and outward separation.
"""

import math
import random
from typing import Tuple, List, Optional, Dict, Any
import pygame

from config import (
    FRUITS_CONFIG,
    BOMB_CONFIG,
    GRAVITY,
    HALF_ANGULAR_VELOCITY_MAX,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)
from game.assets import AssetCache


class Fruit:
    """
    Represents an active airborne fruit with ballistics, rotation, and slicing states.
    """

    def __init__(
        self,
        fruit_type: str,
        start_x: float,
        start_y: float,
        vx: float,
        vy: float,
        image_surface: Optional[pygame.Surface] = None,
    ):
        self.fruit_type = fruit_type
        self.cfg = FRUITS_CONFIG.get(fruit_type, FRUITS_CONFIG["apple"])
        self.name = self.cfg["name"]
        self.radius = self.cfg["radius"]
        self.points = self.cfg["points"]
        self.color_outer = self.cfg["color_outer"]
        self.color_inner = self.cfg["color_inner"]
        self.juice_color = self.cfg["juice_color"]
        self.seed_color = self.cfg["seed_color"]

        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.angle = random.uniform(0, 360)
        self.angular_velocity = random.uniform(-180.0, 180.0)  # Deg / sec

        self.is_sliced = False
        self.has_peaked = False
        self.custom_surface = image_surface if image_surface is not None else AssetCache.get_fruit_surface(fruit_type)

    def update(self, dt: float):
        """Advances fruit physics by dt seconds."""
        if self.is_sliced:
            return

        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.angular_velocity * dt) % 360.0

        if self.vy > 0 and not self.has_peaked:
            self.has_peaked = True

    def is_offscreen(self, max_height: int = SCREEN_HEIGHT) -> bool:
        """Checks if fruit fell below screen bottom after being airborne."""
        return self.y > (max_height + self.radius + 30) and self.vy > 0

    def get_hitbox(self) -> Tuple[Tuple[float, float], float]:
        """Returns ((center_x, center_y), radius) for collision detection."""
        return ((self.x, self.y), float(self.radius))

    def slice(self, slice_dynamics: Dict[str, Any]) -> List["FruitHalf"]:
        """
        Marks fruit as sliced and instantiates two separating FruitHalf entities.
        Guarantees that slicing only happens once.
        """
        if self.is_sliced:
            return []

        self.is_sliced = True
        cut_angle = slice_dynamics["cut_angle_deg"]
        h1_impulse = slice_dynamics["half1_impulse"]
        h2_impulse = slice_dynamics["half2_impulse"]
        normal = slice_dynamics.get("normal", (0.0, 1.0))

        # Initial separation offset along cut normal for instant visual feedback
        sep_dist = 8.0
        h1_x = self.x + normal[0] * sep_dist
        h1_y = self.y + normal[1] * sep_dist
        h2_x = self.x - normal[0] * sep_dist
        h2_y = self.y - normal[1] * sep_dist

        # Half 1
        h1 = FruitHalf(
            fruit_type=self.fruit_type,
            cfg=self.cfg,
            center_x=h1_x,
            center_y=h1_y,
            vx=self.vx + h1_impulse[0],
            vy=self.vy + h1_impulse[1],
            angle=cut_angle,
            angular_velocity=random.uniform(-HALF_ANGULAR_VELOCITY_MAX, -140.0),
            half_index=1,
            cut_angle_deg=cut_angle,
        )

        # Half 2
        h2 = FruitHalf(
            fruit_type=self.fruit_type,
            cfg=self.cfg,
            center_x=h2_x,
            center_y=h2_y,
            vx=self.vx + h2_impulse[0],
            vy=self.vy + h2_impulse[1],
            angle=cut_angle,
            angular_velocity=random.uniform(140.0, HALF_ANGULAR_VELOCITY_MAX),
            half_index=2,
            cut_angle_deg=cut_angle,
        )

        return [h1, h2]

    def render(self, surface: pygame.Surface):
        """Draws the fruit onto the pygame surface."""
        if self.is_sliced:
            return

        cx, cy = int(self.x), int(self.y)
        r = int(self.radius)

        if self.custom_surface is not None:
            # Rotate custom asset surface
            rotated = pygame.transform.rotate(self.custom_surface, self.angle)
            rect = rotated.get_rect(center=(cx, cy))
            surface.blit(rotated, rect)
            return

        # High-quality procedural rendering
        temp_surf = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        tcx, tcy = r + 4, r + 4

        # Outer body with rim
        pygame.draw.circle(temp_surf, self.color_outer, (tcx, tcy), r)
        # Inner pulp / gradient shading
        inner_r = max(2, int(r * 0.88))
        pygame.draw.circle(temp_surf, self.color_inner, (tcx, tcy), inner_r)

        # Unique fruit detail textures
        if self.fruit_type == "watermelon":
            # Dark green stripes on outer rind
            for i in range(0, 360, 45):
                rad = math.radians(i)
                sx = tcx + int(math.cos(rad) * (r - 2))
                sy = tcy + int(math.sin(rad) * (r - 2))
                pygame.draw.circle(temp_surf, (15, 75, 25), (sx, sy), max(2, r // 10))
            # Seeds
            for seed_offset in [(-12, -8), (10, -10), (-6, 12), (12, 10), (0, 0)]:
                spos = (tcx + seed_offset[0] * r // 45, tcy + seed_offset[1] * r // 45)
                pygame.draw.circle(temp_surf, self.seed_color, spos, max(2, r // 18))

        elif self.fruit_type == "orange":
            # Citrus segments
            for i in range(0, 360, 45):
                rad = math.radians(i)
                ex = tcx + int(math.cos(rad) * (inner_r - 4))
                ey = tcy + int(math.sin(rad) * (inner_r - 4))
                pygame.draw.line(temp_surf, (255, 230, 180), (tcx, tcy), (ex, ey), 2)
            pygame.draw.circle(temp_surf, (255, 240, 200), (tcx, tcy), max(3, r // 10))

        elif self.fruit_type == "banana":
            # Slight banana curve accent
            pygame.draw.arc(temp_surf, (210, 180, 20), (tcx - r, tcy - r, r * 2, r * 2), 0.2, 1.8, 3)

        elif self.fruit_type == "apple":
            # Core and stem highlight
            pygame.draw.circle(temp_surf, (60, 30, 15), (tcx, tcy - r + 3), max(2, r // 12))

        # Specular 3D highlight gloss
        hl_x = tcx - int(r * 0.35)
        hl_y = tcy - int(r * 0.35)
        hl_r = max(3, int(r * 0.22))
        pygame.draw.circle(temp_surf, (255, 255, 255, 120), (hl_x, hl_y), hl_r)

        # Rotate and blit
        rotated = pygame.transform.rotate(temp_surf, self.angle)
        rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, rect)


class FruitHalf:
    """
    Represents one sliced half of a fruit flying away along its trajectory.
    """

    def __init__(
        self,
        fruit_type: str,
        cfg: Dict[str, Any],
        center_x: float,
        center_y: float,
        vx: float,
        vy: float,
        angle: float,
        angular_velocity: float,
        half_index: int,
        cut_angle_deg: float,
    ):
        self.fruit_type = fruit_type
        self.cfg = cfg
        self.radius = cfg["radius"]
        self.color_outer = cfg["color_outer"]
        self.color_inner = cfg["color_inner"]
        self.juice_color = cfg["juice_color"]
        self.seed_color = cfg["seed_color"]

        self.x = float(center_x)
        self.y = float(center_y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.angle = float(angle)
        self.angular_velocity = float(angular_velocity)
        self.half_index = half_index
        self.cut_angle_deg = cut_angle_deg
        self.custom_surface = AssetCache.get_half_surface(fruit_type, half_index)

    def update(self, dt: float):
        """Advances fruit half physics."""
        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.angular_velocity * dt) % 360.0

    def is_offscreen(self, max_height: int = SCREEN_HEIGHT) -> bool:
        """Returns True if half has fallen below screen."""
        return self.y > (max_height + self.radius + 40) and self.vy > 0

    def render(self, surface: pygame.Surface):
        """Renders the sliced semicircle half with visible pulp and cut face."""
        cx, cy = int(self.x), int(self.y)
        r = int(self.radius)

        if self.custom_surface is not None:
            rotated = pygame.transform.rotate(self.custom_surface, self.angle)
            rect = rotated.get_rect(center=(cx, cy))
            surface.blit(rotated, rect)
            return

        surf_size = r * 2 + 10
        temp_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        tcx, tcy = surf_size // 2, surf_size // 2

        # Draw semicircle representing the half
        # Half 1 draws angle 0 to 180, Half 2 draws 180 to 360 relative to base cut
        start_angle = 0 if self.half_index == 1 else math.pi
        end_angle = math.pi if self.half_index == 1 else 2 * math.pi

        # Outer curved skin
        points = [(tcx, tcy)]
        steps = 24
        for step in range(steps + 1):
            theta = start_angle + (end_angle - start_angle) * (step / steps)
            px = tcx + int(math.cos(theta) * r)
            py = tcy - int(math.sin(theta) * r)
            points.append((px, py))
        pygame.draw.polygon(temp_surf, self.color_outer, points)

        # Inner edible flesh semicircle
        inner_r = max(2, int(r * 0.88))
        inner_points = [(tcx, tcy)]
        for step in range(steps + 1):
            theta = start_angle + (end_angle - start_angle) * (step / steps)
            px = tcx + int(math.cos(theta) * inner_r)
            py = tcy - int(math.sin(theta) * inner_r)
            inner_points.append((px, py))
        pygame.draw.polygon(temp_surf, self.color_inner, inner_points)

        # Cut face edge line (flat cut surface)
        if self.half_index == 1:
            pygame.draw.line(temp_surf, (255, 255, 255, 180), (tcx - r, tcy), (tcx + r, tcy), 3)
        else:
            pygame.draw.line(temp_surf, (255, 255, 255, 180), (tcx - r, tcy), (tcx + r, tcy), 3)

        # Rotate half by dynamic angle
        rotated = pygame.transform.rotate(temp_surf, self.angle)
        rect = rotated.get_rect(center=(cx, cy))
        surface.blit(rotated, rect)


class Bomb:
    """
    Represents an airborne bomb. Slicing it triggers explosion penalty or instant game over.
    """

    def __init__(
        self,
        start_x: float,
        start_y: float,
        vx: float,
        vy: float,
    ):
        self.radius = BOMB_CONFIG["radius"]
        self.color_body = BOMB_CONFIG["color_body"]
        self.color_rim = BOMB_CONFIG["color_rim"]
        self.fuse_color = BOMB_CONFIG["fuse_spark_color"]

        self.x = float(start_x)
        self.y = float(start_y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.angle = 0.0
        self.angular_velocity = random.uniform(-100.0, 100.0)

        self.is_sliced = False
        self.fuse_timer = 0.0

    def update(self, dt: float):
        """Advances bomb physics and fuse animation."""
        if self.is_sliced:
            return

        self.vy += GRAVITY * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle = (self.angle + self.angular_velocity * dt) % 360.0
        self.fuse_timer += dt

    def is_offscreen(self, max_height: int = SCREEN_HEIGHT) -> bool:
        """Returns True if bomb fell below screen."""
        return self.y > (max_height + self.radius + 30) and self.vy > 0

    def get_hitbox(self) -> Tuple[Tuple[float, float], float]:
        """Returns ((center_x, center_y), radius)."""
        return ((self.x, self.y), float(self.radius))

    def render(self, surface: pygame.Surface):
        """Renders bomb sphere with fuse rope and animated sparking particles."""
        if self.is_sliced:
            return

        cx, cy = int(self.x), int(self.y)
        r = int(self.radius)

        # Metallic bomb sphere
        pygame.draw.circle(surface, self.color_body, (cx, cy), r)
        pygame.draw.circle(surface, self.color_rim, (cx, cy), r, 3)

        # Highlight reflection
        pygame.draw.circle(surface, (110, 115, 130), (cx - r // 3, cy - r // 3), max(3, r // 4))

        # Skull / Warning crossbones accent
        pygame.draw.line(surface, (230, 45, 45), (cx - 10, cy - 10), (cx + 10, cy + 10), 3)
        pygame.draw.line(surface, (230, 45, 45), (cx + 10, cy - 10), (cx - 10, cy + 10), 3)

        # Fuse cap & curved fuse rope
        cap_rect = pygame.Rect(cx - 7, cy - r - 6, 14, 8)
        pygame.draw.rect(surface, (120, 125, 140), cap_rect, border_radius=2)

        fuse_tip_x = cx + 14
        fuse_tip_y = cy - r - 16
        pygame.draw.lines(surface, (180, 140, 70), False, [
            (cx, cy - r - 4),
            (cx + 6, cy - r - 10),
            (fuse_tip_x, fuse_tip_y)
        ], 3)

        # Sparking fuse animation
        spark_r = random.randint(4, 8)
        pygame.draw.circle(surface, (255, 230, 50), (fuse_tip_x, fuse_tip_y), spark_r)
        pygame.draw.circle(surface, (255, 90, 20), (fuse_tip_x, fuse_tip_y), max(2, spark_r // 2))

        # Tiny flying embers
        for _ in range(2):
            ex = fuse_tip_x + random.randint(-8, 8)
            ey = fuse_tip_y + random.randint(-8, 8)
            pygame.draw.circle(surface, (255, 240, 120), (ex, ey), 2)
