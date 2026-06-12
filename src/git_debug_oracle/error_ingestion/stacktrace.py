"""Stacktrace parsers for multiple programming languages.

This module provides parsers for extracting stack frames from stacktraces in
different languages: Python, JavaScript, Java, and Go. Each parser converts
language-specific stacktrace formats into a normalized StackFrame list.
"""

import re
from typing import Optional

from git_debug_oracle.error_ingestion.models import StackFrame


def parse_python_stacktrace(stacktrace: str) -> list[StackFrame]:
    """Parse Python traceback format into stack frames.

    Extracts file path, function name, and line number from Python Traceback
    format. Handles multi-line frames with context lines. Frames without
    line numbers are skipped gracefully.

    Args:
        stacktrace: Python traceback string

    Returns:
        List of StackFrame objects extracted from the traceback. Empty list
        if stacktrace is not valid Python format or cannot be parsed.

    Example:
        >>> trace = '''Traceback (most recent call last):
        ...   File "src/app.py", line 42, in process_data
        ...     result = calculate(x, y)
        ...   File "src/math.py", line 15, in calculate
        ...     return a / b
        ... ZeroDivisionError: division by zero'''
        >>> frames = parse_python_stacktrace(trace)
        >>> len(frames)
        2
        >>> frames[0].file_path
        'src/app.py'
    """
    if "Traceback" not in stacktrace:
        return []

    frames: list[StackFrame] = []

    # Pattern to match frame header: File "path", line N, in function_name
    frame_pattern = r'^\s*File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(.+)$'

    for line in stacktrace.split("\n"):
        match = re.match(frame_pattern, line)
        if match:
            file_path = match.group(1)
            line_number_str = match.group(2)
            function_name = match.group(3)

            try:
                line_number = int(line_number_str)
                if line_number > 0:
                    frames.append(
                        StackFrame(
                            file_path=file_path,
                            function_name=function_name,
                            line_number=line_number,
                        )
                    )
            except ValueError:
                # Skip frames with invalid line numbers
                pass

    return frames


def parse_javascript_stacktrace(stacktrace: str) -> list[StackFrame]:
    """Parse JavaScript/Node.js stacktrace formats.

    Handles both Node.js format (at function (file.js:line:col)) and browser
    format (functionName@file.js:line:col). Anonymous functions are shown
    as "<anonymous>". Column numbers are extracted but only line_number is
    used in the StackFrame.

    Args:
        stacktrace: JavaScript stacktrace string

    Returns:
        List of StackFrame objects. Empty list if stacktrace is not valid
        JavaScript format.

    Example:
        >>> trace = '''Error: Cannot read property 'x' of undefined
        ...     at processData (app.js:42:10)
        ...     at Object.<anonymous> (app.js:1:1)'''
        >>> frames = parse_javascript_stacktrace(trace)
        >>> len(frames)
        2
        >>> frames[0].function_name
        'processData'
    """
    frames: list[StackFrame] = []

    # Node.js format: at function_name (file.js:line:col)
    node_pattern = r'^\s+at\s+(.+?)\s+\(([^:]+):(\d+):\d+\)$'

    # Browser format: functionName@file.js:line:col
    browser_pattern = r'^([^@]+)@([^:]+):(\d+):\d+$'

    for line in stacktrace.split("\n"):
        # Try Node.js format first
        match = re.match(node_pattern, line)
        if match:
            function_name = match.group(1)
            file_path = match.group(2)
            line_number_str = match.group(3)

            try:
                line_number = int(line_number_str)
                if line_number > 0:
                    frames.append(
                        StackFrame(
                            file_path=file_path,
                            function_name=function_name,
                            line_number=line_number,
                        )
                    )
            except ValueError:
                pass
            continue

        # Try browser format
        match = re.match(browser_pattern, line)
        if match:
            function_name = match.group(1)
            file_path = match.group(2)
            line_number_str = match.group(3)

            try:
                line_number = int(line_number_str)
                if line_number > 0:
                    frames.append(
                        StackFrame(
                            file_path=file_path,
                            function_name=function_name,
                            line_number=line_number,
                        )
                    )
            except ValueError:
                pass

    return frames


