"""
Asset loader and texture cache.
Loads PNG images for fruits, sliced halves, bombs, and backgrounds with automatic
procedural fallback if files are not present.
"""

import os
from typing import Dict, Optional, Tuple
import pygame

from config import ASSETS_DIR


class AssetCache:
    """
    Caches loaded pygame Surfaces to ensure optimal performance.
    """

    _instance = None
    _fruit_images: Dict[str, pygame.Surface] = {}
    _half1_images: Dict[str, pygame.Surface] = {}
    _half2_images: Dict[str, pygame.Surface] = {}
    _bomb_image: Optional[pygame.Surface] = None
    _bg_image: Optional[pygame.Surface] = None
    _initialized = False

    @classmethod
    def initialize(cls):
        """Loads and caches all sprite assets."""
        if cls._initialized:
            return

        fruits_dir = os.path.join(ASSETS_DIR, "fruits")
        sliced_dir = os.path.join(ASSETS_DIR, "sliced_fruits")
        bombs_dir = os.path.join(ASSETS_DIR, "bombs")
        bg_dir = os.path.join(ASSETS_DIR, "backgrounds")

        # Load whole fruit sprites
        if os.path.exists(fruits_dir):
            for fname in os.listdir(fruits_dir):
                if fname.endswith(".png"):
                    key = fname.replace(".png", "")
                    try:
                        surf = pygame.image.load(os.path.join(fruits_dir, fname)).convert_alpha()
                        cls._fruit_images[key] = surf
                    except Exception:
                        pass

        # Load sliced fruit halves
        if os.path.exists(sliced_dir):
            for fname in os.listdir(sliced_dir):
                if fname.endswith("_half_1.png"):
                    key = fname.replace("_half_1.png", "")
                    try:
                        surf = pygame.image.load(os.path.join(sliced_dir, fname)).convert_alpha()
                        cls._half1_images[key] = surf
                    except Exception:
                        pass
                elif fname.endswith("_half_2.png"):
                    key = fname.replace("_half_2.png", "")
                    try:
                        surf = pygame.image.load(os.path.join(sliced_dir, fname)).convert_alpha()
                        cls._half2_images[key] = surf
                    except Exception:
                        pass

        # Load Bomb
        bomb_file = os.path.join(bombs_dir, "bomb.png")
        if os.path.exists(bomb_file):
            try:
                cls._bomb_image = pygame.image.load(bomb_file).convert_alpha()
            except Exception:
                cls._bomb_image = None

        # Load Background
        bg_file = os.path.join(bg_dir, "arcade_bg.png")
        if os.path.exists(bg_file):
            try:
                cls._bg_image = pygame.image.load(bg_file).convert()
            except Exception:
                cls._bg_image = None

        cls._initialized = True

    @classmethod
    def get_fruit_surface(cls, fruit_type: str) -> Optional[pygame.Surface]:
        return cls._fruit_images.get(fruit_type)

    @classmethod
    def get_half_surface(cls, fruit_type: str, half_index: int) -> Optional[pygame.Surface]:
        if half_index == 1:
            return cls._half1_images.get(fruit_type)
        return cls._half2_images.get(fruit_type)

    @classmethod
    def get_bomb_surface(cls) -> Optional[pygame.Surface]:
        return cls._bomb_image

    @classmethod
    def get_background(cls) -> Optional[pygame.Surface]:
        return cls._bg_image
