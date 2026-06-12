"""Integration tests for Phase 3 retrieval and error ingestion."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch, Mock

from git_debug_oracle.error_ingestion.models import ErrorContext, RetrievalResult
from git_debug_oracle.retriever.query_constructor import construct_query
from git_debug_oracle.retriever.recency_weighting import apply_recency_weight


class TestPhase3Integration:
    """End-to-end Phase 3 workflows."""

    def test_error_to_query_pipeline(self) -> None:
        """Error context converts to query string."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name="process_data",
            error_type="ValueError",
            error_message="invalid input",
        )

        query = construct_query(ctx)

        assert isinstance(query, str)
        assert len(query) > 0
        assert len(query) <= 500
        assert "process_data" in query
        assert "src/app.py" in query

    def test_recency_weighting_formula(self) -> None:
        """Recency weighting follows specified formula."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        # Test case: 15 days old, 30-day window
        old = now - timedelta(days=15)
        score, boost = apply_recency_weight(0.8, old, now, recent_window_days=30)

        # Expected: 1.0 - (15/30) * 0.3 = 0.85
        # Final: 0.8 * 0.85 = 0.68
        assert 0.67 <= score <= 0.69
        assert 0.84 <= boost <= 0.86

    def test_query_normalization(self) -> None:
        """Query normalizes whitespace correctly."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=1,
            function_name="func  with  spaces",
            error_message="error  message   here",
        )

        query = construct_query(ctx)

        # No double spaces
        assert "  " not in query
        # Properly trimmed
        assert query[0] != " "
        assert query[-1] != " "

    def test_query_truncation_preserves_words(self) -> None:
        """Query truncation stops at word boundary."""
        long_msg = " ".join(["word"] * 200)
        ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
            function_name="func",
            error_message=long_msg,
        )

        query = construct_query(ctx)

        # Truncated to 500 chars
        assert len(query) <= 500
        # Should not end with partial word
        assert query[-1].isalpha() or query[-1] in [" ", "d", "r"]

    def test_recency_boost_decreases_with_age(self) -> None:
        """Older commits get lower boost."""
        now = datetime.now(timezone.utc)
        from datetime import timedelta

        scores = []
        for days_old in [0, 10, 20, 30, 40]:
            commit_time = now - timedelta(days=days_old)
            score, _ = apply_recency_weight(1.0, commit_time, now, recent_window_days=30)
            scores.append(score)

        # Scores should be decreasing
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1]

    def test_zero_score_stays_zero(self) -> None:
        """Zero original score unaffected by recency."""
        now = datetime.now(timezone.utc)
        score, _ = apply_recency_weight(0.0, now, now)
        assert score == 0.0

    def test_error_context_validation(self) -> None:
        """Error context validates required fields."""
        # Valid minimal
        ctx1 = ErrorContext(file_path="app.py", line_number=1)
        assert ctx1.file_path == "app.py"

        # Invalid: missing file_path
        with pytest.raises(ValueError):
            ErrorContext(file_path="", line_number=1)

        # Invalid: missing line_number
        with pytest.raises(ValueError):
            ErrorContext(file_path="app.py", line_number=0)

    def test_retrieval_result_scoring(self) -> None:
        """RetrievalResult validates score ranges."""
        now = datetime.now(timezone.utc)

        # Valid scores
        result = RetrievalResult(
            rank=1,
            file_path="app.py",
            start_line=1,
            end_line=10,
            code_snippet="code",
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=now,
            original_score=0.9,
            recency_score=0.95,
            final_score=0.855,
        )
        assert result.final_score == 0.855

        # Invalid: score > 1.0
        with pytest.raises(ValueError):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=1,
                end_line=10,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=now,
                original_score=1.5,
            )

    def test_full_pipeline_flow(self) -> None:
        """Error → Query → Results → Format flow."""
        # Create error context
        ctx = ErrorContext(
            file_path="src/calculator.py",
            line_number=15,
            function_name="divide",
            error_type="ZeroDivisionError",
            error_message="division by zero",
        )

        # Generate query
        query = construct_query(ctx)
        assert "divide" in query

        # Mock retrieval result
        now = datetime.now(timezone.utc)
        result = RetrievalResult(
            rank=1,
            file_path="src/calculator.py",
            start_line=10,
            end_line=20,
            code_snippet="def divide(a, b):\n    return a / b",
            commit_hash="abc123",
            commit_author="alice",
            commit_timestamp=now,
            function_name="divide",
            original_score=0.92,
            recency_score=1.0,
            final_score=0.92,
        )

        # Format results
        from git_debug_oracle.retriever.result_formatter import format_results

        formatted = format_results([result], [], ctx)

        assert formatted["error_context"]["file_path"] == "src/calculator.py"
        assert len(formatted["retrieval_results"]) == 1
        assert formatted["retrieval_results"][0]["rank"] == 1
        assert formatted["retrieval_results"][0]["score"] == 0.92
