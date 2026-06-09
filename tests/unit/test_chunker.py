"""Unit tests for indexer/chunker.py."""

import ast

import pytest

from git_debug_oracle.indexer.chunker import (
    calculate_overlap_lines,
    chunk_entire_file,
    chunk_file,
    chunk_function,
    extract_functions,
    get_function_content,
    get_function_lines,
    parse_python_file,
)


def test_parse_python_file_with_valid_code() -> None:
    """Test parse_python_file returns AST for valid Python code."""
    code = "def hello():\n    return 'world'\n"
    result = parse_python_file(code)

    assert result is not None
    assert isinstance(result, ast.Module)


def test_parse_python_file_with_invalid_code() -> None:
    """Test parse_python_file returns None for invalid Python code."""
    code = "def hello(\n    return 'world'\n"
    result = parse_python_file(code)

    assert result is None


def test_parse_python_file_with_empty_code() -> None:
    """Test parse_python_file handles empty code."""
    code = ""
    result = parse_python_file(code)

    assert result is not None
    assert isinstance(result, ast.Module)


def test_extract_functions_with_single_function() -> None:
    """Test extract_functions finds single function."""
    code = "def hello():\n    return 'world'\n"
    tree = parse_python_file(code)
    assert tree is not None

    functions = extract_functions(tree)

    assert len(functions) == 1
    assert functions[0].name == "hello"


def test_extract_functions_with_multiple_functions() -> None:
    """Test extract_functions finds multiple functions."""
    code = """
def hello():
    return 'world'

def goodbye():
    return 'farewell'
"""
    tree = parse_python_file(code)
    assert tree is not None

    functions = extract_functions(tree)

    assert len(functions) == 2
    assert functions[0].name == "hello"
    assert functions[1].name == "goodbye"


def test_extract_functions_with_class_methods() -> None:
    """Test extract_functions finds class methods."""
    code = """
class MyClass:
    def method1(self):
        pass

    def method2(self):
        pass
"""
    tree = parse_python_file(code)
    assert tree is not None

    functions = extract_functions(tree)

    assert len(functions) == 2
    assert functions[0].name == "method1"
    assert functions[1].name == "method2"


def test_extract_functions_with_no_functions() -> None:
    """Test extract_functions returns empty list when no functions."""
    code = "x = 1\ny = 2\n"
    tree = parse_python_file(code)
    assert tree is not None

    functions = extract_functions(tree)

    assert len(functions) == 0


def test_get_function_lines() -> None:
    """Test get_function_lines returns correct line numbers."""
    code = """
def hello():
    return 'world'
"""
    tree = parse_python_file(code)
    assert tree is not None
    functions = extract_functions(tree)
    assert len(functions) == 1

    source_lines = code.splitlines(keepends=True)
    start_line, end_line = get_function_lines(functions[0], source_lines)

    assert start_line == 2
    assert end_line == 3


def test_get_function_content() -> None:
    """Test get_function_content extracts function code."""
    code = """
def hello():
    return 'world'
"""
    tree = parse_python_file(code)
    assert tree is not None
    functions = extract_functions(tree)
    assert len(functions) == 1

    source_lines = code.splitlines(keepends=True)
    content = get_function_content(functions[0], source_lines)

    assert "def hello():" in content
    assert "return 'world'" in content


def test_chunk_function_with_small_function() -> None:
    """Test chunk_function keeps small function as single chunk."""
    code = """
def hello():
    return 'world'
"""
    tree = parse_python_file(code)
    assert tree is not None
    functions = extract_functions(tree)
    assert len(functions) == 1

    source_lines = code.splitlines(keepends=True)
    chunks = chunk_function(functions[0], source_lines, chunk_size=1000, overlap=200)

    assert len(chunks) == 1
    assert chunks[0]["function_name"] == "hello"
    assert chunks[0]["start_line"] == 2
    assert chunks[0]["end_line"] == 3


