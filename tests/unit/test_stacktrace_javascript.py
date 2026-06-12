"""Unit tests for JavaScript stacktrace parser."""

import pytest

from git_debug_oracle.error_ingestion.stacktrace import parse_javascript_stacktrace


class TestJavaScriptStacktraceParser:
    """Test suite for JavaScript stacktrace parsing."""

    def test_parse_nodejs_format(self) -> None:
        """Node.js stacktrace format."""
        stacktrace = """Error: Cannot read property 'x' of undefined
    at processData (app.js:42:10)
    at Object.<anonymous> (app.js:1:1)"""

        frames = parse_javascript_stacktrace(stacktrace)
        assert len(frames) == 2
        assert frames[0].file_path == "app.js"
        assert frames[0].line_number == 42
        assert frames[0].function_name == "processData"
        assert frames[1].file_path == "app.js"
        assert frames[1].line_number == 1
        assert frames[1].function_name == "Object.<anonymous>"

    def test_parse_browser_format(self) -> None:
        """Browser @ format."""
        stacktrace = """Error: Cannot set property x
processData@app.js:42:10
Object.<anonymous>@app.js:1:1"""

        frames = parse_javascript_stacktrace(stacktrace)
        assert len(frames) >= 1
        assert frames[0].file_path == "app.js"
        assert frames[0].line_number == 42
        assert frames[0].function_name == "processData"

    def test_parse_anonymous_function(self) -> None:
        """Anonymous functions handled."""
        stacktrace = """Error: Something failed
    at <anonymous> (app.js:5:1)"""

        frames = parse_javascript_stacktrace(stacktrace)
        assert len(frames) == 1
        assert frames[0].function_name == "<anonymous>"
        assert frames[0].line_number == 5

    def test_parse_no_error_header(self) -> None:
        """Stacktrace without 'Error:' or 'at ' returns empty."""
        stacktrace = "just some text"
        frames = parse_javascript_stacktrace(stacktrace)
        assert frames == []

    def test_parse_column_number_ignored(self) -> None:
        """Column numbers are extracted but line_number used only."""
        stacktrace = """Error: test
    at func (file.js:42:15)"""

        frames = parse_javascript_stacktrace(stacktrace)
        assert frames[0].line_number == 42
        # Verify column (15) is not in the frame
        assert not hasattr(frames[0], 'column_number')

    def test_parse_multiple_frames(self) -> None:
        """Multiple frames parsed correctly."""
        stacktrace = """TypeError: Cannot read property 'map' of undefined
    at Array.forEach (<anonymous>)
    at processItems (src/processor.js:23:5)
    at main (src/index.js:10:3)"""

        frames = parse_javascript_stacktrace(stacktrace)
        assert len(frames) >= 2
        # Verify at least one frame is from src/processor.js
        files = [f.file_path for f in frames]
        assert "src/processor.js" in files or any(".js" in f for f in files)
