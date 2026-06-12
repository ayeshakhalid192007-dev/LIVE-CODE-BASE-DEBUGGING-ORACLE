"""Unit tests for stacktrace normalization."""

import pytest

from git_debug_oracle.error_ingestion.stacktrace import normalize_stacktrace


class TestStacktraceNormalization:
    """Test suite for stacktrace normalization."""

    def test_normalize_stacktrace_none(self) -> None:
        """None stacktrace stays None."""
        result = normalize_stacktrace(None)
        assert result is None

    def test_normalize_stacktrace_string(self) -> None:
        """String stacktrace unchanged."""
        trace = "Traceback..."
        result = normalize_stacktrace(trace)
        assert result == trace

    def test_normalize_stacktrace_empty_list(self) -> None:
        """Empty list becomes None."""
        result = normalize_stacktrace([])
        assert result is None

    def test_normalize_stacktrace_list_to_string(self) -> None:
        """List joined with newlines."""
        trace_list = ["line 1", "line 2", "line 3"]
        result = normalize_stacktrace(trace_list)
        assert result == "line 1\nline 2\nline 3"

    def test_normalize_stacktrace_single_item_list(self) -> None:
        """Single-item list becomes string."""
        trace_list = ["single line"]
        result = normalize_stacktrace(trace_list)
        assert result == "single line"

    def test_normalize_stacktrace_list_with_empty_strings(self) -> None:
        """List with empty strings joined normally."""
        trace_list = ["line 1", "", "line 3"]
        result = normalize_stacktrace(trace_list)
        assert result == "line 1\n\nline 3"
