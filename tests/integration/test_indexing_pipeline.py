"""Integration tests for indexing pipeline."""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock

import pytest
from git import Repo

from git_debug_oracle.indexer.pipeline import IndexingPipeline
from git_debug_oracle.types import CodeChunk


@pytest.fixture
def temp_test_repo(tmp_path: Path) -> str:
    """Create a temporary test repository.

    Args:
        tmp_path: Pytest temporary directory

    Returns:
        Absolute path to test repository
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    repo = Repo.init(repo_path)
    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    file1 = repo_path / "module1.py"
    file1.write_text("def function1():\n    return 'result1'\n")
    repo.index.add(["module1.py"])
    repo.index.commit("Initial commit")

    file2 = repo_path / "module2.py"
    file2.write_text("def function2():\n    return 'result2'\n")
    repo.index.add(["module2.py"])
    repo.index.commit("Add module2")

    return str(repo_path)


@pytest.fixture
def mock_embedder() -> Mock:
    """Create a mock embedder.

    Returns:
        Mock embedder instance
    """
    mock = Mock()
    mock.embed_batch.return_value = [[0.1] * 1536 for _ in range(100)]
    return mock


@pytest.fixture
def mock_qdrant_wrapper() -> Mock:
    """Create a mock Qdrant wrapper.

    Returns:
        Mock Qdrant wrapper instance
    """
    mock = Mock()
    mock.collection_name = "test_collection"
    mock.create_collection_if_missing = Mock()
    mock.upsert_chunks = Mock()
    return mock


def test_indexing_pipeline_initialization(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test IndexingPipeline initializes correctly."""
    pipeline = IndexingPipeline(
        mock_qdrant_wrapper,
        mock_embedder,
        chunk_size=1000,
        chunk_overlap=200,
    )

    assert pipeline.chunk_size == 1000
    assert pipeline.chunk_overlap == 200
    assert pipeline.qdrant == mock_qdrant_wrapper
    assert pipeline.embedder == mock_embedder


def test_process_files_filters_non_python_files(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test _process_files skips non-Python files."""
    pipeline = IndexingPipeline(mock_qdrant_wrapper, mock_embedder)

    files_data = [
        ("module.py", "def hello(): pass"),
        ("file.txt", "Not Python"),
        ("script.py", "def goodbye(): pass"),
    ]

    commit_metadata = {
        "hash": "abc123",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        chunks = pipeline._process_files(files_data, tmpdir, commit_metadata)

    assert len(chunks) == 2
    assert all(isinstance(c, CodeChunk) for c in chunks)


def test_process_files_generates_chunks(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test _process_files generates CodeChunk objects."""
    pipeline = IndexingPipeline(mock_qdrant_wrapper, mock_embedder)

    files_data = [
        ("module.py", "def hello():\n    return 'world'\n"),
    ]

    commit_metadata = {
        "hash": "abc123",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        chunks = pipeline._process_files(files_data, tmpdir, commit_metadata)

    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.file_path == "module.py"
    assert chunk.commit_hash == "abc123"
    assert chunk.commit_author == "Test User"


def test_process_files_preserves_metadata(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test _process_files preserves chunk metadata."""
    pipeline = IndexingPipeline(mock_qdrant_wrapper, mock_embedder)

    files_data = [
        ("module.py", "def hello():\n    return 'world'\n"),
    ]

    commit_metadata = {
        "hash": "abc123def456",
        "author": "Alice Developer",
        "timestamp": "2026-05-29T14:30:00",
        "message": "Feature: add hello function",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        chunks = pipeline._process_files(files_data, tmpdir, commit_metadata)

    assert len(chunks) >= 1
    chunk = chunks[0]
    assert chunk.commit_hash == "abc123def456"
    assert chunk.commit_author == "Alice Developer"
    assert chunk.file_path == "module.py"


def test_process_files_with_empty_files_list(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test _process_files handles empty files list."""
    pipeline = IndexingPipeline(mock_qdrant_wrapper, mock_embedder)

    files_data: list = []

    commit_metadata = {
        "hash": "abc123",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        chunks = pipeline._process_files(files_data, tmpdir, commit_metadata)

    assert chunks == []


def test_process_files_generates_deterministic_chunk_ids(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test _process_files generates deterministic chunk IDs."""
    pipeline = IndexingPipeline(mock_qdrant_wrapper, mock_embedder)

    files_data = [
        ("module.py", "def hello():\n    return 'world'\n"),
    ]

    commit_metadata = {
        "hash": "abc123",
        "author": "Test User",
        "timestamp": "2026-05-29T12:00:00",
        "message": "Test commit",
    }

    with tempfile.TemporaryDirectory() as tmpdir:
        chunks1 = pipeline._process_files(files_data, tmpdir, commit_metadata)
        chunks2 = pipeline._process_files(files_data, tmpdir, commit_metadata)

    assert len(chunks1) == len(chunks2)
    for c1, c2 in zip(chunks1, chunks2):
        assert c1.chunk_id == c2.chunk_id


def test_check_memory_usage_does_not_raise(
    mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test _check_memory_usage does not raise exceptions."""
    pipeline = IndexingPipeline(mock_qdrant_wrapper, mock_embedder)

    pipeline._check_memory_usage()
