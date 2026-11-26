"""
Central Fruit Ninja Game Engine.
Coordinates Pygame rendering, OpenCV camera capture, MediaPipe gesture detection,
physics simulation, collision resolution, particle animations, audio, and state machines.
"""

import os
import sys
import time
from typing import Optional, List, Dict, Any
import cv2
import pygame
import numpy as np

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    COLOR_BACKGROUND,
    CAMERA_INDEX,
    CAMERA_WIDTH,
    CAMERA_HEIGHT,
    CAMERA_MIRROR,
    HAND_LANDMARKER_MODEL_PATH,
    MODE_CLASSIC,
    MODE_TIME_CHALLENGE,
    MODE_PRACTICE,
)
from hand_tracking.detector import HandDetector
from hand_tracking.tracker import FingertipTracker
from game.fruit import Fruit, FruitHalf, Bomb
from game.fruit_spawner import FruitSpawner
from game.slicing import SliceManager, BladeRenderer
from game.particles import ParticleSystem
from game.scoring import ScoreManager
from game.sound import SoundManager
from game.ui import UIRenderer
from game.assets import AssetCache


# Game States
STATE_MENU = "MENU"
STATE_PLAYING = "PLAYING"
STATE_PAUSED = "PAUSED"
STATE_GAME_OVER = "GAME_OVER"