def parse_java_stacktrace(stacktrace: str) -> list[StackFrame]:
    """Parse Java stacktrace format.

    Extracts frames from Java exception stacktraces. Handles package-qualified
    class and method names, extracting the filename from the .java extension.
    Native Method and Unknown Source entries are skipped.

    Args:
        stacktrace: Java stacktrace string

    Returns:
        List of StackFrame objects. Empty list if stacktrace is not valid
        Java format.

    Example:
        >>> trace = '''java.lang.NullPointerException
        ...     at com.example.Calculator.divide(Calculator.java:45)
        ...     at com.example.Main.main(Main.java:12)'''
        >>> frames = parse_java_stacktrace(trace)
        >>> len(frames)
        2
        >>> frames[0].function_name
        'divide'
    """
    frames: list[StackFrame] = []

    # Pattern: at package.Class.method(File.java:123) or at package.Class.<init>(File.java:123)
    # Captures: package.Class.method or package.Class.<init>, File.java, line number
    frame_pattern = r'^\s+at\s+([\w.<>]+)\(([^)]+)\)$'

    for line in stacktrace.split("\n"):
        match = re.match(frame_pattern, line)
        if not match:
            continue

        full_path = match.group(1)
        location = match.group(2)

        # Skip Native Method and Unknown Source
        if location in ("Native Method", "Unknown Source"):
            continue

        # Extract filename and line number from location: File.java:123
        location_match = re.match(r'([^:]+):(\d+)', location)
        if not location_match:
            continue

        file_path = location_match.group(1)
        line_number_str = location_match.group(2)

        # Extract method name from full path (last component after final dot)
        method_parts = full_path.split(".")
        if not method_parts:
            continue
        function_name = method_parts[-1]

        try:
            line_number = int(line_number_str)
            if line_number > 0:
                frames.append(
                    StackFrame(
                        file_path=file_path,
                        function_name=function_name,
                        line_number=line_number,
                    )
                )
        except ValueError:
            pass

    return frames


def parse_go_stacktrace(stacktrace: str) -> list[StackFrame]:
    """Parse Go panic stacktrace format.

    Extracts frames from Go panic stacktraces. Handles multiple goroutines
    but only parses the main goroutine (goroutine 1). Skips hex offsets
    (+0x...) in the output.

    Args:
        stacktrace: Go stacktrace string

    Returns:
        List of StackFrame objects. Empty list if stacktrace is not valid
        Go format.

    Example:
        >>> trace = '''panic: runtime error: index out of range [10] with length 5
        ...
        ... goroutine 1 [running]:
        ... main.process()
        ...     /path/to/file.go:42 +0x1c4
        ... main.main()
        ...     /path/to/file.go:15 +0x44'''
        >>> frames = parse_go_stacktrace(trace)
        >>> len(frames)
        2
        >>> frames[0].line_number
        42
    """
    frames: list[StackFrame] = []

    lines = stacktrace.split("\n")

    # Find the main goroutine (goroutine 1)
    main_goroutine_idx = -1
    for i, line in enumerate(lines):
        if "goroutine 1" in line:
            main_goroutine_idx = i
            break

    if main_goroutine_idx < 0:
        return []

    # Process lines starting from main goroutine until next goroutine or end
    i = main_goroutine_idx + 1
    while i < len(lines):
        line = lines[i]

        # Stop if we hit another goroutine
        if "goroutine" in line and i > main_goroutine_idx:
            break

        # Pattern: package.function() or github.com/example/pkg.function()
        # Followed by indented line with path:line +0xoffset
        function_pattern = r'^([\w./]+\.[\w]+)\(\)$'
        func_match = re.match(function_pattern, line)

        if func_match and i + 1 < len(lines):
            full_func_name = func_match.group(1)
            # Extract function name (after the last dot)
            function_name = full_func_name.split(".")[-1]

            next_line = lines[i + 1]
            # Pattern: /path/to/file.go:line +0xoffset (or just /path/to/file.go:line)
            path_pattern = r'^\s+(/[^:]+):(\d+)\s*(\+0x[a-f0-9]+)?$'
            path_match = re.match(path_pattern, next_line)

            if path_match:
                file_path = path_match.group(1)
                line_number_str = path_match.group(2)

                try:
                    line_number = int(line_number_str)
                    if line_number > 0:
                        frames.append(
                            StackFrame(
                                file_path=file_path,
                                function_name=function_name,
                                line_number=line_number,
                            )
                        )
                except ValueError:
                    pass

            i += 2
        else:
            i += 1

    return frames


def normalize_stacktrace(stacktrace: Optional[str | list[str]]) -> Optional[str]:
    """Normalize stacktrace to string format.

    Converts stacktrace from various input formats to a single normalized
    string. List stacktraces are joined with newlines. None input returns None.
    Empty lists return None.

    Args:
        stacktrace: Stacktrace as string, list of strings, or None

    Returns:
        Normalized stacktrace string, or None if input is None or empty list

    Example:
        >>> normalize_stacktrace(["line 1", "line 2", "line 3"])
        'line 1\\nline 2\\nline 3'
        >>> normalize_stacktrace(None)
        None
        >>> normalize_stacktrace([])
        None
    """
    if stacktrace is None:
        return None

    if isinstance(stacktrace, str):
        return stacktrace

    if isinstance(stacktrace, list):
        if not stacktrace:
            return None
        return "\n".join(stacktrace)

    return None
