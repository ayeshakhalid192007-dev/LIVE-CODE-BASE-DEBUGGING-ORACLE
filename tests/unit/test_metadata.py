"""Unit tests for indexer/metadata.py."""

from datetime import datetime

import pytest

from git_debug_oracle.indexer.metadata import extract_chunk_metadata, generate_chunk_id
from git_debug_oracle.types import CodeChunk


def test_generate_chunk_id_is_deterministic() -> None:
    """Test generate_chunk_id produces same ID for same inputs."""
    file_path = "src/module.py"
    start_line = 10
    end_line = 20
    commit_hash = "abc123def456"

    chunk_id_1 = generate_chunk_id(file_path, start_line, end_line, commit_hash)
    chunk_id_2 = generate_chunk_id(file_path, start_line, end_line, commit_hash)

    assert chunk_id_1 == chunk_id_2


def test_generate_chunk_id_differs_for_different_file_paths() -> None:
    """Test generate_chunk_id produces different IDs for different file paths."""
    start_line = 10
    end_line = 20
    commit_hash = "abc123def456"

    chunk_id_1 = generate_chunk_id("src/module1.py", start_line, end_line, commit_hash)
    chunk_id_2 = generate_chunk_id("src/module2.py", start_line, end_line, commit_hash)

    assert chunk_id_1 != chunk_id_2


def test_generate_chunk_id_differs_for_different_line_ranges() -> None:
    """Test generate_chunk_id produces different IDs for different line ranges."""
    file_path = "src/module.py"
    commit_hash = "abc123def456"

    chunk_id_1 = generate_chunk_id(file_path, 10, 20, commit_hash)
    chunk_id_2 = generate_chunk_id(file_path, 30, 40, commit_hash)

    assert chunk_id_1 != chunk_id_2


def test_generate_chunk_id_differs_for_different_commits() -> None:
    """Test generate_chunk_id produces different IDs for different commits."""
    file_path = "src/module.py"
    start_line = 10
    end_line = 20

    chunk_id_1 = generate_chunk_id(file_path, start_line, end_line, "abc123def456")
    chunk_id_2 = generate_chunk_id(file_path, start_line, end_line, "xyz789ghi012")

    assert chunk_id_1 != chunk_id_2


def test_generate_chunk_id_returns_sha256_hash() -> None:
    """Test generate_chunk_id returns SHA256 hash (64 hex characters)."""
    file_path = "src/module.py"
    start_line = 10
    end_line = 20
    commit_hash = "abc123def456"

    chunk_id = generate_chunk_id(file_path, start_line, end_line, commit_hash)

    assert len(chunk_id) == 64
    assert all(c in "0123456789abcdef" for c in chunk_id)


def test_extract_chunk_metadata_creates_code_chunk() -> None:
    """Test extract_chunk_metadata creates CodeChunk with all fields."""
    chunk_dict = {
        "content": "def hello():\n    return 'world'\n",
        "start_line": 10,
        "end_line": 11,
        "function_name": "hello",
    }
    file_path = "src/module.py"
    commit_metadata = {
        "hash": "abc123def456",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    chunk = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)

    assert isinstance(chunk, CodeChunk)
    assert chunk.content == "def hello():\n    return 'world'\n"
    assert chunk.file_path == "src/module.py"
    assert chunk.start_line == 10
    assert chunk.end_line == 11
    assert chunk.commit_hash == "abc123def456"
    assert chunk.commit_author == "Test User"
    assert chunk.function_name == "hello"
    assert chunk.embedding is None


def test_extract_chunk_metadata_parses_timestamp() -> None:
    """Test extract_chunk_metadata parses ISO timestamp correctly."""
    chunk_dict = {
        "content": "x = 1",
        "start_line": 1,
        "end_line": 1,
        "function_name": None,
    }
    file_path = "src/module.py"
    commit_metadata = {
        "hash": "abc123def456",
        "author": "Test User",
        "timestamp": "2026-05-29T12:30:45",
        "message": "Test commit",
    }

    chunk = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)

    assert isinstance(chunk.commit_timestamp, datetime)
    assert chunk.commit_timestamp.year == 2026
    assert chunk.commit_timestamp.month == 5
    assert chunk.commit_timestamp.day == 29
    assert chunk.commit_timestamp.hour == 12
    assert chunk.commit_timestamp.minute == 30
    assert chunk.commit_timestamp.second == 45


def test_extract_chunk_metadata_generates_chunk_id() -> None:
    """Test extract_chunk_metadata generates deterministic chunk_id."""
    chunk_dict = {
        "content": "def hello():\n    return 'world'\n",
        "start_line": 10,
        "end_line": 11,
        "function_name": "hello",
    }
    file_path = "src/module.py"
    commit_metadata = {
        "hash": "abc123def456",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    chunk = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)

    assert chunk.chunk_id is not None
    assert len(chunk.chunk_id) == 64


def test_extract_chunk_metadata_with_none_function_name() -> None:
    """Test extract_chunk_metadata handles None function_name."""
    chunk_dict = {
        "content": "x = 1\ny = 2\n",
        "start_line": 1,
        "end_line": 2,
        "function_name": None,
    }
    file_path = "src/module.py"
    commit_metadata = {
        "hash": "abc123def456",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    chunk = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)

    assert chunk.function_name is None


def test_extract_chunk_metadata_with_missing_function_name_key() -> None:
    """Test extract_chunk_metadata handles missing function_name key."""
    chunk_dict = {
        "content": "x = 1\ny = 2\n",
        "start_line": 1,
        "end_line": 2,
    }
    file_path = "src/module.py"
    commit_metadata = {
        "hash": "abc123def456",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    chunk = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)

    assert chunk.function_name is None


def test_extract_chunk_metadata_consistency() -> None:
    """Test extract_chunk_metadata produces consistent results."""
    chunk_dict = {
        "content": "def hello():\n    return 'world'\n",
        "start_line": 10,
        "end_line": 11,
        "function_name": "hello",
    }
    file_path = "src/module.py"
    commit_metadata = {
        "hash": "abc123def456",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    chunk1 = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)
    chunk2 = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)

    assert chunk1.chunk_id == chunk2.chunk_id
    assert chunk1.content == chunk2.content
    assert chunk1.file_path == chunk2.file_path
    assert chunk1.start_line == chunk2.start_line
    assert chunk1.end_line == chunk2.end_line
    assert chunk1.commit_hash == chunk2.commit_hash