class GameEngine:
    """
    Main game lifecycle manager.
    """

    def __init__(self, headless: bool = False):
        self.headless = headless
        self.running = False
        self.state = STATE_MENU
        self.selected_mode = MODE_CLASSIC

        # Initialize Pygame Display
        pygame.init()
        if not self.headless:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
            pygame.display.set_caption(TITLE)
        else:
            self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        self.clock = pygame.time.Clock()
        AssetCache.initialize()

        # Initialize Subsystems
        self.particles = ParticleSystem()
        self.scores = ScoreManager(mode=self.selected_mode)
        self.sounds = SoundManager(enabled=not self.headless)
        self.spawner = FruitSpawner(mode=self.selected_mode)
        self.ui = UIRenderer()
        self.slice_mgr = SliceManager(self.particles, self.scores, self.sounds)
        self.blade_renderer = BladeRenderer()

        # Initialize Computer Vision & Hand Tracking
        self.tracker = FingertipTracker()
        self.detector = HandDetector(
            model_path=HAND_LANDMARKER_MODEL_PATH,
            target_width=SCREEN_WIDTH,
            target_height=SCREEN_HEIGHT,
        )

        # Webcam Setup
        self.camera: Optional[cv2.VideoCapture] = None
        self.camera_available = False
        self._init_camera()

        # Active Entities
        self.active_fruits: List[Fruit] = []
        self.active_bombs: List[Bomb] = []
        self.active_halves: List[FruitHalf] = []

        # Mouse fallback control (in case webcam is absent or user moves mouse)
        self.use_mouse_fallback = False
        self.prev_mouse_pos: Optional[Tuple[float, float]] = None
        self.current_landmarks: List[Tuple[int, int, float]] = []

    def _init_camera(self):
        """Attempts to open the webcam with fallback handling."""
        if self.headless:
            return

        # On Windows, try cv2.CAP_DSHOW first to avoid MSMF startup latency
        backends = [cv2.CAP_DSHOW, cv2.CAP_ANY] if sys.platform == "win32" else [cv2.CAP_ANY]
        for backend in backends:
            try:
                self.camera = cv2.VideoCapture(CAMERA_INDEX, backend)
                if self.camera and self.camera.isOpened():
                    self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
                    self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
                    ret, frame = self.camera.read()
                    if ret and frame is not None:
                        self.camera_available = True
                        print(f"[GameEngine] Webcam initialized successfully on index {CAMERA_INDEX} ({frame.shape[1]}x{frame.shape[0]}).")
                        return
                    self.camera.release()
            except Exception as e:
                print(f"[GameEngine] Webcam backend attempt ({backend}) note: {e}")

        print("[GameEngine] Notice: Webcam not detected or unavailable. Mouse fallback is enabled.")
        self.camera_available = False

    def start_game(self, mode: Optional[str] = None):
        """Starts a fresh game round."""
        if mode:
            self.selected_mode = mode
        self.scores.reset(mode=self.selected_mode)
        self.spawner.reset(mode=self.selected_mode)
        self.particles.clear()
        self.tracker.clear()
        self.active_fruits.clear()
        self.active_bombs.clear()
        self.active_halves.clear()
        self.state = STATE_PLAYING
        self.sounds.play("swoosh")

    def run(self):
        """Main game loop."""
        self.running = True

        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            # Cap dt to prevent physics tunneling after long stalls
            dt = min(dt, 0.05)

            self._handle_events()
            self._update(dt)
            self._render()

            if not self.headless:
                pygame.display.flip()

        self.cleanup()

    def _handle_events(self):
        """Processes keyboard and mouse events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
                        self.state = STATE_MENU
                    else:
                        self.running = False

                elif event.key == pygame.K_p:
                    if self.state == STATE_PLAYING:
                        self.state = STATE_PAUSED
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING

                elif event.key == pygame.K_r:
                    if self.state in (STATE_PLAYING, STATE_GAME_OVER, STATE_PAUSED):
                        self.start_game()

                elif event.key == pygame.K_c:
                    self.ui.toggle_pip()

                elif event.key == pygame.K_1 and self.state == STATE_MENU:
                    self.selected_mode = MODE_CLASSIC
                elif event.key == pygame.K_2 and self.state == STATE_MENU:
                    self.selected_mode = MODE_TIME_CHALLENGE
                elif event.key == pygame.K_3 and self.state == STATE_MENU:
                    self.selected_mode = MODE_PRACTICE

                elif event.key == pygame.K_SPACE:
                    if self.state == STATE_MENU:
                        self.start_game(self.selected_mode)
                    elif self.state == STATE_GAME_OVER:
                        self.start_game(self.selected_mode)
                    elif self.state == STATE_PAUSED:
                        self.state = STATE_PLAYING

            elif event.type == pygame.MOUSEMOTION:
                # If mouse moves significantly, activate mouse fallback
                if not self.camera_available or pygame.mouse.get_pressed()[0]:
                    self.use_mouse_fallback = True

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if self.state == STATE_GAME_OVER:
                    if self.ui.btn_game_over_play_again and self.ui.btn_game_over_play_again.collidepoint(mx, my):
                        self.start_game(self.selected_mode)
                    elif self.ui.btn_game_over_main_menu and self.ui.btn_game_over_main_menu.collidepoint(mx, my):
                        self.state = STATE_MENU
                elif self.state == STATE_PAUSED:
                    if self.ui.btn_pause_resume and self.ui.btn_pause_resume.collidepoint(mx, my):
                        self.state = STATE_PLAYING
                    elif self.ui.btn_pause_main_menu and self.ui.btn_pause_main_menu.collidepoint(mx, my):
                        self.state = STATE_MENU
                elif self.state == STATE_MENU:
                    modes = [MODE_CLASSIC, MODE_TIME_CHALLENGE, MODE_PRACTICE]
                    for idx, btn_rect in enumerate(self.ui.btn_menu_modes):
                        if btn_rect and btn_rect.collidepoint(mx, my):
                            self.selected_mode = modes[idx]
                            break
                    if self.ui.btn_menu_start and self.ui.btn_menu_start.collidepoint(mx, my):
                        self.start_game(self.selected_mode)

    def _update(self, dt: float):
        """Runs computer vision tracking, physics updates, and collisions."""
        # 1. Computer Vision Processing
        raw_finger_tip = None
        hand_detected = False

        if self.camera_available and self.camera:
            ret, frame = self.camera.read()
            if ret and frame is not None:
                detect_res = self.detector.process_frame(frame, mirror=CAMERA_MIRROR)
                hand_detected = detect_res["detected"]
                raw_finger_tip = detect_res["index_tip"]
                self.current_landmarks = detect_res.get("landmarks", []) if hand_detected else []
                self.ui.update_pip_frame(detect_res["annotated_frame"])
            else:
                self.current_landmarks = []
        else:
            self.current_landmarks = []

        # Fallback to mouse pointer if no hand or mouse dragged
        if raw_finger_tip is None and (self.use_mouse_fallback or not self.camera_available):
            mx, my = pygame.mouse.get_pos()
            # If mouse pressed or camera unavailable, treat mouse as fingertip
            if pygame.mouse.get_pressed()[0] or not self.camera_available:
                raw_finger_tip = (float(mx), float(my))
                hand_detected = True

        # Update fingertip tracker
        smoothed_pos, is_slicing = self.tracker.update(raw_finger_tip)

        # 2. State-Specific Updates
        if self.state == STATE_PLAYING:
            # Round timer update
            if self.scores.update_timer(dt):
                self.sounds.play("game_over")
                self.state = STATE_GAME_OVER

            if self.scores.is_game_over:
                self.sounds.play("game_over")
                self.state = STATE_GAME_OVER

            # Spawn new fruits / bombs
            new_spawns = self.spawner.update(dt, len(self.active_fruits))
            for entity in new_spawns:
                if isinstance(entity, Bomb):
                    self.active_bombs.append(entity)
                else:
                    self.active_fruits.append(entity)

            # Update active fruits
            surviving_fruits = []
            for fruit in self.active_fruits:
                fruit.update(dt)
                if fruit.is_offscreen(SCREEN_HEIGHT):
                    if not fruit.is_sliced:
                        self.scores.register_fruit_missed()
                else:
                    surviving_fruits.append(fruit)
            self.active_fruits = surviving_fruits

            # Update active bombs
            surviving_bombs = []
            for bomb in self.active_bombs:
                bomb.update(dt)
                if not bomb.is_offscreen(SCREEN_HEIGHT):
                    surviving_bombs.append(bomb)
            self.active_bombs = surviving_bombs

            # Update fruit halves
            surviving_halves = []
            for half in self.active_halves:
                half.update(dt)
                if not half.is_offscreen(SCREEN_HEIGHT):
                    surviving_halves.append(half)
            self.active_halves = surviving_halves

            # Blade Collision Resolution
            slice_segments = self.tracker.get_active_slice_segments()
            if slice_segments:
                self.sounds.play("swoosh", volume=0.3)
                self.active_fruits, self.active_bombs, self.active_halves = (
                    self.slice_mgr.process_slice_collisions(
                        slice_segment=slice_segments,
                        active_fruits=self.active_fruits,
                        active_bombs=self.active_bombs,
                        active_halves=self.active_halves,
                        font=self.ui.font_medium,
                    )
                )

        # Particle animations run in all states
        self.particles.update(dt)

    def _render(self):
        """Renders current scene to the screen."""
        # 1. Background
        self.screen.fill(COLOR_BACKGROUND)

        # 2. Active Game Entities (Fruits, Halves, Bombs)
        if self.state in (STATE_PLAYING, STATE_PAUSED, STATE_GAME_OVER):
            for half in self.active_halves:
                half.render(self.screen)
            for fruit in self.active_fruits:
                fruit.render(self.screen)
            for bomb in self.active_bombs:
                bomb.render(self.screen)

        # 3. Particle Systems (Juice droplets, shockwaves, floating scores)
        self.particles.render(self.screen)

        # 4. Virtual Blade Glowing Trail (Only cutting gestures on main game screen)
        trail_pts = self.tracker.get_trail_points()
        self.blade_renderer.render(
            self.screen,
            trail_points=trail_pts,
            is_slicing=self.tracker.is_slicing,
        )

        # 5. UI Layers based on Game State
        if self.state == STATE_PLAYING:
            self.ui.render_hud(
                self.screen,
                score_mgr=self.scores,
                is_hand_detected=self.tracker.is_hand_present,
            )
        elif self.state == STATE_MENU:
            self.ui.render_menu(
                self.screen,
                selected_mode=self.selected_mode,
                high_score=self.scores.high_score,
                is_hand_detected=self.tracker.is_hand_present,
            )
        elif self.state == STATE_PAUSED:
            self.ui.render_hud(self.screen, self.scores, self.tracker.is_hand_present)
            self.ui.render_pause(self.screen, is_hand_detected=self.tracker.is_hand_present)
        elif self.state == STATE_GAME_OVER:
            self.ui.render_hud(self.screen, self.scores, self.tracker.is_hand_present)
            summary = self.scores.get_summary()
            self.ui.render_game_over(self.screen, summary, is_hand_detected=self.tracker.is_hand_present)

    def cleanup(self):
        """Cleans up webcam and detector resources on shutdown."""
        if self.camera:
            try:
                self.camera.release()
            except Exception:
                pass
            self.camera = None
        if self.detector:
            self.detector.close()
        pygame.quit()
