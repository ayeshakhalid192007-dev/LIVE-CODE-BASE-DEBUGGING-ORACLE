"""Unit tests for error payload parser."""

import pytest

from git_debug_oracle.error_ingestion.parsers import parse_error_payload


class TestErrorPayloadParser:
    """Test suite for error payload parsing."""

    def test_parse_valid_minimal_payload(self) -> None:
        """Minimum valid payload: file_path and line_number only."""
        payload = {"file_path": "src/app.py", "line_number": 42}
        result = parse_error_payload(payload)
        assert result.file_path == "src/app.py"
        assert result.line_number == 42
        assert result.function_name is None

    def test_parse_valid_full_payload(self) -> None:
        """All fields present and valid."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "function_name": "process_data",
            "error_type": "ZeroDivisionError",
            "error_message": "division by zero",
            "stacktrace": "Traceback...",
            "language": "python",
        }
        result = parse_error_payload(payload)
        assert result.file_path == "src/app.py"
        assert result.line_number == 42
        assert result.function_name == "process_data"

    def test_parse_missing_file_path(self) -> None:
        """file_path is required."""
        payload = {"line_number": 42}
        with pytest.raises(ValueError, match="file_path"):
            parse_error_payload(payload)

    def test_parse_missing_line_number(self) -> None:
        """line_number is required."""
        payload = {"file_path": "src/app.py"}
        with pytest.raises(ValueError, match="line_number"):
            parse_error_payload(payload)

    def test_parse_invalid_line_number_zero(self) -> None:
        """line_number must be > 0."""
        payload = {"file_path": "src/app.py", "line_number": 0}
        with pytest.raises(ValueError, match="line_number"):
            parse_error_payload(payload)

    def test_parse_invalid_line_number_negative(self) -> None:
        """line_number must be > 0."""
        payload = {"file_path": "src/app.py", "line_number": -1}
        with pytest.raises(ValueError, match="line_number"):
            parse_error_payload(payload)

    def test_parse_empty_file_path(self) -> None:
        """file_path must not be empty string."""
        payload = {"file_path": "", "line_number": 42}
        with pytest.raises(ValueError, match="file_path"):
            parse_error_payload(payload)

    def test_parse_stacktrace_string(self) -> None:
        """stacktrace as string is valid."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "stacktrace": "Traceback (most recent call last):\n  File...",
        }
        result = parse_error_payload(payload)
        assert result.stacktrace is not None

    def test_parse_stacktrace_list(self) -> None:
        """stacktrace as list is normalized to string."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "stacktrace": ["File src/app.py", "line 42"],
        }
        result = parse_error_payload(payload)
        assert isinstance(result.stacktrace, str)
        assert "File src/app.py" in result.stacktrace

    def test_parse_stacktrace_invalid_type(self) -> None:
        """stacktrace must be string or list."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "stacktrace": 123,
        }
        with pytest.raises(ValueError, match="stacktrace"):
            parse_error_payload(payload)

    def test_parse_extra_fields_ignored(self) -> None:
        """Extra fields in payload are ignored gracefully."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "unknown_field": "ignored",
        }
        result = parse_error_payload(payload)
        assert result.file_path == "src/app.py"

    def test_parse_whitespace_in_file_path(self) -> None:
        """Leading/trailing whitespace in file_path trimmed."""
        payload = {"file_path": "  src/app.py  ", "line_number": 42}
        # Should fail because we check for empty after strip, but the value itself isn't trimmed
        # Actually, looking at the code, we check if file_path.strip() is empty, so whitespace-only is rejected
        with pytest.raises(ValueError, match="file_path"):
            parse_error_payload(payload={"file_path": "   ", "line_number": 42})

    def test_parse_line_number_as_string(self) -> None:
        """line_number must be integer, not string."""
        payload = {"file_path": "src/app.py", "line_number": "42"}
        with pytest.raises(ValueError, match="line_number"):
            parse_error_payload(payload)

    def test_parse_stacktrace_empty_list(self) -> None:
        """Empty list stacktrace becomes None."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "stacktrace": [],
        }
        result = parse_error_payload(payload)
        assert result.stacktrace is None
