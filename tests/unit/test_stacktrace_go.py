"""Unit tests for Go stacktrace parser."""

import pytest

from git_debug_oracle.error_ingestion.stacktrace import parse_go_stacktrace


class TestGoStacktraceParser:
    """Test suite for Go stacktrace parsing."""

    def test_parse_go_panic(self) -> None:
        """Go panic stacktrace."""
        stacktrace = """panic: runtime error: index out of range [10] with length 5

goroutine 1 [running]:
main.process()
	/path/to/file.go:42 +0x1c4
main.main()
	/path/to/file.go:15 +0x44"""

        frames = parse_go_stacktrace(stacktrace)
        assert len(frames) == 2
        assert frames[0].file_path == "/path/to/file.go"
        assert frames[0].line_number == 42
        assert frames[0].function_name == "process"
        assert frames[1].file_path == "/path/to/file.go"
        assert frames[1].line_number == 15
        assert frames[1].function_name == "main"

    def test_parse_single_goroutine(self) -> None:
        """Single goroutine processed."""
        stacktrace = """goroutine 1 [running]:
main.main()
	/app/main.go:10 +0x20"""

        frames = parse_go_stacktrace(stacktrace)
        assert len(frames) == 1
        assert frames[0].line_number == 10
        assert frames[0].function_name == "main"

    def test_parse_multiple_goroutines(self) -> None:
        """Multiple goroutines - main goroutine used only."""
        stacktrace = """goroutine 1 [running]:
main.main()
	/app/main.go:10 +0x20

goroutine 2 [runnable]:
main.worker()
	/app/worker.go:50 +0x40"""

        frames = parse_go_stacktrace(stacktrace)
        # Only goroutine 1 should be parsed
        assert any(f.line_number == 10 for f in frames)
        # Should not include goroutine 2
        assert not any(f.line_number == 50 for f in frames)

    def test_parse_invalid_format(self) -> None:
        """Malformed Go stacktrace returns empty."""
        stacktrace = "not a go stacktrace"
        frames = parse_go_stacktrace(stacktrace)
        assert frames == []

    def test_parse_with_package_prefix(self) -> None:
        """Package-prefixed function names extracted correctly."""
        stacktrace = """goroutine 1 [running]:
github.com/example/pkg.Handler()
	/home/user/src/handler.go:25 +0x100"""

        frames = parse_go_stacktrace(stacktrace)
        assert len(frames) == 1
        assert frames[0].function_name == "Handler"
        assert frames[0].file_path == "/home/user/src/handler.go"

    def test_parse_deep_call_stack(self) -> None:
        """Multiple function calls in stack."""
        stacktrace = """goroutine 1 [running]:
main.funcA()
	/app/a.go:10 +0x20
main.funcB()
	/app/b.go:20 +0x40
main.funcC()
	/app/c.go:30 +0x60"""

        frames = parse_go_stacktrace(stacktrace)
        assert len(frames) == 3
        assert frames[0].function_name == "funcA"
        assert frames[1].function_name == "funcB"
        assert frames[2].function_name == "funcC"

    def test_parse_no_goroutine_header(self) -> None:
        """Stacktrace without goroutine header returns empty."""
        stacktrace = """main.process()
	/app/main.go:42 +0x1c4"""

        frames = parse_go_stacktrace(stacktrace)
        assert frames == []

    def test_parse_goroutine_without_main(self) -> None:
        """Only non-main goroutines present returns empty."""
        stacktrace = """goroutine 2 [runnable]:
main.worker()
	/app/worker.go:50 +0x40"""

        frames = parse_go_stacktrace(stacktrace)
        assert frames == []
