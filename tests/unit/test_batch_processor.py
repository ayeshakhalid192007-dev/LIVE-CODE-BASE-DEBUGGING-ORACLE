"""Unit tests for embedder/batch_processor.py."""

from datetime import datetime
from unittest.mock import Mock

import pytest

from git_debug_oracle.embedder.batch_processor import batch_embed
from git_debug_oracle.types import CodeChunk


@pytest.fixture
def sample_chunks() -> list[CodeChunk]:
    """Create sample CodeChunk objects for testing.

    Returns:
        List of CodeChunk instances
    """
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunks = [
        CodeChunk(
            content="def hello():\n    return 'world'",
            file_path="src/module1.py",
            start_line=1,
            end_line=2,
            commit_hash="abc123",
            commit_author="Test User",
            commit_timestamp=timestamp,
            function_name="hello",
            embedding=None,
            chunk_id="chunk1",
        ),
        CodeChunk(
            content="def goodbye():\n    return 'farewell'",
            file_path="src/module2.py",
            start_line=5,
            end_line=6,
            commit_hash="abc123",
            commit_author="Test User",
            commit_timestamp=timestamp,
            function_name="goodbye",
            embedding=None,
            chunk_id="chunk2",
        ),
    ]
    return chunks


@pytest.fixture
def mock_embedder() -> Mock:
    """Create a mock embedder.

    Returns:
        Mock embedder instance
    """
    mock = Mock()
    mock.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]
    return mock


def test_batch_embed_with_empty_chunks() -> None:
    """Test batch_embed handles empty chunk list."""
    mock_embedder = Mock()

    result = batch_embed([], mock_embedder)

    assert result == []
    mock_embedder.embed_batch.assert_not_called()


def test_batch_embed_attaches_embeddings(sample_chunks: list[CodeChunk]) -> None:
    """Test batch_embed attaches embeddings to chunks."""
    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]

    result = batch_embed(sample_chunks, mock_embedder)

    assert len(result) == 2
    assert result[0].embedding == [0.1] * 1536
    assert result[1].embedding == [0.2] * 1536


def test_batch_embed_preserves_chunk_data(sample_chunks: list[CodeChunk]) -> None:
    """Test batch_embed preserves all chunk data."""
    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]

    result = batch_embed(sample_chunks, mock_embedder)

    assert result[0].content == sample_chunks[0].content
    assert result[0].file_path == sample_chunks[0].file_path
    assert result[0].start_line == sample_chunks[0].start_line
    assert result[0].end_line == sample_chunks[0].end_line
    assert result[0].commit_hash == sample_chunks[0].commit_hash
    assert result[0].commit_author == sample_chunks[0].commit_author
    assert result[0].function_name == sample_chunks[0].function_name
    assert result[0].chunk_id == sample_chunks[0].chunk_id


def test_batch_embed_batches_correctly() -> None:
    """Test batch_embed batches chunks into groups of 100."""
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunks = [
        CodeChunk(
            content=f"def func_{i}(): pass",
            file_path=f"src/module_{i}.py",
            start_line=i,
            end_line=i + 1,
            commit_hash="abc123",
            commit_author="Test User",
            commit_timestamp=timestamp,
            function_name=f"func_{i}",
            embedding=None,
            chunk_id=f"chunk_{i}",
        )
        for i in range(250)
    ]

    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536 for _ in range(250)]

    batch_embed(chunks, mock_embedder)

    assert mock_embedder.embed_batch.call_count == 3


def test_batch_embed_calls_embed_with_texts(sample_chunks: list[CodeChunk]) -> None:
    """Test batch_embed calls embedder with correct texts."""
    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]

    batch_embed(sample_chunks, mock_embedder)

    mock_embedder.embed_batch.assert_called_once()
    call_args = mock_embedder.embed_batch.call_args[0][0]
    assert len(call_args) == 2
    assert call_args[0] == sample_chunks[0].content
    assert call_args[1] == sample_chunks[1].content


def test_batch_embed_returns_code_chunks(sample_chunks: list[CodeChunk]) -> None:
    """Test batch_embed returns CodeChunk instances."""
    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]

    result = batch_embed(sample_chunks, mock_embedder)

    assert all(isinstance(chunk, CodeChunk) for chunk in result)


def test_batch_embed_with_single_chunk() -> None:
    """Test batch_embed with single chunk."""
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunks = [
        CodeChunk(
            content="def hello(): pass",
            file_path="src/module.py",
            start_line=1,
            end_line=1,
            commit_hash="abc123",
            commit_author="Test User",
            commit_timestamp=timestamp,
            function_name="hello",
            embedding=None,
            chunk_id="chunk1",
        )
    ]

    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536]

    result = batch_embed(chunks, mock_embedder)

    assert len(result) == 1
    assert result[0].embedding == [0.1] * 1536
    mock_embedder.embed_batch.assert_called_once()


def test_batch_embed_maintains_chunk_order(sample_chunks: list[CodeChunk]) -> None:
    """Test batch_embed maintains order of chunks."""
    mock_embedder = Mock()
    mock_embedder.embed_batch.return_value = [[0.1] * 1536, [0.2] * 1536]

    result = batch_embed(sample_chunks, mock_embedder)

    assert result[0].chunk_id == "chunk1"
    assert result[1].chunk_id == "chunk2"
    assert result[0].function_name == "hello"
    assert result[1].function_name == "goodbye"
