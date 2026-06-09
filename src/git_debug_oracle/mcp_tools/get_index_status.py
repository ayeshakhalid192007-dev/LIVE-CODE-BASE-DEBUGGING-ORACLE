"""MCP tool for querying index status."""

from typing import Optional

from git_debug_oracle.config import Config
from git_debug_oracle.git_watcher.commit_tracker import CommitTracker
from git_debug_oracle.utils.logging import get_logger
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper

logger = get_logger(__name__)


def get_index_status(
    repo_path: Optional[str] = None,
    branch: Optional[str] = None,
    config: Optional[Config] = None,
    qdrant_wrapper: Optional[QdrantClientWrapper] = None,
) -> dict:
    """Get the current index status for a repository and branch.

    Args:
        repo_path: Absolute path to repository (defaults to config.repo_path)
        branch: Branch name (defaults to config.watch_branch)
        config: Configuration object
        qdrant_wrapper: Qdrant client wrapper

    Returns:
        Dictionary with index status information
    """
    if config is None:
        config = Config()

    if qdrant_wrapper is None:
        qdrant_wrapper = QdrantClientWrapper(config)

    repo_path = repo_path or config.repo_path
    branch = branch or config.watch_branch

    logger.info(
        "MCP tool called: get_index_status",
        repo_path=repo_path,
        branch=branch,
    )

    try:
        tracker = CommitTracker(qdrant_wrapper)
        last_indexed_commit = tracker.get_last_indexed_commit(branch)

        if last_indexed_commit is None:
            logger.info("No index found for branch", branch=branch)
            return {
                "status": "not_indexed",
                "repo_path": repo_path,
                "branch": branch,
                "last_indexed_commit": None,
                "last_indexed_timestamp": None,
                "total_chunks": 0,
                "total_files": 0,
                "collection_name": config.qdrant_collection,
                "is_indexing": False,
                "error_message": None,
            }

        collection_info = qdrant_wrapper.get_collection_info(config.qdrant_collection)
        last_indexed_timestamp = tracker.get_last_indexed_timestamp(branch)

        result = {
            "status": "indexed",
            "repo_path": repo_path,
            "branch": branch,
            "last_indexed_commit": last_indexed_commit,
            "last_indexed_timestamp": last_indexed_timestamp,
            "total_chunks": collection_info.get("points_count", 0),
            "total_files": collection_info.get("vectors_count", 0),
            "collection_name": config.qdrant_collection,
            "is_indexing": False,
            "error_message": None,
        }

        logger.info("get_index_status completed successfully", **result)
        return result

    except Exception as e:
        error_message = str(e)
        logger.error("get_index_status failed", error=error_message)
        return {
            "status": "error",
            "repo_path": repo_path,
            "branch": branch,
            "last_indexed_commit": None,
            "last_indexed_timestamp": None,
            "total_chunks": 0,
            "total_files": 0,
            "collection_name": config.qdrant_collection,
            "is_indexing": False,
            "error_message": error_message,
        }


def get_all_indexed_branches(
    config: Optional[Config] = None,
    qdrant_wrapper: Optional[QdrantClientWrapper] = None,
) -> dict:
    """Get list of all branches that have been indexed.

    Args:
        config: Configuration object
        qdrant_wrapper: Qdrant client wrapper

    Returns:
        Dictionary with list of indexed branches
    """
    if config is None:
        config = Config()

    if qdrant_wrapper is None:
        qdrant_wrapper = QdrantClientWrapper(config)

    logger.info("MCP tool called: get_all_indexed_branches")

    try:
        tracker = CommitTracker(qdrant_wrapper)
        branches = tracker.get_all_tracked_branches()

        result = {
            "status": "success",
            "branches": branches,
            "total_branches": len(branches),
            "collection_name": config.qdrant_collection,
            "error_message": None,
        }

        logger.info("get_all_indexed_branches completed successfully", **result)
        return result

    except Exception as e:
        error_message = str(e)
        logger.error("get_all_indexed_branches failed", error=error_message)
        return {
            "status": "error",
            "branches": [],
            "total_branches": 0,
            "collection_name": config.qdrant_collection,
            "error_message": error_message,
        }
