"""Integration tests for Phase 4 fix generation pipeline."""

import pytest
from datetime import datetime, timezone
from unittest.mock import patch

from git_debug_oracle.fix_generation.pipeline import FixGenerationPipeline
from git_debug_oracle.fix_generation.claude_client import ClaudeClient
from git_debug_oracle.types import (
    CodeChunk,
    CommitDiff,
    ErrorPayload,
    RetrievalResult,
)


@pytest.fixture
def claude_client() -> ClaudeClient:
    """Create Claude client for testing."""
    return ClaudeClient(
        api_key="test-key",
        model="claude-opus-4-1",
        max_tokens=2048,
    )


@pytest.fixture
def pipeline(claude_client: ClaudeClient) -> FixGenerationPipeline:
    """Create fix generation pipeline."""
    return FixGenerationPipeline(claude_client)


@pytest.fixture
def sample_error() -> ErrorPayload:
    """Sample error payload."""
    return ErrorPayload(
        error_type="IndexError",
        error_message="list index out of range",
        file_path="src/app.py",
        line_number=42,
        function_name="process_items",
        stacktrace="Traceback...",
        timestamp=datetime.now(timezone.utc),
        source_system="sentry",
        additional_context={},
    )


@pytest.fixture
def sample_retrieval_results() -> list[RetrievalResult]:
    """Sample retrieval results."""
    chunk = CodeChunk(
        content="for i in range(len(items) - 1):\n    process(items[i])",
        file_path="src/app.py",
        start_line=40,
        end_line=45,
        commit_hash="abc123",
        commit_author="developer",
        commit_timestamp=datetime.now(timezone.utc),
        function_name="process_items",
        embedding=None,
        chunk_id="chunk_1",
    )

    return [
        RetrievalResult(
            chunk=chunk,
            score=0.85,
            recency_score=0.9,
            combined_score=0.875,
            rank=1,
        )
    ]


@pytest.fixture
def sample_diffs() -> list[CommitDiff]:
    """Sample commit diffs."""
    return [
        CommitDiff(
            commit_hash="abc123",
            commit_author="developer",
            commit_timestamp=datetime.now(timezone.utc),
            commit_message="Fix off-by-one error",
            file_path="src/app.py",
            diff_content="- for i in range(len(items)):\n+ for i in range(len(items) - 1):",
            additions=1,
            deletions=1,
        )
    ]


class TestFixGenerationPipeline:
    """Tests for fix generation pipeline."""

    def test_pipeline_with_mocked_claude(
        self,
        pipeline: FixGenerationPipeline,
        sample_error: ErrorPayload,
        sample_retrieval_results: list[RetrievalResult],
        sample_diffs: list[CommitDiff],
    ) -> None:
        """Pipeline succeeds with mocked Claude response."""
        claude_response = """
ROOT CAUSE: Off-by-one error in loop boundary

FIX:
```python
for i in range(len(items) - 1):
    process(items[i])
```

CONFIDENCE: 0.85

EXPLANATION: The loop was iterating one element too far.
"""

        with patch.object(
            pipeline.claude,
            "call_with_caching",
            return_value=claude_response,
        ):
            fix = pipeline.generate_fix(sample_error, sample_retrieval_results, sample_diffs)

            assert fix is not None
            assert "off-by-one" in fix.root_cause.lower()
            assert fix.confidence > 0.7
            assert fix.affected_file == "src/app.py"

    def test_pipeline_fallback_on_api_failure(
        self,
        pipeline: FixGenerationPipeline,
        sample_error: ErrorPayload,
        sample_retrieval_results: list[RetrievalResult],
        sample_diffs: list[CommitDiff],
    ) -> None:
        """Pipeline uses fallback when Claude API fails."""
        with patch.object(
            pipeline.claude,
            "call_with_caching",
            return_value=None,
        ):
            fix = pipeline.generate_fix(sample_error, sample_retrieval_results, sample_diffs)

            # Fallback should return something
            assert fix is not None
            # Confidence should be lower
            assert fix.confidence < 0.7

    def test_pipeline_fallback_on_circuit_breaker(
        self,
        pipeline: FixGenerationPipeline,
        sample_error: ErrorPayload,
        sample_retrieval_results: list[RetrievalResult],
        sample_diffs: list[CommitDiff],
    ) -> None:
        """Pipeline uses fallback when circuit breaker open."""
        # Open circuit breaker
        pipeline.claude.circuit_breaker_failures = (
            pipeline.claude.circuit_breaker_threshold
        )

        fix = pipeline.generate_fix(sample_error, sample_retrieval_results, sample_diffs)

        assert fix is not None
        assert fix.confidence < 0.7
