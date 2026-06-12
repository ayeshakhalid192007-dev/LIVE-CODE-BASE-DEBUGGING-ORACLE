"""Unit tests for Python stacktrace parser."""

import pytest

from git_debug_oracle.error_ingestion.stacktrace import parse_python_stacktrace


class TestPythonStacktraceParser:
    """Test suite for Python stacktrace parsing."""

    def test_parse_simple_traceback(self) -> None:
        """Simple 2-frame Python traceback."""
        stacktrace = """Traceback (most recent call last):
  File "src/app.py", line 42, in process_data
    result = calculate(x, y)
  File "src/math.py", line 15, in calculate
    return a / b
ZeroDivisionError: division by zero"""

        frames = parse_python_stacktrace(stacktrace)
        assert len(frames) == 2
        assert frames[0].file_path == "src/app.py"
        assert frames[0].line_number == 42
        assert frames[0].function_name == "process_data"
        assert frames[1].file_path == "src/math.py"
        assert frames[1].line_number == 15
        assert frames[1].function_name == "calculate"

    def test_parse_single_frame(self) -> None:
        """Traceback with single frame."""
        stacktrace = """Traceback (most recent call last):
  File "test.py", line 1, in <module>
    x = 1 / 0
ZeroDivisionError: division by zero"""

        frames = parse_python_stacktrace(stacktrace)
        assert len(frames) == 1
        assert frames[0].file_path == "test.py"
        assert frames[0].line_number == 1
        assert frames[0].function_name == "<module>"

    def test_parse_no_traceback_header(self) -> None:
        """Stacktrace without Traceback header returns empty."""
        stacktrace = "Some random error text"
        frames = parse_python_stacktrace(stacktrace)
        assert frames == []

    def test_parse_invalid_format(self) -> None:
        """Malformed stacktrace returns empty list."""
        stacktrace = "not a valid traceback at all"
        frames = parse_python_stacktrace(stacktrace)
        assert frames == []

    def test_parse_absolute_path(self) -> None:
        """Absolute paths handled correctly."""
        stacktrace = """Traceback (most recent call last):
  File "/home/user/project/src/app.py", line 42, in process_data
    x = 1
ValueError: something"""

        frames = parse_python_stacktrace(stacktrace)
        assert frames[0].file_path == "/home/user/project/src/app.py"

    def test_parse_with_context_lines(self) -> None:
        """Code context lines are skipped."""
        stacktrace = """Traceback (most recent call last):
  File "app.py", line 10, in main
    result = process()
    ^^^^^^^^^
  File "app.py", line 5, in process
    return 1 / 0
ValueError: error"""

        frames = parse_python_stacktrace(stacktrace)
        assert len(frames) == 2

    def test_parse_missing_line_number(self) -> None:
        """Frame with missing line number is skipped."""
        stacktrace = """Traceback (most recent call last):
  File "app.py", in unknown_function
    some_code()
ValueError: error"""

        frames = parse_python_stacktrace(stacktrace)
        assert len(frames) == 0
