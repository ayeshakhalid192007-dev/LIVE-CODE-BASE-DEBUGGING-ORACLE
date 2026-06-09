"""Unit tests for indexer/file_filter.py."""

import tempfile
from pathlib import Path

import pytest

from git_debug_oracle.indexer.file_filter import (
    get_gitignore_patterns,
    has_python_extension,
    is_binary_file,
    is_file_too_large,
    matches_gitignore,
    matches_pattern,
    should_index_file,
    should_index_file_with_gitignore,
)


def test_has_python_extension_with_py_file() -> None:
    """Test has_python_extension returns True for .py files."""
    assert has_python_extension("test.py") is True
    assert has_python_extension("src/module/test.py") is True
    assert has_python_extension("path/to/file.py") is True


def test_has_python_extension_with_non_py_file() -> None:
    """Test has_python_extension returns False for non-.py files."""
    assert has_python_extension("test.txt") is False
    assert has_python_extension("test.js") is False
    assert has_python_extension("test.pyc") is False
    assert has_python_extension("test") is False


def test_is_binary_file_with_text_content() -> None:
    """Test is_binary_file returns False for text content."""
    text_content = "def hello():\n    return 'world'\n"
    assert is_binary_file(text_content) is False


def test_is_binary_file_with_binary_content() -> None:
    """Test is_binary_file returns True for binary content."""
    binary_content = "def hello():\x00\n    return 'world'\n"
    assert is_binary_file(binary_content) is True


def test_is_file_too_large_with_small_file() -> None:
    """Test is_file_too_large returns False for small files."""
    small_content = "def hello():\n    return 'world'\n" * 100
    assert is_file_too_large(small_content) is False


def test_is_file_too_large_with_large_file() -> None:
    """Test is_file_too_large returns True for files over 1MB."""
    large_content = "x" * (1_048_577)
    assert is_file_too_large(large_content) is True


def test_is_file_too_large_at_boundary() -> None:
    """Test is_file_too_large at exactly 1MB boundary."""
    boundary_content = "x" * 1_048_576
    assert is_file_too_large(boundary_content) is False

    over_boundary_content = "x" * 1_048_577
    assert is_file_too_large(over_boundary_content) is True


def test_should_index_file_with_valid_python_file() -> None:
    """Test should_index_file returns True for valid Python files."""
    file_path = "test.py"
    file_content = "def hello():\n    return 'world'\n"
    assert should_index_file(file_path, file_content) is True


def test_should_index_file_with_non_python_file() -> None:
    """Test should_index_file returns False for non-Python files."""
    file_path = "test.txt"
    file_content = "Hello world"
    assert should_index_file(file_path, file_content) is False


def test_should_index_file_with_binary_file() -> None:
    """Test should_index_file returns False for binary files."""
    file_path = "test.py"
    file_content = "def hello():\x00\n    return 'world'\n"
    assert should_index_file(file_path, file_content) is False


def test_should_index_file_with_large_file() -> None:
    """Test should_index_file returns False for large files."""
    file_path = "test.py"
    file_content = "x" * (1_048_577)
    assert should_index_file(file_path, file_content) is False


def test_get_gitignore_patterns_with_no_gitignore(tmp_path: Path) -> None:
    """Test get_gitignore_patterns returns empty list when no .gitignore exists."""
    patterns = get_gitignore_patterns(str(tmp_path))
    assert patterns == []


def test_get_gitignore_patterns_with_gitignore(tmp_path: Path) -> None:
    """Test get_gitignore_patterns loads patterns from .gitignore."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.pyc\n__pycache__/\n.env\n")

    patterns = get_gitignore_patterns(str(tmp_path))

    assert len(patterns) == 3
    assert "*.pyc" in patterns
    assert "__pycache__/" in patterns
    assert ".env" in patterns


def test_get_gitignore_patterns_ignores_comments(tmp_path: Path) -> None:
    """Test get_gitignore_patterns ignores comment lines."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("# Comment\n*.pyc\n# Another comment\n__pycache__/\n")

    patterns = get_gitignore_patterns(str(tmp_path))

    assert len(patterns) == 2
    assert "*.pyc" in patterns
    assert "__pycache__/" in patterns


