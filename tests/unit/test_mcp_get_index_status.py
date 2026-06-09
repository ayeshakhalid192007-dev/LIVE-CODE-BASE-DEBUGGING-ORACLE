"""Unit tests for mcp_tools/get_index_status.py."""

from unittest.mock import Mock, patch

import pytest

from git_debug_oracle.mcp_tools.get_index_status import (
    get_index_status,
    get_all_indexed_branches,
)


@pytest.fixture
def mock_config() -> Mock:
    """Create a mock Config instance.

    Returns:
        Mock Config instance
    """
    config = Mock()
    config.repo_path = "/test/repo"
    config.watch_branch = "main"
    config.qdrant_collection = "test_collection"
    return config


@pytest.fixture
def mock_qdrant_wrapper() -> Mock:
    """Create a mock Qdrant wrapper.

    Returns:
        Mock Qdrant wrapper instance
    """
    return Mock()


def test_get_index_status_indexed(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_index_status returns status when indexed."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_last_indexed_commit.return_value = "abc123"

        mock_qdrant_wrapper.get_collection_info.return_value = {
            "name": "test_collection",
            "points_count": 100,
            "vectors_count": 100,
        }

        result = get_index_status(
            repo_path="/test/repo",
            branch="main",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "indexed"
        assert result["last_indexed_commit"] == "abc123"
        assert result["total_chunks"] == 100


def test_get_index_status_not_indexed(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_index_status returns not_indexed when no prior index."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_last_indexed_commit.return_value = None

        result = get_index_status(
            repo_path="/test/repo",
            branch="main",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "not_indexed"
        assert result["last_indexed_commit"] is None
        assert result["total_chunks"] == 0


def test_get_index_status_uses_defaults(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_index_status uses config defaults."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_last_indexed_commit.return_value = "abc123"

        mock_qdrant_wrapper.get_collection_info.return_value = {
            "points_count": 50,
            "vectors_count": 50,
        }

        result = get_index_status(
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "indexed"
        assert result["repo_path"] == "/test/repo"
        assert result["branch"] == "main"


def test_get_index_status_error_handling(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_index_status error handling."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker_class.side_effect = Exception("Tracker error")

        result = get_index_status(
            repo_path="/test/repo",
            branch="main",
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "error"
        assert "Tracker error" in result["error_message"]


def test_get_all_indexed_branches_success(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_all_indexed_branches returns branch list."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_all_tracked_branches.return_value = ["main", "develop", "feature"]

        result = get_all_indexed_branches(
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "success"
        assert len(result["branches"]) == 3
        assert "main" in result["branches"]
        assert result["total_branches"] == 3


def test_get_all_indexed_branches_empty(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_all_indexed_branches returns empty list when no branches."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker = Mock()
        mock_tracker_class.return_value = mock_tracker
        mock_tracker.get_all_tracked_branches.return_value = []

        result = get_all_indexed_branches(
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "success"
        assert result["branches"] == []
        assert result["total_branches"] == 0


def test_get_all_indexed_branches_error_handling(
    mock_config: Mock, mock_qdrant_wrapper: Mock
) -> None:
    """Test get_all_indexed_branches error handling."""
    with patch("git_debug_oracle.mcp_tools.get_index_status.CommitTracker") as mock_tracker_class:
        mock_tracker_class.side_effect = Exception("Tracker error")

        result = get_all_indexed_branches(
            config=mock_config,
            qdrant_wrapper=mock_qdrant_wrapper,
        )

        assert result["status"] == "error"
        assert "Tracker error" in result["error_message"]
        assert result["branches"] == []
