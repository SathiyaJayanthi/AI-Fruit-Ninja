"""
Particle effects system for fruit juice splatters, blade glow trails,
bomb explosions, slice flashes, and floating score/combo popups.
"""

import math
import random
from typing import List, Tuple, Optional
import pygame

from config import SCREEN_WIDTH, SCREEN_HEIGHT


class Particle:
    """Represents a single physical particle (juice droplet, spark, ember)."""

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        color: Tuple[int, int, int],
        radius: float,
        lifetime: float,
        gravity: float = 500.0,
    ):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.radius = float(radius)
        self.initial_radius = float(radius)
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)
        self.gravity = float(gravity)

    def update(self, dt: float) -> bool:
        """Updates particle physics. Returns False when particle expires."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False

        self.vy += self.gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        # Shrink over lifetime
        progress = self.lifetime / self.max_lifetime
        self.radius = max(1.0, self.initial_radius * progress)
        return True

    def render(self, surface: pygame.Surface):
        """Renders particle with alpha fade."""
        if self.lifetime <= 0:
            return
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        r, g, b = self.color
        color_with_alpha = (r, g, b, alpha)

        rad = int(self.radius)
        if rad <= 1:
            surface.set_at((int(self.x), int(self.y)), (r, g, b))
        else:
            s = pygame.Surface((rad * 2 + 2, rad * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, color_with_alpha, (rad + 1, rad + 1), rad)
            surface.blit(s, (int(self.x) - rad, int(self.y) - rad))


class FloatingText:
    """Floating notification for combo awards and bonus points."""

    def __init__(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int],
        font: pygame.font.Font,
        lifetime: float = 1.0,
    ):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.font = font
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)
        self.vy = -75.0  # Float upward

    def update(self, dt: float) -> bool:
        """Moves text upward and fades out. Returns False when expired."""
        self.lifetime -= dt
        if self.lifetime <= 0:
            return False
        self.y += self.vy * dt
        return True

    def render(self, surface: pygame.Surface):
        """Renders anti-aliased text with fading transparency."""
        progress = max(0.0, self.lifetime / self.max_lifetime)
        alpha = int(255 * progress)

        text_surf = self.font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(text_surf, rect)


class Shockwave:
    """Expanding circular blast wave for bomb detonations."""

    def __init__(self, x: float, y: float, max_radius: float = 220.0, lifetime: float = 0.5):
        self.x = float(x)
        self.y = float(y)
        self.max_radius = float(max_radius)
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        return self.lifetime > 0

    def render(self, surface: pygame.Surface):
        progress = 1.0 - (self.lifetime / self.max_lifetime)
        current_r = max(4, int(self.max_radius * progress))
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        thickness = max(2, int(8 * (1.0 - progress)))

        s = pygame.Surface((current_r * 2 + 10, current_r * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 120, 40, alpha), (current_r + 5, current_r + 5), current_r, thickness)
        surface.blit(s, (int(self.x) - current_r - 5, int(self.y) - current_r - 5))


class SliceFlash:
    """Bright linear flash along the slice cut segment that quickly fades."""

    def __init__(
        self,
        p1: Tuple[float, float],
        p2: Tuple[float, float],
        color: Tuple[int, int, int] = (255, 255, 255),
        lifetime: float = 0.16,
    ):
        self.p1 = p1
        self.p2 = p2
        self.color = color
        self.lifetime = float(lifetime)
        self.max_lifetime = float(lifetime)

    def update(self, dt: float) -> bool:
        self.lifetime -= dt
        return self.lifetime > 0

    def render(self, surface: pygame.Surface):
        progress = max(0.0, self.lifetime / self.max_lifetime)
        alpha = int(255 * progress)
        width = max(1, int(4 * progress))

        min_x = int(min(self.p1[0], self.p2[0])) - 12
        min_y = int(min(self.p1[1], self.p2[1])) - 12
        max_x = int(max(self.p1[0], self.p2[0])) + 12
        max_y = int(max(self.p1[1], self.p2[1])) + 12

        w = max(2, max_x - min_x)
        h = max(2, max_y - min_y)
        s = pygame.Surface((w, h), pygame.SRCALPHA)

        lp1 = (int(self.p1[0] - min_x), int(self.p1[1] - min_y))
        lp2 = (int(self.p2[0] - min_x), int(self.p2[1] - min_y))

        # Cyan glow
        pygame.draw.line(s, (0, 230, 255, int(alpha * 0.7)), lp1, lp2, width + 4)
        # White core
        pygame.draw.line(s, (255, 255, 255, alpha), lp1, lp2, width)

        surface.blit(s, (min_x, min_y))


class ParticleSystem:
    """Manages all active particles, explosions, shockwaves, slice flashes, and floating texts."""

    def __init__(self):
        self.particles: List[Particle] = []
        self.floating_texts: List[FloatingText] = []
        self.shockwaves: List[Shockwave] = []
        self.slice_flashes: List[SliceFlash] = []

    def emit_juice_splatter(
        self,
        x: float,
        y: float,
        juice_color: Tuple[int, int, int],
        count: int = 32,
        normal: Optional[Tuple[float, float]] = None,
    ):
        """Generates a burst of liquid droplets when a fruit is sliced."""
        for _ in range(count):
            if normal is not None and random.random() < 0.65:
                # Preferential spray perpendicular to slice cut
                sign = 1.0 if random.random() < 0.5 else -1.0
                base_angle = math.atan2(normal[1] * sign, normal[0] * sign)
                angle = base_angle + random.uniform(-0.5, 0.5)
            else:
                angle = random.uniform(0, 2 * math.pi)

            speed = random.uniform(140.0, 420.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed - 50.0  # slight upward bias
            radius = random.uniform(3.0, 8.0)
            lifetime = random.uniform(0.4, 0.9)

            # Tint variation
            r = min(255, max(0, juice_color[0] + random.randint(-20, 20)))
            g = min(255, max(0, juice_color[1] + random.randint(-20, 20)))
            b = min(255, max(0, juice_color[2] + random.randint(-20, 20)))

            p = Particle(
                x=x, y=y, vx=vx, vy=vy, color=(r, g, b), radius=radius, lifetime=lifetime, gravity=620.0
            )
            self.particles.append(p)

    def emit_slice_flash(self, p1: Tuple[float, float], p2: Tuple[float, float]):
        """Adds a blade slash cut line flash."""
        self.slice_flashes.append(SliceFlash(p1, p2))

    def emit_bomb_explosion(self, x: float, y: float):
        """Generates violent explosion effect with fire, smoke, and shockwave."""
        self.shockwaves.append(Shockwave(x=x, y=y, max_radius=240.0, lifetime=0.55))

        # Fire and sparks
        for _ in range(65):
            angle = random.uniform(0, 2 * math.pi)
            speed = random.uniform(150.0, 550.0)
            vx = math.cos(angle) * speed
            vy = math.sin(angle) * speed
            radius = random.uniform(4.0, 10.0)
            lifetime = random.uniform(0.4, 0.85)
            color = random.choice([
                (255, 235, 50),
                (255, 130, 25),
                (255, 50, 20),
                (230, 230, 240),
            ])
            self.particles.append(
                Particle(x=x, y=y, vx=vx, vy=vy, color=color, radius=radius, lifetime=lifetime, gravity=250.0)
            )

    def add_floating_text(
        self,
        text: str,
        x: float,
        y: float,
        color: Tuple[int, int, int],
        font: pygame.font.Font,
        lifetime: float = 0.9
    ):
        """Adds a floating text popup."""
        self.floating_texts.append(FloatingText(text, x, y, color, font, lifetime))

    def update(self, dt: float):
        """Updates all particles, flashes, and texts; removes dead ones."""
        self.slice_flashes = [f for f in self.slice_flashes if f.update(dt)]
        self.particles = [p for p in self.particles if p.update(dt)]
        self.floating_texts = [t for t in self.floating_texts if t.update(dt)]
        self.shockwaves = [s for s in self.shockwaves if s.update(dt)]

    def render(self, surface: pygame.Surface):
        """Renders slice flashes, shockwaves, particles, and floating texts."""
        for f in self.slice_flashes:
            f.render(surface)
        for s in self.shockwaves:
            s.render(surface)
        for p in self.particles:
            p.render(surface)
        for t in self.floating_texts:
            t.render(surface)

    def clear(self):
        """Clears all active particles."""
        self.slice_flashes.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.shockwaves.clear()
