"""Unit tests for git_watcher/commit_tracker.py."""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest
from qdrant_client.models import PointStruct, Record

from git_debug_oracle.config import Config
from git_debug_oracle.git_watcher.commit_tracker import CommitTracker
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper


@pytest.fixture
def mock_config() -> Config:
    """Create a mock Config instance for testing.

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
    """Create a mock QdrantClientWrapper for testing.

    Args:
        mock_config: Mock Config fixture

    Returns:
        Mock QdrantClientWrapper instance
    """
    wrapper = Mock(spec=QdrantClientWrapper)
    wrapper.client = MagicMock()
    wrapper.config = mock_config
    return wrapper


@pytest.fixture
def commit_tracker(mock_qdrant_wrapper: QdrantClientWrapper) -> CommitTracker:
    """Create a CommitTracker instance with mocked Qdrant client.

    Args:
        mock_qdrant_wrapper: Mock QdrantClientWrapper fixture

    Returns:
        CommitTracker instance
    """
    with patch.object(CommitTracker, "_ensure_metadata_collection"):
        tracker = CommitTracker(mock_qdrant_wrapper)
    return tracker


def test_commit_tracker_initialization(mock_qdrant_wrapper: QdrantClientWrapper) -> None:
    """Test CommitTracker initializes and creates metadata collection."""
    mock_qdrant_wrapper.client.get_collection.side_effect = Exception("Collection not found")

    tracker = CommitTracker(mock_qdrant_wrapper)

    mock_qdrant_wrapper.client.create_collection.assert_called_once()
    assert tracker is not None


def test_commit_tracker_initialization_with_existing_collection(
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test CommitTracker initialization when collection already exists."""
    mock_qdrant_wrapper.client.get_collection.return_value = Mock()

    tracker = CommitTracker(mock_qdrant_wrapper)

    mock_qdrant_wrapper.client.create_collection.assert_not_called()
    assert tracker is not None


def test_get_last_indexed_commit_returns_commit_hash(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_last_indexed_commit returns commit hash for tracked branch."""
    expected_commit = "abc123def456"
    mock_point = Record(
        id="branch_main",
        vector=[0.0],
        payload={
            "branch": "main",
            "last_commit": expected_commit,
            "last_indexed_timestamp": "2026-05-29T12:00:00",
        },
    )
    mock_qdrant_wrapper.client.retrieve.return_value = [mock_point]

    result = commit_tracker.get_last_indexed_commit("main")

    assert result == expected_commit
    mock_qdrant_wrapper.client.retrieve.assert_called_once()


def test_get_last_indexed_commit_returns_none_for_untracked_branch(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_last_indexed_commit returns None for untracked branch."""
    mock_qdrant_wrapper.client.retrieve.return_value = []

    result = commit_tracker.get_last_indexed_commit("feature_branch")

    assert result is None


def test_get_last_indexed_commit_handles_exception(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_last_indexed_commit handles exceptions gracefully."""
    mock_qdrant_wrapper.client.retrieve.side_effect = Exception("Connection error")

    result = commit_tracker.get_last_indexed_commit("main")

    assert result is None


def test_set_last_indexed_commit_upserts_point(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test set_last_indexed_commit upserts point to Qdrant."""
    branch = "main"
    commit_hash = "abc123def456"
    timestamp = datetime(2026, 5, 29, 12, 0, 0)

    commit_tracker.set_last_indexed_commit(branch, commit_hash, timestamp)

    mock_qdrant_wrapper.client.upsert.assert_called_once()
    call_args = mock_qdrant_wrapper.client.upsert.call_args
    assert call_args.kwargs["collection_name"] == "git_debug_oracle_metadata"

    points = call_args.kwargs["points"]
    assert len(points) == 1
    assert points[0].payload["branch"] == branch
    assert points[0].payload["last_commit"] == commit_hash
    assert points[0].payload["last_indexed_timestamp"] == timestamp.isoformat()


def test_set_last_indexed_commit_uses_correct_point_id(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test set_last_indexed_commit uses correct point ID format."""
    branch = "feature_branch"
    commit_hash = "xyz789"
    timestamp = datetime(2026, 5, 29, 12, 0, 0)

    commit_tracker.set_last_indexed_commit(branch, commit_hash, timestamp)

    call_args = mock_qdrant_wrapper.client.upsert.call_args
    points = call_args.kwargs["points"]
    
    # Point ID should be integer
    assert isinstance(points[0].id, int)
    # Point payload should contain branch name
    assert points[0].payload["branch"] == branch


def test_get_all_tracked_branches_returns_branch_list(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_all_tracked_branches returns list of tracked branches."""
    mock_points = [
        Record(
            id="branch_main",
            vector=[0.0],
            payload={"branch": "main", "last_commit": "abc123"},
        ),
        Record(
            id="branch_develop",
            vector=[0.0],
            payload={"branch": "develop", "last_commit": "def456"},
        ),
        Record(
            id="branch_feature",
            vector=[0.0],
            payload={"branch": "feature", "last_commit": "ghi789"},
        ),
    ]
    mock_qdrant_wrapper.client.scroll.return_value = (mock_points, None)

    result = commit_tracker.get_all_tracked_branches()

    assert len(result) == 3
    assert "main" in result
    assert "develop" in result
    assert "feature" in result


def test_get_all_tracked_branches_returns_empty_list_on_error(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_all_tracked_branches returns empty list on error."""
    mock_qdrant_wrapper.client.scroll.side_effect = Exception("Connection error")

    result = commit_tracker.get_all_tracked_branches()

    assert result == []


def test_get_all_tracked_branches_filters_invalid_payloads(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test get_all_tracked_branches filters points without branch field."""
    mock_points = [
        Record(
            id="branch_main",
            vector=[0.0],
            payload={"branch": "main", "last_commit": "abc123"},
        ),
        Record(
            id="invalid_point",
            vector=[0.0],
            payload={"last_commit": "def456"},
        ),
    ]
    mock_qdrant_wrapper.client.scroll.return_value = (mock_points, None)

    result = commit_tracker.get_all_tracked_branches()

    assert len(result) == 1
    assert "main" in result


def test_branch_to_point_id_format(commit_tracker: CommitTracker) -> None:
    """Test _branch_to_point_id generates deterministic integer."""
    result = commit_tracker._branch_to_point_id("main")
    assert isinstance(result, int)
    assert result > 0

    # Same branch should generate same ID
    result2 = commit_tracker._branch_to_point_id("main")
    assert result == result2

    # Different branch should generate different ID
    result3 = commit_tracker._branch_to_point_id("feature/new-feature")
    assert result3 != result
    assert isinstance(result3, int)


def test_set_and_get_last_indexed_commit_integration(
    commit_tracker: CommitTracker,
    mock_qdrant_wrapper: QdrantClientWrapper,
) -> None:
    """Test setting and getting last indexed commit works together."""
    branch = "main"
    commit_hash = "abc123def456"
    timestamp = datetime(2026, 5, 29, 12, 0, 0)

    commit_tracker.set_last_indexed_commit(branch, commit_hash, timestamp)

    mock_point = Record(
        id="branch_main",
        vector=[0.0],
        payload={
            "branch": branch,
            "last_commit": commit_hash,
            "last_indexed_timestamp": timestamp.isoformat(),
        },
    )
    mock_qdrant_wrapper.client.retrieve.return_value = [mock_point]

    result = commit_tracker.get_last_indexed_commit(branch)

    assert result == commit_hash
