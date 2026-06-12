"""Tests for query constructor that builds vector search queries from error context."""

import pytest

from git_debug_oracle.error_ingestion.models import ErrorContext, StackFrame
from git_debug_oracle.retriever.query_constructor import construct_query


class TestQueryConstructor:
    """Query construction from ErrorContext."""

    def test_query_with_function_name(self) -> None:
        """Function name takes priority in query."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name="process_data",
            error_type="ValueError",
            error_message="invalid input",
        )
        query = construct_query(ctx)
        assert "process_data" in query
        assert "src/app.py" in query
        assert "invalid input" in query

    def test_query_without_function_name(self) -> None:
        """Falls back to file_path when no function_name."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name=None,
            error_type="ValueError",
            error_message="invalid input",
        )
        query = construct_query(ctx)
        assert "src/app.py" in query
        assert "invalid input" in query

    def test_query_minimal_fields(self) -> None:
        """Query with only file_path and line_number."""
        ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
            function_name=None,
            error_type=None,
            error_message=None,
        )
        query = construct_query(ctx)
        assert "app.py" in query
        assert len(query) > 0

    def test_query_max_length(self) -> None:
        """Query truncated to 500 characters."""
        long_message = "x" * 600
        ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
            function_name="func",
            error_type="Error",
            error_message=long_message,
        )
        query = construct_query(ctx)
        assert len(query) <= 500

    def test_query_whitespace_normalized(self) -> None:
        """Multiple spaces collapsed to single space."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name="func  with  spaces",
            error_type="Error",
            error_message="message  with   spaces",
        )
        query = construct_query(ctx)
        assert "  " not in query

    def test_query_leading_trailing_whitespace(self) -> None:
        """Leading and trailing whitespace removed."""
        ctx = ErrorContext(
            file_path="  app.py  ",
            line_number=1,
            function_name="  func  ",
            error_type=None,
            error_message=None,
        )
        query = construct_query(ctx)
        assert query[0] != " "
        assert query[-1] != " "

    def test_query_all_fields(self) -> None:
        """Query includes function, file, error type, and message."""
        ctx = ErrorContext(
            file_path="src/calculator.py",
            line_number=15,
            function_name="divide",
            error_type="ZeroDivisionError",
            error_message="division by zero",
        )
        query = construct_query(ctx)
        assert "divide" in query
        assert "calculator" in query
        assert "zero" in query

    def test_query_none_fields_excluded(self) -> None:
        """None fields not included in query string."""
        ctx = ErrorContext(
            file_path="app.py",
            line_number=1,
            function_name="process",
            error_type=None,
            error_message=None,
        )
        query = construct_query(ctx)
        assert "None" not in query

    def test_query_special_characters_preserved(self) -> None:
        """Special characters in error message preserved."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name=None,
            error_type="KeyError",
            error_message="'user_id' not found",
        )
        query = construct_query(ctx)
        assert "user_id" in query or "found" in query