def test_get_gitignore_patterns_ignores_empty_lines(tmp_path: Path) -> None:
    """Test get_gitignore_patterns ignores empty lines."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.pyc\n\n__pycache__/\n\n")

    patterns = get_gitignore_patterns(str(tmp_path))

    assert len(patterns) == 2
    assert "*.pyc" in patterns
    assert "__pycache__/" in patterns


def test_matches_pattern_with_wildcard() -> None:
    """Test matches_pattern with wildcard patterns."""
    assert matches_pattern("test.pyc", "*.pyc") is True
    assert matches_pattern("module.pyc", "*.pyc") is True
    assert matches_pattern("test.py", "*.pyc") is False


def test_matches_pattern_with_directory() -> None:
    """Test matches_pattern with directory patterns."""
    assert matches_pattern("__pycache__/test.pyc", "__pycache__/") is True
    assert matches_pattern("__pycache__/module/test.pyc", "__pycache__/") is True
    assert matches_pattern("src/__pycache__/test.pyc", "__pycache__/") is False


def test_matches_pattern_with_path() -> None:
    """Test matches_pattern with path patterns."""
    assert matches_pattern("src/test.py", "src/*.py") is True
    assert matches_pattern("src/module.py", "src/*.py") is True
    assert matches_pattern("tests/test.py", "src/*.py") is False


def test_matches_pattern_with_question_mark() -> None:
    """Test matches_pattern with question mark wildcard."""
    assert matches_pattern("test1.py", "test?.py") is True
    assert matches_pattern("test2.py", "test?.py") is True
    assert matches_pattern("test12.py", "test?.py") is False


def test_matches_gitignore_with_matching_pattern() -> None:
    """Test matches_gitignore returns True for matching patterns."""
    patterns = ["*.pyc", "__pycache__/", ".env"]
    assert matches_gitignore("test.pyc", patterns) is True
    assert matches_gitignore("__pycache__/test.pyc", patterns) is True
    assert matches_gitignore(".env", patterns) is True


def test_matches_gitignore_with_non_matching_pattern() -> None:
    """Test matches_gitignore returns False for non-matching patterns."""
    patterns = ["*.pyc", "__pycache__/", ".env"]
    assert matches_gitignore("test.py", patterns) is False
    assert matches_gitignore("src/module.py", patterns) is False


def test_matches_gitignore_with_empty_patterns() -> None:
    """Test matches_gitignore returns False with empty pattern list."""
    assert matches_gitignore("test.py", []) is False
    assert matches_gitignore("test.pyc", []) is False


def test_should_index_file_with_gitignore_accepts_valid_file(tmp_path: Path) -> None:
    """Test should_index_file_with_gitignore accepts valid Python files."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.pyc\n")

    file_path = "test.py"
    file_content = "def hello():\n    return 'world'\n"

    assert should_index_file_with_gitignore(file_path, file_content, str(tmp_path)) is True


def test_should_index_file_with_gitignore_rejects_ignored_file(tmp_path: Path) -> None:
    """Test should_index_file_with_gitignore rejects gitignored files."""
    gitignore_path = tmp_path / ".gitignore"
    gitignore_path.write_text("*.pyc\n")

    file_path = "test.pyc"
    file_content = "binary content"

    assert should_index_file_with_gitignore(file_path, file_content, str(tmp_path)) is False


def test_should_index_file_with_gitignore_rejects_non_python_file(tmp_path: Path) -> None:
    """Test should_index_file_with_gitignore rejects non-Python files."""
    file_path = "test.txt"
    file_content = "Hello world"

    assert should_index_file_with_gitignore(file_path, file_content, str(tmp_path)) is False


def test_should_index_file_with_gitignore_rejects_binary_file(tmp_path: Path) -> None:
    """Test should_index_file_with_gitignore rejects binary files."""
    file_path = "test.py"
    file_content = "def hello():\x00\n    return 'world'\n"

    assert should_index_file_with_gitignore(file_path, file_content, str(tmp_path)) is False


def test_should_index_file_with_gitignore_rejects_large_file(tmp_path: Path) -> None:
    """Test should_index_file_with_gitignore rejects large files."""
    file_path = "test.py"
    file_content = "x" * (1_048_577)

    assert should_index_file_with_gitignore(file_path, file_content, str(tmp_path)) is False
