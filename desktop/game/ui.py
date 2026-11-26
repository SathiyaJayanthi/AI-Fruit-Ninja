"""
User Interface, Heads-Up Display (HUD), Webcam PIP Overlay, Menus,
and Game-Over Statistics Screen.
"""

import math
import time
from typing import Optional, Dict, Any, Tuple
import pygame
import cv2
import numpy as np

from config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BACKGROUND,
    COLOR_PANEL_BG,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    COLOR_ACCENT_CYAN,
    COLOR_ACCENT_GOLD,
    COLOR_ACCENT_RED,
    COLOR_ACCENT_GREEN,
    PIP_WIDTH,
    PIP_HEIGHT,
    PIP_MARGIN,
    MODE_CLASSIC,
    MODE_TIME_CHALLENGE,
    MODE_PRACTICE,
)
from game.scoring import ScoreManager


class UIRenderer:
    """
    Renders all 2D UI elements including in-game HUD, floating PIP camera feed,
    menus, and post-game statistics card.
    """

    def __init__(self):
        pygame.font.init()
        # High quality font hierarchy
        self.font_title = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 54, bold=True)
        self.font_subtitle = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 22, bold=False)
        self.font_large = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 36, bold=True)
        self.font_medium = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 22, bold=True)
        self.font_small = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 16, bold=False)
        self.font_digits = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 42, bold=True)

        self.pip_surface: Optional[pygame.Surface] = None
        self.show_pip = True

        # Interactive Button Rectangles for Click / Tap Detection
        self.btn_game_over_play_again: Optional[pygame.Rect] = None
        self.btn_game_over_main_menu: Optional[pygame.Rect] = None
        self.btn_pause_resume: Optional[pygame.Rect] = None
        self.btn_pause_main_menu: Optional[pygame.Rect] = None
        self.btn_menu_modes: List[pygame.Rect] = []
        self.btn_menu_start: Optional[pygame.Rect] = None

    def toggle_pip(self):
        """Toggles webcam PIP display."""
        self.show_pip = not self.show_pip

    def update_pip_frame(self, bgr_frame: Optional[np.ndarray]):
        """Converts annotated OpenCV BGR frame into a Pygame surface for PIP preview."""
        if bgr_frame is None or not self.show_pip:
            return

        h, w = bgr_frame.shape[:2]
        # Resize to PIP dimensions
        resized = cv2.resize(bgr_frame, (PIP_WIDTH, PIP_HEIGHT), interpolation=cv2.INTER_LINEAR)
        rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        # Convert to Pygame Surface
        self.pip_surface = pygame.surfarray.make_surface(np.transpose(rgb, (1, 0, 2)))

    def render_hud(
        self,
        surface: pygame.Surface,
        score_mgr: ScoreManager,
        is_hand_detected: bool,
    ):
        """Renders active gameplay HUD: Score, Lives/Timer, Mode, and PIP."""
        # 1. Score Panel (Top Left)
        score_card_rect = pygame.Rect(25, 20, 240, 75)
        self._draw_rounded_panel(surface, score_card_rect, COLOR_PANEL_BG)

        score_label = self.font_small.render("SCORE", True, COLOR_TEXT_SECONDARY)
        surface.blit(score_label, (40, 28))

        score_val = self.font_digits.render(str(score_mgr.score), True, COLOR_ACCENT_CYAN)
        surface.blit(score_val, (40, 44))

        best_label = self.font_small.render(f"BEST: {score_mgr.high_score}", True, COLOR_ACCENT_GOLD)
        surface.blit(best_label, (155, 30))

        # 2. Mode / Objectives Panel (Top Center)
        mode_rect = pygame.Rect(SCREEN_WIDTH // 2 - 120, 20, 240, 44)
        self._draw_rounded_panel(surface, mode_rect, COLOR_PANEL_BG)

        mode_text = f"MODE: {score_mgr.mode}"
        mode_surf = self.font_small.render(mode_text, True, COLOR_TEXT_PRIMARY)
        surface.blit(mode_surf, mode_surf.get_rect(center=mode_rect.center))

        # 3. Lives or Timer (Top Right, next to PIP)
        if score_mgr.mode == MODE_CLASSIC:
            lives_rect = pygame.Rect(SCREEN_WIDTH - PIP_WIDTH - 210, 20, 180, 50)
            self._draw_rounded_panel(surface, lives_rect, COLOR_PANEL_BG)

            lives_label = self.font_small.render("LIVES:", True, COLOR_TEXT_SECONDARY)
            surface.blit(lives_label, (lives_rect.x + 15, lives_rect.y + 16))

            # Render 3 ninja X marks
            for i in range(3):
                lx = lives_rect.x + 85 + i * 28
                ly = lives_rect.y + 25
                if i < score_mgr.lives:
                    # Active life (Bright red cross mark)
                    pygame.draw.line(surface, COLOR_ACCENT_RED, (lx - 8, ly - 8), (lx + 8, ly + 8), 4)
                    pygame.draw.line(surface, COLOR_ACCENT_RED, (lx + 8, ly - 8), (lx - 8, ly + 8), 4)
                else:
                    # Lost life (Dim gray cross mark)
                    pygame.draw.line(surface, (70, 75, 90), (lx - 8, ly - 8), (lx + 8, ly + 8), 3)
                    pygame.draw.line(surface, (70, 75, 90), (lx + 8, ly - 8), (lx - 8, ly + 8), 3)

        elif score_mgr.mode == MODE_TIME_CHALLENGE:
            timer_rect = pygame.Rect(SCREEN_WIDTH - PIP_WIDTH - 210, 20, 180, 50)
            self._draw_rounded_panel(surface, timer_rect, COLOR_PANEL_BG)

            time_val = max(0, int(score_mgr.time_remaining))
            time_color = COLOR_ACCENT_RED if time_val <= 10 else COLOR_ACCENT_GREEN
            t_surf = self.font_large.render(f"00:{time_val:02d}", True, time_color)
            surface.blit(t_surf, t_surf.get_rect(center=timer_rect.center))

        # 4. Webcam PIP Preview (Top Right)
        if self.show_pip and self.pip_surface is not None:
            pip_x = SCREEN_WIDTH - PIP_WIDTH - PIP_MARGIN
            pip_y = PIP_MARGIN
            pip_rect = pygame.Rect(pip_x, pip_y, PIP_WIDTH, PIP_HEIGHT)

            # Draw camera frame
            surface.blit(self.pip_surface, (pip_x, pip_y))

            # Glowing border around PIP (Green if hand detected, cyan default)
            border_color = COLOR_ACCENT_GREEN if is_hand_detected else (60, 70, 95)
            pygame.draw.rect(surface, border_color, pip_rect, 3, border_radius=6)

            # Hand status badge
            badge_rect = pygame.Rect(pip_x, pip_y + PIP_HEIGHT - 24, PIP_WIDTH, 24)
            s = pygame.Surface((PIP_WIDTH, 24), pygame.SRCALPHA)
            s.fill((15, 18, 30, 200))
            surface.blit(s, badge_rect.topleft)

            status_msg = "● HAND DETECTED" if is_hand_detected else "○ SHOW HAND"
            status_color = COLOR_ACCENT_GREEN if is_hand_detected else (240, 180, 50)
            status_surf = self.font_small.render(status_msg, True, status_color)
            surface.blit(status_surf, status_surf.get_rect(center=badge_rect.center))

        # 5. Bottom Controls Bar
        hint_text = "[C] Toggle Camera  |  [P] Pause  |  [R] Restart  |  [ESC] Menu"
        hint_surf = self.font_small.render(hint_text, True, (120, 130, 160))
        surface.blit(hint_surf, hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 22)))

    def render_menu(
        self,
        surface: pygame.Surface,
        selected_mode: str,
        high_score: int,
        is_hand_detected: bool,
    ):
        """Renders interactive Main Menu."""
        # Backdrop
        surface.fill(COLOR_BACKGROUND)

        # Title
        title_surf = self.font_title.render("AI FRUIT NINJA", True, COLOR_ACCENT_CYAN)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 130)))

        subtitle = self.font_subtitle.render(
            "MediaPipe AI Hand Gesture Controlled Slicing Game", True, COLOR_TEXT_SECONDARY
        )
        surface.blit(subtitle, subtitle.get_rect(center=(SCREEN_WIDTH // 2, 180)))

        # High score banner
        hs_text = self.font_medium.render(f"★ ALL-TIME HIGH SCORE: {high_score} ★", True, COLOR_ACCENT_GOLD)
        surface.blit(hs_text, hs_text.get_rect(center=(SCREEN_WIDTH // 2, 230)))

        # Mode Selection Buttons
        modes = [
            (MODE_CLASSIC, "CLASSIC MODE", "3 Lives, Bombs, Pure Fruit Ninja"),
            (MODE_TIME_CHALLENGE, "TIME CHALLENGE", "60 Seconds Frenzy, Maximize Score"),
            (MODE_PRACTICE, "PRACTICE MODE", "No Bombs, Infinite Zen, Gesture Training"),
        ]

        start_y = 280
        self.btn_menu_modes = []
        for i, (m_id, m_name, m_desc) in enumerate(modes):
            is_selected = (m_id == selected_mode)
            btn_rect = pygame.Rect(SCREEN_WIDTH // 2 - 280, start_y + i * 85, 560, 68)
            self.btn_menu_modes.append(btn_rect)

            bg_color = (35, 45, 80) if is_selected else (22, 26, 44)
            border_color = COLOR_ACCENT_CYAN if is_selected else (60, 70, 95)
            self._draw_rounded_panel(surface, btn_rect, bg_color, border_color=border_color, border_width=3 if is_selected else 1)

            num_str = f"[{i + 1}] "
            name_color = COLOR_ACCENT_CYAN if is_selected else COLOR_TEXT_PRIMARY
            name_surf = self.font_medium.render(num_str + m_name, True, name_color)
            surface.blit(name_surf, (btn_rect.x + 25, btn_rect.y + 12))

            desc_surf = self.font_small.render(m_desc, True, COLOR_TEXT_SECONDARY)
            surface.blit(desc_surf, (btn_rect.x + 25, btn_rect.y + 38))

        # Clickable START GAME Button
        prompt_y = start_y + len(modes) * 85 + 20
        self.btn_menu_start = pygame.Rect(SCREEN_WIDTH // 2 - 140, prompt_y - 6, 280, 48)
        self._draw_rounded_panel(
            surface,
            self.btn_menu_start,
            bg_color=(0, 160, 220),
            border_color=(255, 255, 255),
            border_width=2,
            border_radius=12,
        )
        start_txt = self.font_large.render("START GAME", True, (255, 255, 255))
        surface.blit(start_txt, start_txt.get_rect(center=self.btn_menu_start.center))

        # Hand Detection Calibration Indicator
        cam_hint = (
            "✔ Camera Active: Hand Tracked - Ready to Slice!"
            if is_hand_detected
            else "Camera Active: Hold your index finger up to webcam"
        )
        cam_color = COLOR_ACCENT_GREEN if is_hand_detected else COLOR_ACCENT_GOLD
        cam_surf = self.font_small.render(cam_hint, True, cam_color)
        surface.blit(cam_surf, cam_surf.get_rect(center=(SCREEN_WIDTH // 2, prompt_y + 60)))

    def render_pause(self, surface: pygame.Surface):
        """Renders Pause Menu overlay with interactive clickable buttons."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 25, 200))
        surface.blit(overlay, (0, 0))

        title = self.font_title.render("GAME PAUSED", True, COLOR_TEXT_PRIMARY)
        surface.blit(title, title.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 70)))

        # Interactive Buttons
        self.btn_pause_resume = pygame.Rect(SCREEN_WIDTH // 2 - 210, SCREEN_HEIGHT // 2 + 10, 190, 46)
        self.btn_pause_main_menu = pygame.Rect(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 2 + 10, 190, 46)

        self._draw_rounded_panel(surface, self.btn_pause_resume, (0, 160, 220), border_color=(255, 255, 255), border_width=2, border_radius=10)
        res_txt = self.font_medium.render("RESUME [P]", True, (255, 255, 255))
        surface.blit(res_txt, res_txt.get_rect(center=self.btn_pause_resume.center))

        self._draw_rounded_panel(surface, self.btn_pause_main_menu, (35, 45, 75), border_color=COLOR_ACCENT_CYAN, border_width=2, border_radius=10)
        menu_txt = self.font_medium.render("MAIN MENU [ESC]", True, COLOR_ACCENT_CYAN)
        surface.blit(menu_txt, menu_txt.get_rect(center=self.btn_pause_main_menu.center))

    def render_game_over(
        self,
        surface: pygame.Surface,
        summary: Dict[str, Any],
    ):
        """Renders Game Over statistics card with interactive clickable buttons."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 14, 25, 225))
        surface.blit(overlay, (0, 0))

        card_rect = pygame.Rect(SCREEN_WIDTH // 2 - 270, 70, 540, 560)
        self._draw_rounded_panel(surface, card_rect, (24, 30, 52), border_color=COLOR_ACCENT_CYAN, border_width=3)

        # Title
        title_text = "TIME'S UP!" if summary["mode"] == MODE_TIME_CHALLENGE and summary["time_remaining"] <= 0 else "GAME OVER"
        title_surf = self.font_title.render(title_text, True, COLOR_ACCENT_RED)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 120)))

        # Final Score
        score_val = summary["final_score"]
        score_surf = self.font_digits.render(f"FINAL SCORE: {score_val}", True, COLOR_ACCENT_CYAN)
        surface.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, 180)))

        if score_val >= summary["high_score"] and score_val > 0:
            hs_banner = self.font_medium.render("★ NEW HIGH SCORE! ★", True, COLOR_ACCENT_GOLD)
            surface.blit(hs_banner, hs_banner.get_rect(center=(SCREEN_WIDTH // 2, 220)))

        # Detailed Statistics Grid
        stats = [
            ("Game Mode", summary["mode"]),
            ("Fruits Sliced", str(summary["fruits_sliced"])),
            ("Fruits Missed", str(summary["fruits_missed"])),
            ("Bomb Hits", str(summary["bomb_hits"])),
            ("Highest Combo", f"{summary['highest_combo']}x"),
            ("Accuracy", f"{summary['accuracy_pct']}%"),
        ]

        sy = 250
        for label, val in stats:
            lbl_surf = self.font_medium.render(label, True, COLOR_TEXT_SECONDARY)
            val_surf = self.font_medium.render(val, True, COLOR_TEXT_PRIMARY)
            surface.blit(lbl_surf, (card_rect.x + 50, sy))
            surface.blit(val_surf, (card_rect.right - 50 - val_surf.get_width(), sy))
            sy += 36

        # Interactive Buttons: PLAY AGAIN & MAIN MENU
        self.btn_game_over_play_again = pygame.Rect(card_rect.centerx - 220, card_rect.bottom - 68, 200, 48)
        self.btn_game_over_main_menu = pygame.Rect(card_rect.centerx + 20, card_rect.bottom - 68, 200, 48)

        self._draw_rounded_panel(surface, self.btn_game_over_play_again, (0, 160, 220), border_color=(255, 255, 255), border_width=2, border_radius=10)
        again_txt = self.font_medium.render("PLAY AGAIN [R]", True, (255, 255, 255))
        surface.blit(again_txt, again_txt.get_rect(center=self.btn_game_over_play_again.center))

        self._draw_rounded_panel(surface, self.btn_game_over_main_menu, (35, 45, 75), border_color=COLOR_ACCENT_CYAN, border_width=2, border_radius=10)
        menu_txt = self.font_medium.render("MAIN MENU [ESC]", True, COLOR_ACCENT_CYAN)
        surface.blit(menu_txt, menu_txt.get_rect(center=self.btn_game_over_main_menu.center))

    def _draw_rounded_panel(
        self,
        surface: pygame.Surface,
        rect: pygame.Rect,
        bg_color: Tuple[int, ...],
        border_color: Optional[Tuple[int, ...]] = None,
        border_width: int = 1,
        border_radius: int = 10,
    ):
        """Draws a smooth rounded rectangle panel with optional border."""
        if len(bg_color) == 4:
            s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(s, bg_color, (0, 0, rect.width, rect.height), border_radius=border_radius)
            surface.blit(s, rect.topleft)
        else:
            pygame.draw.rect(surface, bg_color, rect, border_radius=border_radius)

        if border_color:
            pygame.draw.rect(surface, border_color, rect, border_width, border_radius=border_radius)
