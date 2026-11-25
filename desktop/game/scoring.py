"""
Scoring, Combo detection, Lives tracking, and Statistics management.
Includes local high score persistence and combo streak evaluation.
"""

import json
import os
import time
from typing import Dict, Any, Optional, List, Tuple

from config import (
    BASE_DIR,
    DEFAULT_LIVES,
    DEFAULT_ROUND_TIME,
    COMBO_TIME_WINDOW,
    COMBO_MIN_FRUITS,
    MODE_CLASSIC,
    MODE_TIME_CHALLENGE,
    MODE_PRACTICE,
)


class ScoreManager:
    """
    Manages score, combos, lives, game time, statistics, and high score persistence.
    """

    HIGH_SCORE_FILE = os.path.join(BASE_DIR, "highscore.json")

    def __init__(self, mode: str = MODE_CLASSIC):
        self.mode = mode
        self.score = 0
        self.lives = DEFAULT_LIVES
        self.time_remaining = float(DEFAULT_ROUND_TIME)
        self.is_game_over = False

        # Statistics
        self.total_fruits_sliced = 0
        self.total_fruits_missed = 0
        self.bomb_hits = 0
        self.highest_combo = 0
        self.total_combos_awarded = 0

        # Combo Tracking state
        # list of (timestamp, fruit_type, points)
        self.recent_slices: List[Tuple[float, str, int]] = []
        self.last_combo_event: Optional[Dict[str, Any]] = None

        # Load persisted best score
        self.high_score = self._load_high_score()

    def reset(self, mode: Optional[str] = None):
        """Resets game state for a new match."""
        if mode:
            self.mode = mode
        self.score = 0
        self.lives = DEFAULT_LIVES if self.mode == MODE_CLASSIC else 999
        self.time_remaining = float(DEFAULT_ROUND_TIME)
        self.is_game_over = False

        self.total_fruits_sliced = 0
        self.total_fruits_missed = 0
        self.bomb_hits = 0
        self.highest_combo = 0
        self.total_combos_awarded = 0
        self.recent_slices.clear()
        self.last_combo_event = None

    def register_fruit_slice(
        self,
        fruit_type: str,
        base_points: int,
        timestamp: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Registers a sliced fruit, computes base score and combo eligibility.
        Returns event summary dict.
        """
        if self.is_game_over:
            return {"points_awarded": 0, "combo_count": 0, "combo_bonus": 0}

        now = timestamp if timestamp is not None else time.time()
        self.score += base_points
        self.total_fruits_sliced += 1

        # Check and update high score immediately
        if self.score > self.high_score:
            self.high_score = self.score
            self._save_high_score()

        # Add to recent slices window
        self.recent_slices.append((now, fruit_type, base_points))

        # Filter slices that occurred within COMBO_TIME_WINDOW
        valid_recent = [s for s in self.recent_slices if (now - s[0]) <= COMBO_TIME_WINDOW]
        self.recent_slices = valid_recent

        combo_count = len(valid_recent)
        combo_bonus = 0

        if combo_count >= COMBO_MIN_FRUITS:
            # Combo bonus formula: combo_count * (combo_count - 1)
            combo_bonus = combo_count * 3
            self.score += combo_bonus
            self.total_combos_awarded += 1

            if combo_count > self.highest_combo:
                self.highest_combo = combo_count

            if self.score > self.high_score:
                self.high_score = self.score
                self._save_high_score()

            self.last_combo_event = {
                "count": combo_count,
                "bonus": combo_bonus,
                "timestamp": now,
            }

        return {
            "fruit_type": fruit_type,
            "base_points": base_points,
            "combo_count": combo_count if combo_bonus > 0 else 0,
            "combo_bonus": combo_bonus,
            "total_score": self.score,
        }

    def register_fruit_missed(self):
        """Called when an unsliced fruit falls off the screen bottom."""
        if self.is_game_over:
            return

        self.total_fruits_missed += 1

        if self.mode == MODE_CLASSIC:
            self.lives -= 1
            if self.lives <= 0:
                self.lives = 0
                self.is_game_over = True

    def register_bomb_hit(self, penalty: int = 15):
        """Called when a bomb is sliced."""
        if self.is_game_over:
            return

        self.bomb_hits += 1

        if self.mode == MODE_CLASSIC:
            # Instant game over or loss of all remaining lives in Classic mode
            self.lives = 0
            self.is_game_over = True
        elif self.mode == MODE_TIME_CHALLENGE:
            # Score penalty and time penalty
            self.score = max(0, self.score - penalty)
            self.time_remaining = max(0.0, self.time_remaining - 3.0)

    def update_timer(self, dt: float) -> bool:
        """
        Decrements round timer in Time Challenge mode.
        Returns True if round time has expired.
        """
        if self.mode == MODE_TIME_CHALLENGE and not self.is_game_over:
            self.time_remaining -= dt
            if self.time_remaining <= 0.0:
                self.time_remaining = 0.0
                self.is_game_over = True
                return True
        return False

    def get_accuracy_percentage(self) -> float:
        """Calculates player accuracy percentage [0.0 - 100.0%]."""
        total = self.total_fruits_sliced + self.total_fruits_missed
        if total == 0:
            return 100.0
        return round((self.total_fruits_sliced / total) * 100.0, 1)

    def get_summary(self) -> Dict[str, Any]:
        """Returns full statistical report of current/ended match."""
        return {
            "mode": self.mode,
            "final_score": self.score,
            "high_score": self.high_score,
            "fruits_sliced": self.total_fruits_sliced,
            "fruits_missed": self.total_fruits_missed,
            "bomb_hits": self.bomb_hits,
            "highest_combo": self.highest_combo,
            "combos_awarded": self.total_combos_awarded,
            "accuracy_pct": self.get_accuracy_percentage(),
            "lives_left": self.lives,
            "time_remaining": round(self.time_remaining, 1),
            "is_game_over": self.is_game_over,
        }

    def _load_high_score(self) -> int:
        """Loads high score from disk if file exists."""
        if os.path.exists(self.HIGH_SCORE_FILE):
            try:
                with open(self.HIGH_SCORE_FILE, "r") as f:
                    data = json.load(f)
                    return int(data.get("high_score", 0))
            except Exception:
                pass
        return 0

    def _save_high_score(self):
        """Persists high score to disk."""
        try:
            with open(self.HIGH_SCORE_FILE, "w") as f:
                json.dump({"high_score": self.high_score, "last_updated": time.time()}, f)
        except Exception:
            pass
