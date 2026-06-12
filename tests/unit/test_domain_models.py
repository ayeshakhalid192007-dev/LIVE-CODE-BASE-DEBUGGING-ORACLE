"""Unit tests for domain models."""

import pytest
from datetime import datetime, timezone

from git_debug_oracle.error_ingestion import (
    CommitDiff,
    ErrorContext,
    RetrievalResult,
    RetrievalResultList,
    StackFrame,
)


class TestStackFrame:
    """Test suite for StackFrame dataclass."""

    def test_create_valid_stackframe(self) -> None:
        """Create valid StackFrame with all required fields."""
        frame = StackFrame(
            file_path="src/app.py",
            function_name="process_data",
            line_number=42,
        )
        assert frame.file_path == "src/app.py"
        assert frame.function_name == "process_data"
        assert frame.line_number == 42

    def test_stackframe_invalid_zero_line_number(self) -> None:
        """StackFrame rejects line_number of 0."""
        with pytest.raises(ValueError, match="line_number must be > 0"):
            StackFrame(
                file_path="app.py",
                function_name="func",
                line_number=0,
            )

    def test_stackframe_invalid_negative_line_number(self) -> None:
        """StackFrame rejects negative line_number."""
        with pytest.raises(ValueError, match="line_number must be > 0"):
            StackFrame(
                file_path="app.py",
                function_name="func",
                line_number=-1,
            )

    def test_stackframe_valid_line_number_one(self) -> None:
        """StackFrame accepts line_number of 1."""
        frame = StackFrame(
            file_path="app.py",
            function_name="func",
            line_number=1,
        )
        assert frame.line_number == 1