def test_chunk_function_with_large_function() -> None:
    """Test chunk_function keeps large function as single chunk."""
    code = """
def large_function():
    x = 1
    y = 2
    z = 3
    return x + y + z
"""
    tree = parse_python_file(code)
    assert tree is not None
    functions = extract_functions(tree)
    assert len(functions) == 1

    source_lines = code.splitlines(keepends=True)
    chunks = chunk_function(functions[0], source_lines, chunk_size=10, overlap=5)

    assert len(chunks) == 1
    assert chunks[0]["function_name"] == "large_function"


def test_chunk_file_with_single_function() -> None:
    """Test chunk_file chunks file with single function."""
    code = """
def hello():
    return 'world'
"""
    chunks = chunk_file("test.py", code, chunk_size=1000, overlap=200)

    assert len(chunks) == 1
    assert chunks[0]["function_name"] == "hello"
    assert chunks[0]["start_line"] == 2
    assert chunks[0]["end_line"] == 3


def test_chunk_file_with_multiple_functions() -> None:
    """Test chunk_file chunks file with multiple functions."""
    code = """
def hello():
    return 'world'

def goodbye():
    return 'farewell'
"""
    chunks = chunk_file("test.py", code, chunk_size=1000, overlap=200)

    assert len(chunks) == 2
    assert chunks[0]["function_name"] == "hello"
    assert chunks[1]["function_name"] == "goodbye"


def test_chunk_file_with_invalid_syntax() -> None:
    """Test chunk_file returns error chunk for invalid syntax."""
    code = "def hello(\n    return 'world'\n"
    chunks = chunk_file("test.py", code, chunk_size=1000, overlap=200)

    assert len(chunks) == 1
    assert "error" in chunks[0]
    assert chunks[0]["error"] == "Failed to parse Python file"
    assert chunks[0]["file_path"] == "test.py"


def test_chunk_file_with_no_functions() -> None:
    """Test chunk_file chunks entire file when no functions."""
    code = "x = 1\ny = 2\nz = 3\n"
    chunks = chunk_file("test.py", code, chunk_size=1000, overlap=200)

    assert len(chunks) == 1
    assert chunks[0]["function_name"] is None
    assert chunks[0]["start_line"] == 1


def test_chunk_entire_file_with_small_file() -> None:
    """Test chunk_entire_file keeps small file as single chunk."""
    code = "x = 1\ny = 2\nz = 3\n"
    chunks = chunk_entire_file(code, chunk_size=1000, overlap=200)

    assert len(chunks) == 1
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 3
    assert chunks[0]["function_name"] is None


def test_chunk_entire_file_with_large_file() -> None:
    """Test chunk_entire_file splits large file into multiple chunks."""
    code = "x = 1\n" * 100
    chunks = chunk_entire_file(code, chunk_size=50, overlap=10)

    assert len(chunks) > 1
    assert chunks[0]["start_line"] == 1
    assert chunks[-1]["end_line"] == 100


def test_chunk_entire_file_applies_overlap() -> None:
    """Test chunk_entire_file applies overlap between chunks."""
    code = "line1\nline2\nline3\nline4\nline5\n"
    chunks = chunk_entire_file(code, chunk_size=15, overlap=6)

    assert len(chunks) >= 2


def test_calculate_overlap_lines_with_zero_overlap() -> None:
    """Test calculate_overlap_lines returns empty list for zero overlap."""
    lines = ["line1\n", "line2\n", "line3\n"]
    overlap_lines = calculate_overlap_lines(lines, overlap=0)

    assert overlap_lines == []


def test_calculate_overlap_lines_with_overlap() -> None:
    """Test calculate_overlap_lines returns correct overlap lines."""
    lines = ["line1\n", "line2\n", "line3\n"]
    overlap_lines = calculate_overlap_lines(lines, overlap=6)

    assert len(overlap_lines) == 1
    assert overlap_lines[0] == "line3\n"


def test_calculate_overlap_lines_with_large_overlap() -> None:
    """Test calculate_overlap_lines returns multiple lines for large overlap."""
    lines = ["line1\n", "line2\n", "line3\n"]
    overlap_lines = calculate_overlap_lines(lines, overlap=15)

    assert len(overlap_lines) >= 2
