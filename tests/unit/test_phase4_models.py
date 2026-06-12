"""Unit tests for Phase 4 domain models and MCP schemas."""

import pytest
from datetime import datetime, timezone

from git_debug_oracle.types import FixProposal, IndexStatus, ErrorPayload, RetrievalResult, CodeChunk
from git_debug_oracle.mcp_tools.schemas import (
    DebugErrorInput,
    DebugErrorOutput,
    GetIndexStatusInput,
    IndexStatusOutput,
    SearchCodebaseInput,
    GetRecentDiffsInput,
)


class TestFixProposalModel:
    """Tests for FixProposal domain model."""

    def test_fix_proposal_creation(self) -> None:
        """Create valid FixProposal."""
        fix = FixProposal(
            root_cause="Off-by-one error in loop",
            affected_file="src/app.py",
            affected_line_range=(42, 45),
            code_patch="for i in range(len(items) - 1):",
            patch_language="python",
            confidence=0.85,
            explanation="Changed range end to exclude last item",
            affected_functions=["process_items"],
            root_cause_category="logic",
        )
        assert fix.confidence == 0.85
        assert fix.patch_language == "python"
        assert len(fix.affected_functions) == 1

    def test_fix_proposal_confidence_range(self) -> None:
        """Confidence should be 0-1 (test documents expected range)."""
        # Dataclasses don't validate by default; this documents expected usage
        fix = FixProposal(
            root_cause="error",
            affected_file="app.py",
            affected_line_range=(1, 5),
            code_patch="fix",
            patch_language="python",
            confidence=0.85,  # Valid 0-1
            explanation="test",
            affected_functions=[],
            root_cause_category="logic",
        )
        assert 0 <= fix.confidence <= 1

    def test_fix_proposal_alternative_fixes_default(self) -> None:
        """Alternative fixes default to empty list."""
        fix = FixProposal(
            root_cause="error",
            affected_file="app.py",
            affected_line_range=(1, 5),
            code_patch="fix",
            patch_language="python",
            confidence=0.8,
            explanation="test",
            affected_functions=[],
            root_cause_category="logic",
        )
        assert fix.alternative_fixes == []


class TestIndexStatusModel:
    """Tests for IndexStatus domain model."""

    def test_index_status_creation(self) -> None:
        """Create valid IndexStatus."""
        now = datetime.now(timezone.utc)
        status = IndexStatus(
            is_indexed=True,
            last_indexed_commit="abc123",
            last_indexed_timestamp=now,
            total_chunks=1000,
            total_files=50,
            branch="main",
            status="indexed",
        )
        assert status.is_indexed is True
        assert status.total_chunks == 1000
        assert status.status == "indexed"

    def test_index_status_not_indexed(self) -> None:
        """Create IndexStatus for non-indexed repo."""
        now = datetime.now(timezone.utc)
        status = IndexStatus(
            is_indexed=False,
            last_indexed_commit="",
            last_indexed_timestamp=now,
            total_chunks=0,
            total_files=0,
            branch="main",
            status="not_indexed",
        )
        assert status.is_indexed is False
        assert status.total_chunks == 0


class TestDebugErrorInputSchema:
    """Tests for debug_error input schema."""

    def test_valid_input(self) -> None:
        """Valid debug_error input."""
        input_data = DebugErrorInput(
            file_path="app.py",
            line_number=42,
            error_type="IndexError",
            error_message="list index out of range",
        )
        assert input_data.file_path == "app.py"
        assert input_data.line_number == 42

    def test_invalid_line_number_zero(self) -> None:
        """Line number must be > 0."""
        with pytest.raises(ValueError):
            DebugErrorInput(
                file_path="app.py",
                line_number=0,
            )

    def test_invalid_line_number_negative(self) -> None:
        """Line number must be positive."""
        with pytest.raises(ValueError):
            DebugErrorInput(
                file_path="app.py",
                line_number=-1,
            )

    def test_optional_fields(self) -> None:
        """Optional fields can be omitted."""
        input_data = DebugErrorInput(
            file_path="app.py",
            line_number=42,
        )
        assert input_data.function_name is None
        assert input_data.error_type is None


