"""
Unit tests for scoring, combo evaluation, lives tracking, and statistics.
"""

import time
import pytest
from config import MODE_CLASSIC, MODE_TIME_CHALLENGE, MODE_PRACTICE
from game.scoring import ScoreManager


class TestScoreManager:

    def test_single_slice_score(self):
        """Standard slice awards base points without combo bonus."""
        sm = ScoreManager(mode=MODE_CLASSIC)
        res = sm.register_fruit_slice("apple", 10, timestamp=1.0)
        assert sm.score == 10
        assert sm.total_fruits_sliced == 1
        assert res["combo_bonus"] == 0

    def test_combo_bonus_multi_slice(self):
        """Two or more slices within window trigger combo awards."""
        sm = ScoreManager(mode=MODE_CLASSIC)
        t = 100.0
        # Slice 1
        sm.register_fruit_slice("apple", 10, timestamp=t)
        # Slice 2 (0.15s later - inside 0.40s window)
        res2 = sm.register_fruit_slice("banana", 15, timestamp=t + 0.15)

        assert res2["combo_count"] == 2
        assert res2["combo_bonus"] == 6  # 2 * 3 = 6
        assert sm.score == 10 + 15 + 6
        assert sm.highest_combo == 2

    def test_combo_window_expiration(self):
        """Slices separated by more than COMBO_TIME_WINDOW do not trigger combo."""
        sm = ScoreManager(mode=MODE_CLASSIC)
        t = 100.0
        sm.register_fruit_slice("apple", 10, timestamp=t)
        # Slice 2 (0.60s later - outside 0.40s window)
        res2 = sm.register_fruit_slice("banana", 15, timestamp=t + 0.60)

        assert res2["combo_count"] == 0
        assert res2["combo_bonus"] == 0
        assert sm.score == 10 + 15

    def test_lives_deduction_in_classic(self):
        """Missed fruit deducts lives until game over in Classic mode."""
        sm = ScoreManager(mode=MODE_CLASSIC)
        assert sm.lives == 3
        sm.register_fruit_missed()
        assert sm.lives == 2
        sm.register_fruit_missed()
        assert sm.lives == 1
        assert sm.is_game_over is False
        sm.register_fruit_missed()
        assert sm.lives == 0
        assert sm.is_game_over is True

    def test_practice_mode_no_life_loss(self):
        """Practice mode does not lose lives on missed fruit."""
        sm = ScoreManager(mode=MODE_PRACTICE)
        sm.register_fruit_missed()
        sm.register_fruit_missed()
        assert sm.is_game_over is False
        assert sm.total_fruits_missed == 2

    def test_bomb_hit_in_classic(self):
        """Bomb hit in Classic mode ends the game immediately."""
        sm = ScoreManager(mode=MODE_CLASSIC)
        sm.register_bomb_hit()
        assert sm.lives == 0
        assert sm.is_game_over is True
        assert sm.bomb_hits == 1

    def test_bomb_hit_in_time_challenge(self):
        """Bomb hit in Time Challenge deducts score and time but does not end game."""
        sm = ScoreManager(mode=MODE_TIME_CHALLENGE)
        sm.score = 50
        sm.time_remaining = 40.0
        sm.register_bomb_hit(penalty=15)
        assert sm.score == 35
        assert sm.time_remaining == 37.0
        assert sm.is_game_over is False

    def test_time_challenge_countdown(self):
        """Timer countdown triggers game over at 0 seconds."""
        sm = ScoreManager(mode=MODE_TIME_CHALLENGE)
        sm.time_remaining = 1.0
        expired = sm.update_timer(1.2)
        assert expired is True
        assert sm.is_game_over is True
        assert sm.time_remaining == 0.0

    def test_accuracy_calculation(self):
        """Verifies accuracy percentage formula."""
        sm = ScoreManager(mode=MODE_CLASSIC)
        sm.total_fruits_sliced = 8
        sm.total_fruits_missed = 2
        # 8 / (8 + 2) = 80.0%
        assert sm.get_accuracy_percentage() == 80.0
