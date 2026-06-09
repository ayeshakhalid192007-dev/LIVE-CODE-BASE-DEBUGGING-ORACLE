"""Unit tests for utils/qdrant_client.py collection management."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from git_debug_oracle.config import Config
from git_debug_oracle.types import CodeChunk
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper


@pytest.fixture
def mock_config() -> Config:
    """Create a mock Config instance.

    Returns:
        Mock Config instance
    """
    config = Mock(spec=Config)
    config.qdrant_host = "localhost"
    config.qdrant_port = 6333
    config.qdrant_collection = "test_collection"
    config.qdrant_api_key = None
    return config


@pytest.fixture
def mock_qdrant_wrapper(mock_config: Config) -> QdrantClientWrapper:
    """Create a QdrantClientWrapper with mocked client.

    Args:
        mock_config: Mock Config instance

    Returns:
        QdrantClientWrapper instance
    """
    wrapper = Mock(spec=QdrantClientWrapper)
    wrapper._client = MagicMock()
    wrapper.client = wrapper._client
    wrapper._config = mock_config
    wrapper.config = mock_config
    wrapper._qdrant = wrapper
    wrapper.collection_name = "test_collection"
    wrapper.create_collection_if_missing = QdrantClientWrapper.create_collection_if_missing.__get__(wrapper)
    wrapper.delete_chunks_by_file = QdrantClientWrapper.delete_chunks_by_file.__get__(wrapper)
    wrapper.upsert_chunks = QdrantClientWrapper.upsert_chunks.__get__(wrapper)
    wrapper.get_collection_info = QdrantClientWrapper.get_collection_info.__get__(wrapper)
    wrapper._chunks_to_points = QdrantClientWrapper._chunks_to_points.__get__(wrapper)
    wrapper._build_file_selector = QdrantClientWrapper._build_file_selector.__get__(wrapper)
    return wrapper


def test_create_collection_if_missing_creates_new_collection(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test create_collection_if_missing creates collection when missing."""
    mock_qdrant_wrapper.client.get_collection.side_effect = Exception("Collection not found")

    mock_qdrant_wrapper.create_collection_if_missing("test_collection", vector_dim=1536)

    mock_qdrant_wrapper.client.create_collection.assert_called_once()


def test_create_collection_if_missing_skips_existing_collection(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test create_collection_if_missing skips existing collection."""
    mock_qdrant_wrapper.client.get_collection.return_value = Mock()

    mock_qdrant_wrapper.create_collection_if_missing("test_collection", vector_dim=1536)

    mock_qdrant_wrapper.client.create_collection.assert_not_called()


def test_delete_chunks_by_file_calls_delete(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test delete_chunks_by_file calls Qdrant delete."""
    mock_qdrant_wrapper.delete_chunks_by_file("src/module.py", "abc123")

    mock_qdrant_wrapper.client.delete.assert_called_once()


def test_upsert_chunks_with_empty_list(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test upsert_chunks handles empty chunk list."""
    mock_qdrant_wrapper.upsert_chunks([])

    mock_qdrant_wrapper.client.upsert.assert_not_called()


def test_upsert_chunks_converts_chunks_to_points(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test upsert_chunks converts CodeChunk to PointStruct."""
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunk = CodeChunk(
        content="def hello(): pass",
        file_path="src/module.py",
        start_line=1,
        end_line=1,
        commit_hash="abc123",
        commit_author="Test User",
        commit_timestamp=timestamp,
        function_name="hello",
        embedding=[0.1] * 1536,
        chunk_id="a" * 64,
    )

    mock_qdrant_wrapper.upsert_chunks([chunk])

    mock_qdrant_wrapper.client.upsert.assert_called_once()
    call_kwargs = mock_qdrant_wrapper.client.upsert.call_args.kwargs
    assert call_kwargs["collection_name"] == "test_collection"
    assert len(call_kwargs["points"]) == 1


def test_upsert_chunks_retries_on_failure(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test upsert_chunks retries on failure."""
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunk = CodeChunk(
        content="def hello(): pass",
        file_path="src/module.py",
        start_line=1,
        end_line=1,
        commit_hash="abc123",
        commit_author="Test User",
        commit_timestamp=timestamp,
        function_name="hello",
        embedding=[0.1] * 1536,
        chunk_id="a" * 64,
    )

    mock_qdrant_wrapper.client.upsert.side_effect = [
        Exception("Network error"),
        Exception("Timeout"),
        None,
    ]

    with patch("git_debug_oracle.utils.qdrant_client.time.sleep"):
        mock_qdrant_wrapper.upsert_chunks([chunk])

    assert mock_qdrant_wrapper.client.upsert.call_count == 3


def test_upsert_chunks_fails_after_retries(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test upsert_chunks raises exception after all retries fail."""
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunk = CodeChunk(
        content="def hello(): pass",
        file_path="src/module.py",
        start_line=1,
        end_line=1,
        commit_hash="abc123",
        commit_author="Test User",
        commit_timestamp=timestamp,
        function_name="hello",
        embedding=[0.1] * 1536,
        chunk_id="a" * 64,
    )

    mock_qdrant_wrapper.client.upsert.side_effect = Exception("Persistent error")

    with patch("git_debug_oracle.utils.qdrant_client.time.sleep"):
        with pytest.raises(Exception, match="Failed to upsert chunks after 3 retries"):
            mock_qdrant_wrapper.upsert_chunks([chunk])


def test_get_collection_info_returns_dict(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_collection_info returns collection information."""
    mock_collection = Mock()
    mock_collection.points_count = 100
    mock_collection.vectors_count = 100
    mock_qdrant_wrapper.client.get_collection.return_value = mock_collection

    info = mock_qdrant_wrapper.get_collection_info("test_collection")

    assert isinstance(info, dict)
    assert info["name"] == "test_collection"
    assert info["points_count"] == 100
    assert info["vectors_count"] == 100


def test_chunks_to_points_creates_points(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test _chunks_to_points converts CodeChunk to PointStruct."""
    timestamp = datetime(2026, 5, 29, 12, 0, 0)
    chunk = CodeChunk(
        content="def hello(): pass",
        file_path="src/module.py",
        start_line=1,
        end_line=1,
        commit_hash="abc123",
        commit_author="Test User",
        commit_timestamp=timestamp,
        function_name="hello",
        embedding=[0.1] * 1536,
        chunk_id="a" * 64,
    )

    points = mock_qdrant_wrapper._chunks_to_points([chunk])

    assert len(points) == 1
    assert points[0].payload["file_path"] == "src/module.py"
    assert points[0].payload["function_name"] == "hello"
    assert points[0].payload["chunk_id"] == "a" * 64
