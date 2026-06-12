"""Tests for recency weighting algorithm."""

import pytest
from datetime import datetime, timedelta, timezone

from git_debug_oracle.retriever.recency_weighting import apply_recency_weight


class TestRecencyWeighting:
    """Recency weighting boosts scores for recent commits."""

    def test_weight_today_commit(self) -> None:
        """Today's commit gets ~1.0x boost."""
        now = datetime.now(timezone.utc)
        score, boost = apply_recency_weight(0.8, now, now, recent_window_days=30)
        assert 0.79 <= score <= 0.81  # 0.8 * 1.0 boost
        assert 0.99 <= boost <= 1.01

    def test_weight_30_days_old(self) -> None:
        """30 days old gets 0.7x (30% penalty)."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=30)
        score, boost = apply_recency_weight(0.8, old, now, recent_window_days=30)
        assert 0.55 <= score <= 0.57  # 0.8 * 0.7 boost
        assert 0.69 <= boost <= 0.71

    def test_weight_15_days_old(self) -> None:
        """15 days old gets ~0.85x."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=15)
        score, boost = apply_recency_weight(0.8, old, now, recent_window_days=30)
        # Boost: 1.0 - (15/30) * 0.3 = 0.85, score = 0.8 * 0.85 = 0.68
        assert 0.67 <= score <= 0.69

    def test_weight_older_than_window(self) -> None:
        """Beyond recent window gets 0.7x penalty."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=100)
        score, boost = apply_recency_weight(0.8, old, now, recent_window_days=30)
        assert 0.55 <= score <= 0.57  # 0.8 * 0.7 boost

    def test_weight_zero_original_score(self) -> None:
        """Zero original score stays zero."""
        now = datetime.now(timezone.utc)
        score, boost = apply_recency_weight(0.0, now, now, recent_window_days=30)
        assert score == 0.0
        assert boost == 1.0

    def test_weight_perfect_original_score(self) -> None:
        """Perfect score of 1.0 with today's commit."""
        now = datetime.now(timezone.utc)
        score, boost = apply_recency_weight(1.0, now, now, recent_window_days=30)
        assert 0.99 <= score <= 1.01

    def test_boost_factor_returned(self) -> None:
        """Function returns both score and boost factor."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=10)
        score, boost = apply_recency_weight(0.8, old, now, recent_window_days=30)
        assert isinstance(score, float)
        assert isinstance(boost, float)
        assert score == pytest.approx(0.8 * boost)

    def test_custom_window(self) -> None:
        """Custom recent_window_days respected."""
        now = datetime.now(timezone.utc)
        old = now - timedelta(days=10)
        score1, _ = apply_recency_weight(0.8, old, now, recent_window_days=30)
        score2, _ = apply_recency_weight(0.8, old, now, recent_window_days=10)
        # Same commit, different windows → different boosts
        assert score1 > score2
