"""Indexing pipeline orchestration for Git repositories."""

import gc
import psutil
from datetime import datetime
from typing import Optional

from git_debug_oracle.git_watcher.repo_reader import (
    extract_files_from_commit,
    get_commit_metadata,
    get_commits_in_range,
    validate_repo,
)
from git_debug_oracle.git_watcher.commit_tracker import CommitTracker
from git_debug_oracle.indexer.file_filter import should_index_file_with_gitignore
from git_debug_oracle.indexer.chunker import chunk_file
from git_debug_oracle.indexer.metadata import extract_chunk_metadata
from git_debug_oracle.embedder.batch_processor import batch_embed
from git_debug_oracle.types import CodeChunk, IndexStatus
from git_debug_oracle.utils.logging import get_logger
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper

logger = get_logger(__name__)

MEMORY_LIMIT_BYTES = 2_147_483_648


class IndexingPipeline:
    """Orchestrates the full indexing pipeline."""

    def __init__(
        self,
        qdrant_wrapper: QdrantClientWrapper,
        embedder,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> None:
        """Initialize indexing pipeline.

        Args:
            qdrant_wrapper: Qdrant client wrapper
            embedder: Embedder instance (Voyage or OpenAI)
            chunk_size: Maximum characters per chunk
            chunk_overlap: Overlap between chunks
        """
        self.qdrant = qdrant_wrapper
        self.embedder = embedder
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        logger.info(
            "Indexing pipeline initialized",
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    def index_commit(
        self,
        repo_path: str,
        commit_hash: str,
        branch: str,
        force_full: bool = False,
    ) -> IndexStatus:
        """Index a single commit.

        Args:
            repo_path: Absolute path to repository
            commit_hash: Commit hash to index
            branch: Branch name
            force_full: Force full re-index (ignore last indexed commit)

        Returns:
            IndexStatus with indexing results

        Raises:
            Exception: If indexing fails
        """
        if not validate_repo(repo_path):
            raise ValueError(f"Invalid Git repository: {repo_path}")

        logger.info(
            "Starting commit indexing",
            repo_path=repo_path,
            commit_hash=commit_hash,
            branch=branch,
            force_full=force_full,
        )

        start_time = datetime.now()

        try:
            files_data = extract_files_from_commit(repo_path, commit_hash)
            commit_metadata = get_commit_metadata(repo_path, commit_hash)

            chunks = self._process_files(
                files_data, repo_path, commit_metadata
            )

            embedded_chunks = batch_embed(chunks, self.embedder)

            self.qdrant.create_collection_if_missing(self.qdrant.collection_name)
            self.qdrant.upsert_chunks(embedded_chunks)

            tracker = CommitTracker(self.qdrant)
            tracker.set_last_indexed_commit(branch, commit_hash, datetime.now())

            duration = (datetime.now() - start_time).total_seconds()

            status = IndexStatus(
                repo_path=repo_path,
                branch=branch,
                last_indexed_commit=commit_hash,
                last_indexed_timestamp=datetime.now(),
                total_chunks=len(embedded_chunks),
                total_files=len(files_data),
                collection_name=self.qdrant.collection_name,
                is_indexing=False,
            )

            logger.info(
                "Commit indexing completed",
                repo_path=repo_path,
                commit_hash=commit_hash,
                files_processed=len(files_data),
                chunks_indexed=len(embedded_chunks),
                duration_seconds=duration,
            )

            return status

        except Exception as e:
            logger.error(
                "Commit indexing failed",
                repo_path=repo_path,
                commit_hash=commit_hash,
                error=str(e),
            )
            raise

    def index_commit_range(
        self,
        repo_path: str,
        start_commit: str,
        end_commit: str,
        branch: str,
    ) -> IndexStatus:
        """Index all commits in a range.

        Args:
            repo_path: Absolute path to repository
            start_commit: Starting commit (exclusive)
            end_commit: Ending commit (inclusive)
            branch: Branch name

        Returns:
            IndexStatus with combined results
        """
        if not validate_repo(repo_path):
            raise ValueError(f"Invalid Git repository: {repo_path}")

        logger.info(
            "Starting commit range indexing",
            repo_path=repo_path,
            start_commit=start_commit,
            end_commit=end_commit,
            branch=branch,
        )

        commit_hashes = get_commits_in_range(repo_path, start_commit, end_commit)

        total_chunks = 0
        total_files = 0

        for commit_hash in commit_hashes:
            try:
                status = self.index_commit(repo_path, commit_hash, branch, force_full=False)
                total_chunks += status.total_chunks
                total_files += status.total_files
            except Exception as e:
                logger.warning(
                    "Failed to index commit in range",
                    commit_hash=commit_hash,
                    error=str(e),
                )

        final_status = IndexStatus(
            repo_path=repo_path,
            branch=branch,
            last_indexed_commit=end_commit,
            last_indexed_timestamp=datetime.now(),
            total_chunks=total_chunks,
            total_files=total_files,
            collection_name=self.qdrant.collection_name,
            is_indexing=False,
        )

        logger.info(
            "Commit range indexing completed",
            repo_path=repo_path,
            commits_indexed=len(commit_hashes),
            total_chunks=total_chunks,
            total_files=total_files,
        )

        return final_status

    def _process_files(
        self,
        files_data: list[tuple[str, str]],
        repo_path: str,
        commit_metadata: dict[str, str],
    ) -> list[CodeChunk]:
        """Process files and generate chunks.

        Args:
            files_data: List of (file_path, content) tuples
            repo_path: Absolute path to repository
            commit_metadata: Commit metadata dictionary

        Returns:
            List of CodeChunk objects
        """
        chunks: list[CodeChunk] = []
        files_processed = 0

        for file_path, file_content in files_data:
            self._check_memory_usage()

            if not should_index_file_with_gitignore(file_path, file_content, repo_path):
                logger.debug("Skipping file", file_path=file_path)
                continue

            try:
                chunk_dicts = chunk_file(file_path, file_content, self.chunk_size, self.chunk_overlap)

                for chunk_dict in chunk_dicts:
                    if "error" in chunk_dict:
                        logger.error(
                            "Failed to chunk file",
                            file_path=file_path,
                            error=chunk_dict.get("error"),
                        )
                        continue

                    chunk = extract_chunk_metadata(chunk_dict, file_path, commit_metadata)
                    chunks.append(chunk)

                files_processed += 1

                if files_processed % 10 == 0:
                    logger.info(
                        "Progress: files processed",
                        files_processed=files_processed,
                        chunks_generated=len(chunks),
                    )

            except Exception as e:
                logger.error(
                    "Error processing file",
                    file_path=file_path,
                    error=str(e),
                )

        logger.info(
            "File processing completed",
            files_processed=files_processed,
            chunks_generated=len(chunks),
        )

        return chunks

    def _check_memory_usage(self) -> None:
        """Check memory usage and pause if exceeding limit."""
        process = psutil.Process()
        memory_usage = process.memory_info().rss

        if memory_usage > MEMORY_LIMIT_BYTES:
            logger.warning(
                "Memory usage exceeds limit, triggering garbage collection",
                memory_usage_mb=memory_usage / 1_048_576,
                limit_mb=MEMORY_LIMIT_BYTES / 1_048_576,
            )
            gc.collect()