class TestErrorContext:
    """Test suite for ErrorContext dataclass."""

    def test_create_minimal_valid_error_context(self) -> None:
        """Create ErrorContext with only required fields."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
        )
        assert ctx.file_path == "src/app.py"
        assert ctx.line_number == 42
        assert ctx.function_name is None
        assert ctx.error_type is None
        assert ctx.error_message is None
        assert ctx.stacktrace is None
        assert ctx.language is None
        assert ctx.parsed_frames == []

    def test_create_full_error_context(self) -> None:
        """Create ErrorContext with all fields populated."""
        frame = StackFrame(
            file_path="src/app.py",
            function_name="process",
            line_number=42,
        )
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name="process_data",
            error_type="ValueError",
            error_message="invalid input",
            stacktrace="Traceback...",
            language="python",
            parsed_frames=[frame],
        )
        assert ctx.file_path == "src/app.py"
        assert ctx.line_number == 42
        assert ctx.function_name == "process_data"
        assert ctx.error_type == "ValueError"
        assert ctx.error_message == "invalid input"
        assert ctx.stacktrace == "Traceback..."
        assert ctx.language == "python"
        assert len(ctx.parsed_frames) == 1
        assert ctx.parsed_frames[0].function_name == "process"

    def test_error_context_invalid_empty_file_path(self) -> None:
        """ErrorContext rejects empty file_path."""
        with pytest.raises(ValueError, match="file_path must not be empty"):
            ErrorContext(
                file_path="",
                line_number=42,
            )

    def test_error_context_invalid_whitespace_only_file_path(self) -> None:
        """ErrorContext rejects whitespace-only file_path."""
        with pytest.raises(ValueError, match="file_path must not be empty"):
            ErrorContext(
                file_path="   ",
                line_number=42,
            )

    def test_error_context_invalid_zero_line_number(self) -> None:
        """ErrorContext rejects line_number of 0."""
        with pytest.raises(ValueError, match="line_number must be > 0"):
            ErrorContext(
                file_path="app.py",
                line_number=0,
            )

    def test_error_context_invalid_negative_line_number(self) -> None:
        """ErrorContext rejects negative line_number."""
        with pytest.raises(ValueError, match="line_number must be > 0"):
            ErrorContext(
                file_path="app.py",
                line_number=-1,
            )

    def test_error_context_valid_line_number_one(self) -> None:
        """ErrorContext accepts line_number of 1."""
        ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        assert ctx.line_number == 1


class TestRetrievalResult:
    """Test suite for RetrievalResult dataclass."""

    def test_create_valid_retrieval_result(self) -> None:
        """Create valid RetrievalResult with all fields."""
        ts = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        result = RetrievalResult(
            rank=1,
            file_path="src/app.py",
            start_line=10,
            end_line=20,
            code_snippet="code here",
            commit_hash="abc123",
            commit_author="Alice",
            commit_timestamp=ts,
            function_name="process",
            original_score=0.95,
            recency_score=1.0,
            final_score=0.95,
        )
        assert result.rank == 1
        assert result.file_path == "src/app.py"
        assert result.start_line == 10
        assert result.end_line == 20
        assert result.code_snippet == "code here"
        assert result.commit_hash == "abc123"
        assert result.commit_author == "Alice"
        assert result.commit_timestamp == ts
        assert result.function_name == "process"
        assert result.original_score == 0.95
        assert result.recency_score == 1.0
        assert result.final_score == 0.95

    def test_retrieval_result_invalid_original_score_negative(self) -> None:
        """RetrievalResult rejects original_score < 0."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="original_score must be in"):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=1,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
                original_score=-0.1,
            )

    def test_retrieval_result_invalid_original_score_too_high(self) -> None:
        """RetrievalResult rejects original_score > 1."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="original_score must be in"):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=1,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
                original_score=1.1,
            )

    def test_retrieval_result_invalid_recency_score_negative(self) -> None:
        """RetrievalResult rejects recency_score < 0."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="recency_score must be in"):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=1,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
                recency_score=-0.1,
            )

    def test_retrieval_result_invalid_final_score_too_high(self) -> None:
        """RetrievalResult rejects final_score > 1."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="final_score must be in"):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=1,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
                final_score=1.1,
            )

    def test_retrieval_result_invalid_rank_zero(self) -> None:
        """RetrievalResult rejects rank < 1."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="rank must be >= 1"):
            RetrievalResult(
                rank=0,
                file_path="app.py",
                start_line=1,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
            )

    def test_retrieval_result_invalid_start_line_zero(self) -> None:
        """RetrievalResult rejects start_line < 1."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="start_line must be >= 1"):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=0,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
            )

    def test_retrieval_result_invalid_end_line_before_start(self) -> None:
        """RetrievalResult rejects end_line < start_line."""
        ts = datetime.now(timezone.utc)
        with pytest.raises(ValueError, match="end_line .* must be >="):
            RetrievalResult(
                rank=1,
                file_path="app.py",
                start_line=10,
                end_line=5,
                code_snippet="code",
                commit_hash="hash",
                commit_author="author",
                commit_timestamp=ts,
            )

    def test_retrieval_result_valid_boundary_scores(self) -> None:
        """RetrievalResult accepts boundary scores (0.0 and 1.0)."""
        ts = datetime.now(timezone.utc)
        result = RetrievalResult(
            rank=1,
            file_path="app.py",
            start_line=1,
            end_line=5,
            code_snippet="code",
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=ts,
            original_score=0.0,
            recency_score=1.0,
            final_score=0.0,
        )
        assert result.original_score == 0.0
        assert result.recency_score == 1.0
        assert result.final_score == 0.0


class TestCommitDiff:
    """Test suite for CommitDiff dataclass."""

    def test_create_valid_commit_diff_with_diff_content(self) -> None:
        """Create CommitDiff with full diff content."""
        ts = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        diff = CommitDiff(
            commit_hash="abc123def",
            author="Alice",
            message="Fix bug in process_data",
            timestamp=ts,
            files_changed=["src/app.py", "src/math.py"],
            diff_content="@@ -1,5 +1,6 @@\n-old\n+new\n",
        )
        assert diff.commit_hash == "abc123def"
        assert diff.author == "Alice"
        assert diff.message == "Fix bug in process_data"
        assert diff.timestamp == ts
        assert diff.files_changed == ["src/app.py", "src/math.py"]
        assert diff.diff_content == "@@ -1,5 +1,6 @@\n-old\n+new\n"

    def test_create_valid_commit_diff_without_diff_content(self) -> None:
        """Create CommitDiff without diff_content (for non-top results)."""
        ts = datetime.now(timezone.utc)
        diff = CommitDiff(
            commit_hash="xyz789",
            author="Bob",
            message="Update dependencies",
            timestamp=ts,
            files_changed=["pyproject.toml"],
            diff_content=None,
        )
        assert diff.commit_hash == "xyz789"
        assert diff.diff_content is None

    def test_create_commit_diff_with_empty_files_changed(self) -> None:
        """Create CommitDiff with no files changed (edge case)."""
        ts = datetime.now(timezone.utc)
        diff = CommitDiff(
            commit_hash="hash",
            author="author",
            message="Empty commit",
            timestamp=ts,
            files_changed=[],
            diff_content=None,
        )
        assert diff.files_changed == []


class TestRetrievalResultList:
    """Test suite for RetrievalResultList dataclass."""

    def test_create_valid_retrieval_result_list(self) -> None:
        """Create valid RetrievalResultList with results and diffs."""
        ts = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        result = RetrievalResult(
            rank=1,
            file_path="src/app.py",
            start_line=1,
            end_line=5,
            code_snippet="code",
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=ts,
        )
        diff = CommitDiff(
            commit_hash="hash",
            author="author",
            message="msg",
            timestamp=ts,
            files_changed=["app.py"],
        )
        metadata = {
            "query_used": "test query",
            "total_chunks_searched": 100,
            "search_duration_ms": 250.5,
            "timestamp": ts.isoformat(),
        }

        result_list = RetrievalResultList(
            error_context=error_ctx,
            retrieval_results=[result],
            related_diffs=[diff],
            metadata=metadata,
        )

        assert result_list.error_context == error_ctx
        assert len(result_list.retrieval_results) == 1
        assert len(result_list.related_diffs) == 1
        assert result_list.metadata == metadata

    def test_retrieval_result_list_empty_results(self) -> None:
        """Create RetrievalResultList with no results."""
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
        )
        result_list = RetrievalResultList(
            error_context=error_ctx,
            retrieval_results=[],
            related_diffs=[],
            metadata={"query_used": "query"},
        )
        assert len(result_list.retrieval_results) == 0
        assert len(result_list.related_diffs) == 0

    def test_to_dict_converts_to_json_serializable(self) -> None:
        """to_dict() returns JSON-serializable dictionary."""
        ts = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=42,
            function_name="process",
            error_type="ValueError",
            error_message="invalid",
        )
        result = RetrievalResult(
            rank=1,
            file_path="src/app.py",
            start_line=10,
            end_line=20,
            code_snippet="code",
            commit_hash="abc123",
            commit_author="Alice",
            commit_timestamp=ts,
            function_name="func",
            original_score=0.95,
            recency_score=1.0,
            final_score=0.95,
        )
        diff = CommitDiff(
            commit_hash="abc123",
            author="Alice",
            message="Fix",
            timestamp=ts,
            files_changed=["app.py"],
            diff_content="@@ -1,5 +1,6 @@",
        )
        result_list = RetrievalResultList(
            error_context=error_ctx,
            retrieval_results=[result],
            related_diffs=[diff],
            metadata={"query_used": "test"},
        )

        as_dict = result_list.to_dict()

        assert "error_context" in as_dict
        assert "retrieval_results" in as_dict
        assert "related_diffs" in as_dict
        assert "metadata" in as_dict

        assert as_dict["error_context"]["file_path"] == "app.py"
        assert as_dict["error_context"]["line_number"] == 42
        assert as_dict["error_context"]["function_name"] == "process"

        assert len(as_dict["retrieval_results"]) == 1
        result_dict = as_dict["retrieval_results"][0]
        assert result_dict["rank"] == 1
        assert result_dict["file_path"] == "src/app.py"
        assert result_dict["start_line"] == 10
        assert result_dict["end_line"] == 20
        assert result_dict["score"] == 0.95
        assert "T" in result_dict["commit_timestamp"]  # ISO8601 format

        assert len(as_dict["related_diffs"]) == 1
        diff_dict = as_dict["related_diffs"][0]
        assert diff_dict["commit_hash"] == "abc123"
        assert diff_dict["author"] == "Alice"

    def test_to_dict_none_fields_preserved(self) -> None:
        """to_dict() preserves None values for optional fields."""
        ts = datetime.now(timezone.utc)
        error_ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
            function_name=None,
            error_type=None,
            error_message=None,
        )
        result = RetrievalResult(
            rank=1,
            file_path="app.py",
            start_line=1,
            end_line=5,
            code_snippet="code",
            commit_hash="hash",
            commit_author="author",
            commit_timestamp=ts,
            function_name=None,
        )
        result_list = RetrievalResultList(
            error_context=error_ctx,
            retrieval_results=[result],
            related_diffs=[],
            metadata={},
        )

        as_dict = result_list.to_dict()

        assert as_dict["error_context"]["function_name"] is None
        assert as_dict["error_context"]["error_type"] is None
        assert as_dict["error_context"]["error_message"] is None
        assert as_dict["retrieval_results"][0]["function_name"] is None
