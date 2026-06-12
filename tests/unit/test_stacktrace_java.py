"""Unit tests for Java stacktrace parser."""

import pytest

from git_debug_oracle.error_ingestion.stacktrace import parse_java_stacktrace


class TestJavaStacktraceParser:
    """Test suite for Java stacktrace parsing."""

    def test_parse_simple_java_stacktrace(self) -> None:
        """Simple Java exception stacktrace."""
        stacktrace = """java.lang.NullPointerException
    at com.example.Calculator.divide(Calculator.java:45)
    at com.example.Main.main(Main.java:12)"""

        frames = parse_java_stacktrace(stacktrace)
        assert len(frames) == 2
        assert frames[0].file_path == "Calculator.java"
        assert frames[0].line_number == 45
        assert frames[0].function_name == "divide"
        assert frames[1].file_path == "Main.java"
        assert frames[1].line_number == 12
        assert frames[1].function_name == "main"

    def test_parse_with_native_methods(self) -> None:
        """Native methods are handled."""
        stacktrace = """java.io.IOException
    at java.lang.System.setOut(Native Method)
    at com.example.Main.main(Main.java:10)"""

        frames = parse_java_stacktrace(stacktrace)
        assert len(frames) == 1  # Native method skipped
        assert frames[0].file_path == "Main.java"
        assert frames[0].line_number == 10

    def test_parse_with_unknown_source(self) -> None:
        """Unknown source entries handled."""
        stacktrace = """java.lang.Exception
    at com.example.Foo.bar(Unknown Source)
    at com.example.Main.main(Main.java:10)"""

        frames = parse_java_stacktrace(stacktrace)
        assert len(frames) == 1  # Unknown source skipped
        assert frames[0].file_path == "Main.java"
        assert frames[0].line_number == 10

    def test_parse_with_package_name(self) -> None:
        """Full package.class.method names parsed correctly."""
        stacktrace = """java.lang.RuntimeException
    at org.springframework.boot.Application.run(Application.java:100)"""

        frames = parse_java_stacktrace(stacktrace)
        assert frames[0].function_name == "run"
        assert frames[0].file_path == "Application.java"
        assert frames[0].line_number == 100

    def test_parse_invalid_format(self) -> None:
        """Malformed Java stacktrace returns empty."""
        stacktrace = "not a java stacktrace"
        frames = parse_java_stacktrace(stacktrace)
        assert frames == []

    def test_parse_multiple_packages(self) -> None:
        """Deep package hierarchies parsed correctly."""
        stacktrace = """java.lang.IllegalArgumentException
    at com.example.service.impl.UserServiceImpl.validateUser(UserServiceImpl.java:55)
    at com.example.controller.UserController.createUser(UserController.java:20)"""

        frames = parse_java_stacktrace(stacktrace)
        assert len(frames) == 2
        assert frames[0].function_name == "validateUser"
        assert frames[0].file_path == "UserServiceImpl.java"
        assert frames[1].function_name == "createUser"
        assert frames[1].file_path == "UserController.java"

    def test_parse_constructor_method(self) -> None:
        """Constructor methods (init) handled correctly."""
        stacktrace = """java.lang.NullPointerException
    at com.example.MyClass.<init>(MyClass.java:30)"""

        frames = parse_java_stacktrace(stacktrace)
        assert len(frames) == 1
        assert frames[0].function_name == "<init>"
        assert frames[0].file_path == "MyClass.java"
