"""Tests for result formatting to JSON output."""

import pytest
from datetime import datetime, timezone

from git_debug_oracle.error_ingestion.models import ErrorContext, RetrievalResult, CommitDiff
from git_debug_oracle.retriever.result_formatter import format_results


class TestResultFormatter:
    """Format retrieval results as JSON."""

    def test_format_minimal_results(self) -> None:
        """Format with minimal required fields."""
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        result = RetrievalResult(
            rank=1,
            file_path="src/app.py",
            start_line=10,
            end_line=20,
            code_snippet="def foo():\n    pass",
            commit_hash="abc123",
            commit_author="user",
            commit_timestamp=datetime.now(timezone.utc),
        )

        formatted = format_results([result], [], error_ctx)

        assert "error_context" in formatted
        assert "retrieval_results" in formatted
        assert "related_diffs" in formatted
        assert "metadata" in formatted

    def test_format_json_structure(self) -> None:
        """Output has required JSON structure."""
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        result = RetrievalResult(
            rank=1,
            file_path="app.py",
            start_line=1,
            end_line=5,
            code_snippet="code",
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=datetime.now(timezone.utc),
            final_score=0.85,
        )

        formatted = format_results([result], [], error_ctx)

        assert formatted["error_context"]["file_path"] == "app.py"
        assert len(formatted["retrieval_results"]) == 1
        assert formatted["retrieval_results"][0]["rank"] == 1
        assert formatted["retrieval_results"][0]["score"] == 0.85

    def test_format_code_snippet_truncation(self) -> None:
        """Code snippet truncated to 500 chars."""
        long_code = "x" * 600
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        result = RetrievalResult(
            rank=1,
            file_path="app.py",
            start_line=1,
            end_line=5,
            code_snippet=long_code,
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=datetime.now(timezone.utc),
        )

        formatted = format_results([result], [], error_ctx)

        assert len(formatted["retrieval_results"][0]["code_snippet"]) <= 500

    def test_format_timestamp_iso8601(self) -> None:
        """Timestamps formatted as ISO8601."""
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        ts = datetime(2026, 6, 12, 12, 30, 45, tzinfo=timezone.utc)
        result = RetrievalResult(
            rank=1,
            file_path="app.py",
            start_line=1,
            end_line=5,
            code_snippet="code",
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=ts,
        )

        formatted = format_results([result], [], error_ctx)

        ts_str = formatted["retrieval_results"][0]["commit_timestamp"]
        assert "T" in ts_str  # ISO8601 has T separator
        assert "2026-06-12" in ts_str

    def test_format_metadata_present(self) -> None:
        """Metadata includes required fields."""
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )

        formatted = format_results([], [], error_ctx)

        assert "query_used" in formatted["metadata"]
        assert "total_chunks_searched" in formatted["metadata"]
        assert "search_duration_ms" in formatted["metadata"]
        assert "timestamp" in formatted["metadata"]

    def test_format_multiple_results(self) -> None:
        """Multiple results ranked correctly."""
        error_ctx = ErrorContext(file_path="app.py", line_number=1)
        results = [
            RetrievalResult(
                rank=i,
                file_path=f"file{i}.py",
                start_line=i * 10,
                end_line=i * 10 + 5,
                code_snippet=f"code{i}",
                commit_hash=f"hash{i}",
                commit_author="author",
                commit_timestamp=datetime.now(timezone.utc),
                final_score=1.0 - (i * 0.1),
            )
            for i in range(1, 4)
        ]

        formatted = format_results(results, [], error_ctx)

        assert len(formatted["retrieval_results"]) == 3
        for i, res in enumerate(formatted["retrieval_results"], 1):
            assert res["rank"] == i

    def test_format_with_diffs(self) -> None:
        """Related diffs included in output."""
        error_ctx = ErrorContext(file_path="app.py", line_number=1)
        diff = CommitDiff(
            commit_hash="abc",
            author="user",
            message="fix bug",
            timestamp=datetime.now(timezone.utc),
            files_changed=["app.py", "test.py"],
            diff_content="--- a/app.py",
        )

        formatted = format_results([], [diff], error_ctx)

        assert len(formatted["related_diffs"]) == 1
        assert formatted["related_diffs"][0]["commit_hash"] == "abc"
        assert "app.py" in formatted["related_diffs"][0]["files_changed"]
