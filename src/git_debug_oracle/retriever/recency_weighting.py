"""Recency weighting algorithm for boosting scores of recent commits.

Applies time-decay boost to retrieval scores based on commit age, prioritizing
recent changes while still considering older relevant code.
"""

from datetime import datetime, timezone


def apply_recency_weight(
    original_score: float,
    commit_timestamp: datetime,
    now: datetime,
    recent_window_days: int = 30,
) -> tuple[float, float]:
    """Apply recency weighting to vector similarity score.

    Boosts scores for chunks from recent commits and penalizes old commits.
    Formula: final_score = original_score * recency_boost

    Recency boost ranges:
    - Today (0 days old): 1.0x (no change)
    - Within recent_window: 1.0 - (days_old / window) * 0.3
    - Beyond window: 0.7x (30% penalty)

    Args:
        original_score: Vector similarity score from Qdrant (0-1)
        commit_timestamp: When commit was created (UTC)
        now: Current time for calculating age (UTC)
        recent_window_days: Days to consider "recent" (default: 30)

    Returns:
        Tuple of (final_score, recency_boost) where:
        - final_score = original_score * recency_boost
        - recency_boost is the multiplier applied (0-1)

    Example:
        >>> now = datetime(2026, 6, 12, tzinfo=timezone.utc)
        >>> today = datetime(2026, 6, 12, tzinfo=timezone.utc)
        >>> score, boost = apply_recency_weight(0.8, today, now)
        >>> boost
        1.0
        >>> old = datetime(2026, 5, 13, tzinfo=timezone.utc)
        >>> score, boost = apply_recency_weight(0.8, old, now)
        >>> boost
        0.7
    """
    # Handle zero original score
    if original_score == 0.0:
        return 0.0, 1.0

    # Calculate days since commit
    age = now - commit_timestamp
    days_old = age.total_seconds() / (24 * 3600)

    # Calculate recency boost
    if days_old <= recent_window_days:
        # Linear decay within window: 1.0 → 0.7
        recency_boost = 1.0 - (days_old / recent_window_days) * 0.3
    else:
        # Beyond window: constant 0.7 penalty
        recency_boost = 0.7

    # Ensure boost stays in [0, 1]
    recency_boost = max(0.0, min(1.0, recency_boost))

    # Final score is original × boost
    final_score = original_score * recency_boost

    return final_score, recency_boost
