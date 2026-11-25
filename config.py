"""
Configuration and Constants for AI Hand Gesture Controlled Fruit Ninja Game.
"""

import os
from dataclasses import dataclass
from typing import Tuple, Dict, Any

# Base Directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Model Path
HAND_LANDMARKER_MODEL_PATH = os.path.join(MODELS_DIR, "hand_landmarker.task")

# Display and Rendering
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "AI Fruit Ninja - Gesture Controlled Blade"

# Color Palette (Dark navy / deep charcoal arcade aesthetic)
COLOR_BACKGROUND = (15, 18, 32)
COLOR_PANEL_BG = (24, 30, 52, 200)
COLOR_TEXT_PRIMARY = (245, 248, 255)
COLOR_TEXT_SECONDARY = (160, 175, 205)
COLOR_ACCENT_CYAN = (0, 230, 255)
COLOR_ACCENT_GOLD = (255, 215, 0)
COLOR_ACCENT_RED = (255, 65, 85)
COLOR_ACCENT_GREEN = (45, 220, 110)
COLOR_ACCENT_PURPLE = (170, 75, 255)

# Blade and Trail Configuration
BLADE_TRAIL_LENGTH = 18
BLADE_MIN_SLICE_SPEED = 320.0  # Pixels per second required to count as slice
BLADE_MIN_SLICE_DISTANCE = 14.0  # Min pixels between frames for slice movement
BLADE_SMOOTHING_ALPHA = 0.65   # Exponential smoothing factor (0 = static, 1 = raw)
BLADE_COLOR_CORE = (255, 255, 255)
BLADE_COLOR_GLOW = (0, 225, 255)
BLADE_COLOR_OUTER = (0, 110, 255)
BLADE_WIDTH_BASE = 14.0

# Webcam and Computer Vision
CAMERA_INDEX = 0
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
CAMERA_MIRROR = True
PIP_WIDTH = 200
PIP_HEIGHT = 150
PIP_MARGIN = 20
DETECTION_CONFIDENCE = 0.55
TRACKING_CONFIDENCE = 0.55

# Gameplay Configuration
DEFAULT_LIVES = 3
DEFAULT_ROUND_TIME = 60  # seconds for Time Challenge mode
COMBO_TIME_WINDOW = 0.40  # Seconds window to chain slices for combo
COMBO_MIN_FRUITS = 2     # Minimum fruits to trigger combo bonus

# Fruit Properties Table
FRUITS_CONFIG: Dict[str, Dict[str, Any]] = {
    "watermelon": {
        "name": "Watermelon",
        "radius": 52,
        "points": 10,
        "color_outer": (35, 130, 45),
        "color_inner": (230, 40, 55),
        "juice_color": (230, 45, 60),
        "seed_color": (30, 30, 30),
        "mass": 1.4,
        "spawn_weight": 20,
    },
    "apple": {
        "name": "Apple",
        "radius": 42,
        "points": 10,
        "color_outer": (220, 30, 40),
        "color_inner": (255, 250, 220),
        "juice_color": (240, 60, 60),
        "seed_color": (70, 40, 20),
        "mass": 1.0,
        "spawn_weight": 22,
    },
    "orange": {
        "name": "Orange",
        "radius": 44,
        "points": 10,
        "color_outer": (255, 140, 0),
        "color_inner": (255, 175, 45),
        "juice_color": (255, 150, 10),
        "seed_color": (240, 230, 180),
        "mass": 1.1,
        "spawn_weight": 20,
    },
    "banana": {
        "name": "Banana",
        "radius": 40,
        "points": 15,
        "color_outer": (255, 225, 45),
        "color_inner": (255, 250, 210),
        "juice_color": (250, 235, 140),
        "seed_color": (90, 80, 50),
        "mass": 0.9,
        "spawn_weight": 16,
    },
    "pineapple": {
        "name": "Pineapple",
        "radius": 54,
        "points": 20,
        "color_outer": (205, 145, 30),
        "color_inner": (255, 235, 75),
        "juice_color": (255, 220, 50),
        "seed_color": (160, 110, 20),
        "mass": 1.5,
        "spawn_weight": 12,
    },
    "strawberry": {
        "name": "Strawberry",
        "radius": 34,
        "points": 15,
        "color_outer": (235, 30, 65),
        "color_inner": (255, 100, 120),
        "juice_color": (240, 40, 70),
        "seed_color": (255, 230, 130),
        "mass": 0.7,
        "spawn_weight": 18,
    },
    "grapes": {
        "name": "Grapes",
        "radius": 38,
        "points": 20,
        "color_outer": (125, 45, 185),
        "color_inner": (180, 120, 225),
        "juice_color": (145, 55, 200),
        "seed_color": (60, 20, 90),
        "mass": 0.8,
        "spawn_weight": 14,
    },
}

# Bomb Configuration
BOMB_CONFIG = {
    "radius": 45,
    "color_body": (40, 42, 48),
    "color_rim": (75, 80, 92),
    "fuse_spark_color": (255, 195, 30),
    "spawn_chance_base": 0.18,  # Chance per wave to include a bomb
    "spawn_chance_max": 0.35,
    "penalty_score": 15,
}

# Physics
GRAVITY = 720.0  # Pixels / second^2 (downward)
FRUIT_MIN_VY = -720.0  # Initial upward velocity
FRUIT_MAX_VY = -920.0
FRUIT_MIN_VX = -160.0  # Horizontal velocity
FRUIT_MAX_VX = 160.0
HALF_SPLIT_IMPULSE_X = 140.0
HALF_SPLIT_IMPULSE_Y = -80.0
HALF_ANGULAR_VELOCITY_MAX = 360.0  # Deg / sec

# Spawner Parameters
INITIAL_SPAWN_INTERVAL = 2.4  # seconds
MIN_SPAWN_INTERVAL = 0.95
DIFFICULTY_RAMP_DURATION = 90.0  # seconds to reach maximum difficulty
MAX_CONCURRENT_FRUITS = 8

# Game Modes
MODE_CLASSIC = "CLASSIC"
MODE_TIME_CHALLENGE = "TIME_CHALLENGE"
MODE_PRACTICE = "PRACTICE"
