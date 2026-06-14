"""Qdrant client wrapper with connection testing and collection management."""

import time
from typing import Optional

from qdrant_client.models import Distance, PointStruct, VectorParams

from qdrant_client import QdrantClient

from git_debug_oracle.config import Config
from git_debug_oracle.types import CodeChunk
from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)


class QdrantClientWrapper:
    """Wrapper for Qdrant client with connection testing and configuration."""

    def __init__(self, config: Config) -> None:
        """Initialize Qdrant client with configuration.

        Args:
            config: Application configuration containing Qdrant settings
        """
        self._config = config

        use_ssl = config.qdrant_host not in ("localhost", "127.0.0.1")

        self._client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port,
            api_key=config.qdrant_api_key,
            https=use_ssl,
        )

        logger.info(
            "Qdrant client initialized",
            host=config.qdrant_host,
            port=config.qdrant_port,
            collection=config.qdrant_collection,
            use_ssl=use_ssl,
        )

    @property
    def client(self) -> QdrantClient:
        """Get the underlying Qdrant client instance.

        Returns:
            QdrantClient instance
        """
        return self._client

    @property
    def config(self) -> Config:
        """Get the configuration.

        Returns:
            Config instance
        """
        return self._config

    @property
    def collection_name(self) -> str:
        """Get the collection name from configuration.

        Returns:
            Collection name string
        """
        return self._config.qdrant_collection

    def test_connection(self) -> bool:
        """Test connection to Qdrant server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Attempt to get collections as a connection test
            self._client.get_collections()
            logger.info("Qdrant connection test successful")
            return True
        except Exception as e:
            logger.error(
                "Qdrant connection test failed",
                error=str(e),
                host=self._config.qdrant_host,
                port=self._config.qdrant_port,
            )
            return False

    def create_collection_if_missing(self, collection_name: str, vector_dim: int = 1536) -> None:
        """Create Qdrant collection if it does not exist.

        Args:
            collection_name: Name of collection to create
            vector_dim: Dimension of vectors (default: 1536 for embeddings)
        """
        try:
            self._client.get_collection(collection_name)
            logger.debug("Collection already exists", collection=collection_name)
        except Exception:
            logger.info("Creating Qdrant collection", collection=collection_name, vector_dim=vector_dim)
            self._client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_dim, distance=Distance.COSINE),
            )
            logger.info("Collection created successfully", collection=collection_name)

    def delete_chunks_by_file(self, file_path: str, commit_hash: str) -> None:
        """Delete all chunks for a specific file in a commit.

        Args:
            file_path: Relative path to file
            commit_hash: Git commit hash
        """
        try:
            self._client.delete(
                collection_name=self.collection_name,
                points_selector=self._build_file_selector(file_path, commit_hash),
            )
            logger.info(
                "Deleted chunks for file",
                collection=self.collection_name,
                file_path=file_path,
                commit_hash=commit_hash[:8],
            )
        except Exception as e:
            logger.error(
                "Failed to delete chunks",
                file_path=file_path,
                commit_hash=commit_hash[:8],
                error=str(e),
            )
            raise

    def upsert_chunks(self, chunks: list[CodeChunk]) -> None:
        """Upsert code chunks into Qdrant with retry logic.

        Args:
            chunks: List of CodeChunk objects to upsert

        Raises:
            Exception: If upsert fails after all retries
        """
        if not chunks:
            logger.warning("Empty chunk list provided to upsert_chunks")
            return

        logger.info(
            "Upserting chunks to Qdrant",
            collection=self.collection_name,
            chunk_count=len(chunks),
        )

        points = self._chunks_to_points(chunks)

        max_retries = 3
        for attempt in range(max_retries):
            try:
                self._client.upsert(
                    collection_name=self.collection_name,
                    points=points,
                )
                logger.info(
                    "Successfully upserted chunks",
                    collection=self.collection_name,
                    chunk_count=len(chunks),
                    attempt=attempt + 1,
                )
                return
            except Exception as e:
                backoff_time = min(1.0 * (2 ** attempt), 10.0)
                if attempt < max_retries - 1:
                    logger.warning(
                        "Upsert failed, retrying",
                        attempt=attempt + 1,
                        max_retries=max_retries,
                        backoff_seconds=backoff_time,
                        error=str(e),
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(
                        "Upsert failed after all retries",
                        max_retries=max_retries,
                        error=str(e),
                    )
                    raise Exception(f"Failed to upsert chunks after {max_retries} retries: {str(e)}") from e

    def get_collection_info(self, collection_name: str) -> dict:
        """Get information about a collection.

        Args:
            collection_name: Name of collection

        Returns:
            Dictionary with collection info
        """
        try:
            collection_info = self._client.get_collection(collection_name)
            logger.debug("Retrieved collection info", collection=collection_name)
            return {
                "name": collection_name,
                "points_count": collection_info.points_count,
                "vectors_count": collection_info.vectors_count,
            }
        except Exception as e:
            logger.error("Failed to get collection info", collection=collection_name, error=str(e))
            raise

    def _chunks_to_points(self, chunks: list[CodeChunk]) -> list[PointStruct]:
        """Convert CodeChunk objects to Qdrant PointStruct objects.

        Args:
            chunks: List of CodeChunk objects

        Returns:
            List of PointStruct objects
        """
        points = []
        for chunk in chunks:
            point_id = int(chunk.chunk_id[:16], 16) % (2**63)
            point = PointStruct(
                id=point_id,
                vector=chunk.embedding if chunk.embedding else [0.0] * 1536,
                payload={
                    "content": chunk.content,
                    "file_path": chunk.file_path,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "commit_hash": chunk.commit_hash,
                    "commit_author": chunk.commit_author,
                    "commit_timestamp": chunk.commit_timestamp.isoformat(),
                    "function_name": chunk.function_name,
                    "chunk_id": chunk.chunk_id,
                },
            )
            points.append(point)
        return points

    def _build_file_selector(self, file_path: str, commit_hash: str):
        """Build a Qdrant filter for selecting chunks by file and commit.

        Args:
            file_path: Relative path to file
            commit_hash: Git commit hash

        Returns:
            Qdrant filter selector
        """
        from qdrant_client.models import Filter, FieldCondition, MatchValue

        return Filter(
            must=[
                FieldCondition(key="file_path", match=MatchValue(value=file_path)),
                FieldCondition(key="commit_hash", match=MatchValue(value=commit_hash)),
            ]
        )
