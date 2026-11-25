"""
Dynamic fruit and bomb spawner.
Manages launch angles, velocities, difficulty progression, and wave patterns.
"""

import math
import random
import time
from typing import List, Optional, Tuple, Dict, Any

from config import (
    FRUITS_CONFIG,
    BOMB_CONFIG,
    INITIAL_SPAWN_INTERVAL,
    MIN_SPAWN_INTERVAL,
    DIFFICULTY_RAMP_DURATION,
    MAX_CONCURRENT_FRUITS,
    FRUIT_MIN_VX,
    FRUIT_MAX_VX,
    FRUIT_MIN_VY,
    FRUIT_MAX_VY,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    MODE_CLASSIC,
    MODE_TIME_CHALLENGE,
    MODE_PRACTICE,
)
from game.fruit import Fruit, Bomb


class FruitSpawner:
    """
    Handles procedural spawning of fruits and bombs based on elapsed game time,
    wave dynamics, and selected game mode.
    """

    def __init__(self, mode: str = MODE_CLASSIC):
        self.mode = mode
        self.fruit_keys = list(FRUITS_CONFIG.keys())
        self.fruit_weights = [FRUITS_CONFIG[k]["spawn_weight"] for k in self.fruit_keys]

        self.spawn_timer = 0.0
        self.next_interval = INITIAL_SPAWN_INTERVAL
        self.elapsed_time = 0.0

    def reset(self, mode: Optional[str] = None):
        """Resets spawner state for a fresh game round."""
        if mode:
            self.mode = mode
        self.spawn_timer = 0.0
        self.next_interval = INITIAL_SPAWN_INTERVAL
        self.elapsed_time = 0.0

    def update(
        self,
        dt: float,
        current_active_fruits_count: int,
    ) -> List[Any]:
        """
        Updates spawner timer and returns a list of newly spawned entities (Fruit / Bomb).
        """
        self.elapsed_time += dt
        self.spawn_timer += dt

        # Calculate dynamic difficulty factor [0.0 to 1.0]
        progress = min(1.0, self.elapsed_time / DIFFICULTY_RAMP_DURATION)

        # Current spawn interval shortens over time
        current_target_interval = (
            INITIAL_SPAWN_INTERVAL - progress * (INITIAL_SPAWN_INTERVAL - MIN_SPAWN_INTERVAL)
        )

        spawned_entities: List[Any] = []

        if self.spawn_timer >= self.next_interval:
            self.spawn_timer = 0.0
            # Add slight randomized jitter (+/- 15%) to spawn rhythm
            self.next_interval = current_target_interval * random.uniform(0.85, 1.15)

            # Check capacity
            if current_active_fruits_count >= MAX_CONCURRENT_FRUITS:
                return []

            # Determine wave size (1 to 4 items depending on difficulty)
            if progress < 0.25:
                wave_size = random.choices([1, 2], weights=[70, 30])[0]
            elif progress < 0.65:
                wave_size = random.choices([1, 2, 3], weights=[35, 45, 20])[0]
            else:
                wave_size = random.choices([2, 3, 4], weights=[30, 45, 25])[0]

            # Clamp wave size so we don't exceed max fruits
            allowed = max(1, MAX_CONCURRENT_FRUITS - current_active_fruits_count)
            wave_size = min(wave_size, allowed)

            # Decide if a bomb spawns in this wave (Classic mode only)
            spawn_bomb = False
            if self.mode == MODE_CLASSIC:
                bomb_chance = (
                    BOMB_CONFIG["spawn_chance_base"]
                    + progress * (BOMB_CONFIG["spawn_chance_max"] - BOMB_CONFIG["spawn_chance_base"])
                )
                if random.random() < bomb_chance:
                    spawn_bomb = True

            for i in range(wave_size):
                # Distribute spawn locations across bottom screen
                # Margin of 120px from screen edges
                min_x = 120
                max_x = SCREEN_WIDTH - 120
                start_x = random.uniform(min_x, max_x)
                start_y = SCREEN_HEIGHT + random.uniform(20, 60)

                # Velocity trajectory calculation
                # Bias vx toward screen center so fruits arc across play area
                center_offset = (SCREEN_WIDTH / 2.0) - start_x
                vx_bias = center_offset * 0.4
                vx = vx_bias + random.uniform(FRUIT_MIN_VX, FRUIT_MAX_VX)

                # Upward launch velocity with slight variation
                vy = random.uniform(FRUIT_MIN_VY, FRUIT_MAX_VY)

                # If this slot is for the bomb
                if spawn_bomb and i == 0:
                    bomb = Bomb(start_x=start_x, start_y=start_y, vx=vx * 0.85, vy=vy * 0.95)
                    spawned_entities.append(bomb)
                    spawn_bomb = False  # Only 1 bomb per wave
                else:
                    fruit_type = random.choices(self.fruit_keys, weights=self.fruit_weights)[0]
                    fruit = Fruit(
                        fruit_type=fruit_type,
                        start_x=start_x,
                        start_y=start_y,
                        vx=vx,
                        vy=vy,
                    )
                    spawned_entities.append(fruit)

        return spawned_entities
