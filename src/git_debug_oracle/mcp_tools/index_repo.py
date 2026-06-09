"""MCP tool for indexing repositories."""

from datetime import datetime
from typing import Optional

from git_debug_oracle.config import Config
from git_debug_oracle.indexer.pipeline import IndexingPipeline
from git_debug_oracle.git_watcher.commit_tracker import CommitTracker
from git_debug_oracle.utils.logging import get_logger
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper

logger = get_logger(__name__)


def index_repo(
    repo_path: Optional[str] = None,
    commit_hash: Optional[str] = None,
    branch: Optional[str] = None,
    force_full: bool = False,
    commit_range: Optional[tuple[str, str]] = None,
    config: Optional[Config] = None,
    qdrant_wrapper: Optional[QdrantClientWrapper] = None,
    embedder=None,
) -> dict:
    """Index a Git repository with optional commit hash or range.

    Args:
        repo_path: Absolute path to repository (defaults to config.repo_path)
        commit_hash: Specific commit to index (defaults to HEAD)
        branch: Branch name for tracking (defaults to config.watch_branch)
        force_full: Force full re-index instead of incremental
        commit_range: Tuple of (start_commit, end_commit) to index range
        config: Configuration object
        qdrant_wrapper: Qdrant client wrapper
        embedder: Embedder instance

    Returns:
        Dictionary with status, chunks_indexed, files_processed, duration_seconds
    """
    if config is None:
        config = Config()

    if qdrant_wrapper is None:
        qdrant_wrapper = QdrantClientWrapper(config)

    if embedder is None:
        from git_debug_oracle.embedder.voyage_client import VoyageEmbedder
        embedder = VoyageEmbedder(config.embedding_api_key)

    repo_path = repo_path or config.repo_path
    commit_hash = commit_hash or "HEAD"
    branch = branch or config.watch_branch

    logger.info(
        "MCP tool called: index_repo",
        repo_path=repo_path,
        commit_hash=commit_hash,
        branch=branch,
        force_full=force_full,
        commit_range=commit_range,
    )

    try:
        pipeline = IndexingPipeline(
            qdrant_wrapper,
            embedder,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )

        start_time = datetime.now()

        if commit_range:
            start_commit, end_commit = commit_range
            status = pipeline.index_commit_range(
                repo_path, start_commit, end_commit, branch
            )
        else:
            status = pipeline.index_commit(
                repo_path, commit_hash, branch, force_full=force_full
            )

        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "status": "success",
            "repo_path": repo_path,
            "branch": branch,
            "chunks_indexed": status.total_chunks,
            "files_processed": status.total_files,
            "last_indexed_commit": status.last_indexed_commit,
            "last_indexed_timestamp": status.last_indexed_timestamp.isoformat(),
            "duration_seconds": duration,
            "collection_name": status.collection_name,
            "error_message": None,
        }

        logger.info("index_repo completed successfully", **result)
        return result

    except Exception as e:
        error_message = str(e)
        logger.error("index_repo failed", error=error_message)
        return {
            "status": "error",
            "repo_path": repo_path,
            "branch": branch,
            "chunks_indexed": 0,
            "files_processed": 0,
            "last_indexed_commit": None,
            "last_indexed_timestamp": None,
            "duration_seconds": 0.0,
            "collection_name": config.qdrant_collection,
            "error_message": error_message,
        }


def index_incremental(
    repo_path: Optional[str] = None,
    branch: Optional[str] = None,
    config: Optional[Config] = None,
    qdrant_wrapper: Optional[QdrantClientWrapper] = None,
    embedder=None,
) -> dict:
    """Incrementally index repository (only new commits since last index).

    Args:
        repo_path: Absolute path to repository
        branch: Branch name to index
        config: Configuration object
        qdrant_wrapper: Qdrant client wrapper
        embedder: Embedder instance

    Returns:
        Dictionary with status and indexing results
    """
    if config is None:
        config = Config()

    if qdrant_wrapper is None:
        qdrant_wrapper = QdrantClientWrapper(config)

    if embedder is None:
        from git_debug_oracle.embedder.voyage_client import VoyageEmbedder
        embedder = VoyageEmbedder(config.embedding_api_key)

    repo_path = repo_path or config.repo_path
    branch = branch or config.watch_branch

    logger.info(
        "MCP tool called: index_incremental",
        repo_path=repo_path,
        branch=branch,
    )

    try:
        tracker = CommitTracker(qdrant_wrapper)
        last_indexed_commit = tracker.get_last_indexed_commit(branch)

        if last_indexed_commit is None:
            logger.info("No previous index found, indexing from HEAD")
            return index_repo(
                repo_path=repo_path,
                commit_hash="HEAD",
                branch=branch,
                force_full=True,
                config=config,
                qdrant_wrapper=qdrant_wrapper,
                embedder=embedder,
            )

        pipeline = IndexingPipeline(
            qdrant_wrapper,
            embedder,
            chunk_size=config.chunk_size,
            chunk_overlap=config.chunk_overlap,
        )

        start_time = datetime.now()
        status = pipeline.index_commit_range(
            repo_path, last_indexed_commit, "HEAD", branch
        )
        duration = (datetime.now() - start_time).total_seconds()

        result = {
            "status": "success",
            "repo_path": repo_path,
            "branch": branch,
            "chunks_indexed": status.total_chunks,
            "files_processed": status.total_files,
            "last_indexed_commit": status.last_indexed_commit,
            "last_indexed_timestamp": status.last_indexed_timestamp.isoformat(),
            "duration_seconds": duration,
            "collection_name": status.collection_name,
            "error_message": None,
        }

        logger.info("index_incremental completed successfully", **result)
        return result

    except Exception as e:
        error_message = str(e)
        logger.error("index_incremental failed", error=error_message)
        return {
            "status": "error",
            "repo_path": repo_path,
            "branch": branch,
            "chunks_indexed": 0,
            "files_processed": 0,
            "last_indexed_commit": None,
            "last_indexed_timestamp": None,
            "duration_seconds": 0.0,
            "collection_name": config.qdrant_collection,
            "error_message": error_message,
        }