class TestDebugErrorOutputSchema:
    """Tests for debug_error output schema."""

    def test_valid_output_with_fix(self) -> None:
        """Valid output with fix proposal."""
        output = DebugErrorOutput(
            error_context={
                "file_path": "app.py",
                "line_number": 42,
                "function_name": None,
                "error_type": None,
                "error_message": None,
            },
            retrieval_results=[],
            fix_proposal={
                "root_cause": "Off-by-one error",
                "affected_file": "app.py",
                "affected_line_range": (42, 45),
                "code_patch": "for i in range(len(items) - 1):",
                "patch_language": "python",
                "confidence": 0.85,
                "explanation": "Fix the loop boundary",
                "affected_functions": ["process"],
                "root_cause_category": "logic",
            },
            status="success",
        )
        assert output.status == "success"
        assert output.fix_proposal is not None

    def test_partial_output_no_fix(self) -> None:
        """Partial output without fix proposal."""
        output = DebugErrorOutput(
            error_context={
                "file_path": "app.py",
                "line_number": 42,
                "function_name": None,
                "error_type": None,
                "error_message": None,
            },
            retrieval_results=[],
            fix_proposal=None,
            status="partial",
        )
        assert output.status == "partial"
        assert output.fix_proposal is None

    def test_invalid_status(self) -> None:
        """Invalid status rejected."""
        with pytest.raises(ValueError):
            DebugErrorOutput(
                error_context={
                    "file_path": "app.py",
                    "line_number": 42,
                    "function_name": None,
                    "error_type": None,
                    "error_message": None,
                },
                retrieval_results=[],
                fix_proposal=None,
                status="invalid",
            )


class TestGetIndexStatusSchema:
    """Tests for get_index_status schemas."""

    def test_input_with_branch(self) -> None:
        """Input with branch specified."""
        input_data = GetIndexStatusInput(branch="main")
        assert input_data.branch == "main"

    def test_input_without_branch(self) -> None:
        """Input without branch (optional)."""
        input_data = GetIndexStatusInput()
        assert input_data.branch is None

    def test_output_indexed_status(self) -> None:
        """Output for indexed repository."""
        output = IndexStatusOutput(
            is_indexed=True,
            last_indexed_commit="abc123",
            last_indexed_timestamp="2026-06-12T10:30:00Z",
            total_chunks=5000,
            total_files=150,
            branch="main",
            status="indexed",
        )
        assert output.status == "indexed"
        assert output.is_indexed is True

    def test_output_invalid_status(self) -> None:
        """Invalid status rejected."""
        with pytest.raises(ValueError):
            IndexStatusOutput(
                is_indexed=False,
                last_indexed_commit="",
                last_indexed_timestamp="2026-06-12T10:30:00Z",
                total_chunks=0,
                total_files=0,
                branch="main",
                status="unknown",
            )


class TestSearchCodebaseSchema:
    """Tests for search_codebase schemas."""

    def test_valid_input(self) -> None:
        """Valid search input."""
        input_data = SearchCodebaseInput(
            query="authentication error",
            top_k=5,
        )
        assert input_data.query == "authentication error"
        assert input_data.top_k == 5

    def test_top_k_limits(self) -> None:
        """top_k must be 1-20."""
        with pytest.raises(ValueError):
            SearchCodebaseInput(query="test", top_k=0)

        with pytest.raises(ValueError):
            SearchCodebaseInput(query="test", top_k=21)

    def test_optional_file_filter(self) -> None:
        """File filter is optional."""
        input_data = SearchCodebaseInput(
            query="test",
            file_filter=None,
        )
        assert input_data.file_filter is None


class TestGetRecentDiffsSchema:
    """Tests for get_recent_diffs schemas."""

    def test_valid_input(self) -> None:
        """Valid input."""
        input_data = GetRecentDiffsInput(
            num_commits=5,
            branch="main",
        )
        assert input_data.num_commits == 5
        assert input_data.branch == "main"

    def test_num_commits_limits(self) -> None:
        """num_commits must be 1-20."""
        with pytest.raises(ValueError):
            GetRecentDiffsInput(num_commits=0)

        with pytest.raises(ValueError):
            GetRecentDiffsInput(num_commits=21)

    def test_defaults(self) -> None:
        """Defaults applied correctly."""
        input_data = GetRecentDiffsInput()
        assert input_data.num_commits == 5
        assert input_data.branch is None
