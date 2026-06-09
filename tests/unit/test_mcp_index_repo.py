"""Unit tests for mcp_tools/index_repo.py."""

from unittest.mock import Mock, patch

import pytest

from git_debug_oracle.mcp_tools.index_repo import index_repo, index_incremental


@pytest.fixture
def mock_config() -> Mock:
    """Create a mock Config instance.

    Returns:
        Mock Config instance
    """
    config = Mock()
    config.repo_path = "/test/repo"
    config.watch_branch = "main"
    config.chunk_size = 1000
    config.chunk_overlap = 200
    config.embedding_api_key = "test_key"
    config.qdrant_collection = "test_collection"
    return config


@pytest.fixture
def mock_qdrant_wrapper() -> Mock:
    """Create a mock Qdrant wrapper.

    Returns:
        Mock Qdrant wrapper instance
    """
    return Mock()


@pytest.fixture
def mock_embedder() -> Mock:
    """Create a mock embedder.

    Returns:
        Mock embedder instance
    """
    return Mock()


def test_index_repo_success(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_repo returns success result."""
    with patch("git_debug_oracle.mcp_tools.index_repo.IndexingPipeline") as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_status = Mock()
        mock_status.total_chunks = 10
        mock_status.total_files = 2
        mock_status.last_indexed_commit = "abc123"
        mock_status.last_indexed_timestamp = Mock()

        mock_pipeline.index_commit.return_value = mock_status

        result = index_repo(
            repo_path="/test/repo",
            commit_hash="abc123",
            branch="main",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )

        assert result["status"] == "success"
        assert result["chunks_indexed"] == 10
        assert result["files_processed"] == 2
        assert result["error_message"] is None


def test_index_repo_uses_defaults(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_repo uses config defaults."""
    with patch("git_debug_oracle.mcp_tools.index_repo.IndexingPipeline") as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_status = Mock()
        mock_status.total_chunks = 0
        mock_status.total_files = 0
        mock_status.last_indexed_commit = "HEAD"
        mock_status.last_indexed_timestamp = Mock()

        mock_pipeline.index_commit.return_value = mock_status

        result = index_repo(
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )

        assert result["status"] == "success"
        mock_pipeline.index_commit.assert_called_once()
        call_args = mock_pipeline.index_commit.call_args
        assert call_args[0][0] == "/test/repo"
        assert call_args[0][2] == "main"


def test_index_repo_with_commit_range(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_repo with commit range."""
    with patch("git_debug_oracle.mcp_tools.index_repo.IndexingPipeline") as mock_pipeline_class:
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline

        mock_status = Mock()
        mock_status.total_chunks = 20
        mock_status.total_files = 5
        mock_status.last_indexed_commit = "def456"
        mock_status.last_indexed_timestamp = Mock()

        mock_pipeline.index_commit_range.return_value = mock_status

        result = index_repo(
            repo_path="/test/repo",
            commit_range=("abc123", "def456"),
            branch="main",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )

        assert result["status"] == "success"
        assert result["chunks_indexed"] == 20
        mock_pipeline.index_commit_range.assert_called_once()


def test_index_repo_error_handling(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_repo error handling."""
    with patch("git_debug_oracle.mcp_tools.index_repo.IndexingPipeline") as mock_pipeline_class:
        mock_pipeline_class.side_effect = Exception("Index failed")

        result = index_repo(
            repo_path="/test/repo",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )

        assert result["status"] == "error"
        assert "Index failed" in result["error_message"]
        assert result["chunks_indexed"] == 0


def test_index_incremental_success(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_incremental returns success result."""
    with patch("git_debug_oracle.mcp_tools.index_repo.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_last_indexed_commit.return_value = "abc123"

        with patch("git_debug_oracle.mcp_tools.index_repo.IndexingPipeline") as mock_pipeline_class:
            mock_pipeline = Mock()
            mock_pipeline_class.return_value = mock_pipeline

            mock_status = Mock()
            mock_status.total_chunks = 5
            mock_status.total_files = 1
            mock_status.last_indexed_commit = "def456"
            mock_status.last_indexed_timestamp = Mock()

            mock_pipeline.index_commit_range.return_value = mock_status

            result = index_incremental(
                repo_path="/test/repo",
                branch="main",
                config=mock_config,
                qdrant_wrapper=mock_qdrant_wrapper,
                embedder=mock_embedder,
            )

            assert result["status"] == "success"
            assert result["chunks_indexed"] == 5


def test_index_incremental_falls_back_to_full_index(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_incremental falls back to full index when no prior index."""
    with patch("git_debug_oracle.mcp_tools.index_repo.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_last_indexed_commit.return_value = None

        with patch("git_debug_oracle.mcp_tools.index_repo.index_repo") as mock_index_repo:
            mock_index_repo.return_value = {"status": "success"}

            result = index_incremental(
                repo_path="/test/repo",
                branch="main",
                config=mock_config,
                qdrant_wrapper=mock_qdrant_wrapper,
                embedder=mock_embedder,
            )

            assert result["status"] == "success"
            mock_index_repo.assert_called_once()


def test_index_incremental_error_handling(
    mock_config: Mock, mock_qdrant_wrapper: Mock, mock_embedder: Mock
) -> None:
    """Test index_incremental error handling."""
    with patch("git_debug_oracle.mcp_tools.index_repo.CommitTracker") as mock_tracker_class:
        mock_tracker_class.side_effect = Exception("Tracker failed")

        result = index_incremental(
            repo_path="/test/repo",
            branch="main",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
            embedder=mock_embedder,
        )

        assert result["status"] == "error"
        assert "Tracker failed" in result["error_message"]
