"""Multi-branch commit tracking using Qdrant metadata collection."""

from datetime import datetime
from typing import Optional

from qdrant_client.models import Distance, PointStruct, VectorParams

from git_debug_oracle.utils.logging import get_logger
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper

logger = get_logger(__name__)

METADATA_COLLECTION_NAME = "git_debug_oracle_metadata"
METADATA_VECTOR_DIM = 1


class CommitTracker:
    """Tracks last indexed commit per branch using Qdrant metadata collection."""

    def __init__(self, qdrant_wrapper: QdrantClientWrapper) -> None:
        """Initialize commit tracker with Qdrant client.

        Args:
            qdrant_wrapper: Qdrant client wrapper instance
        """
        self._qdrant = qdrant_wrapper
        self._ensure_metadata_collection()

    def _ensure_metadata_collection(self) -> None:
        """Create metadata collection if it does not exist."""
        try:
            self._qdrant.client.get_collection(METADATA_COLLECTION_NAME)
            logger.debug("Metadata collection exists", collection=METADATA_COLLECTION_NAME)
        except Exception:
            logger.info("Creating metadata collection", collection=METADATA_COLLECTION_NAME)
            self._qdrant.client.create_collection(
                collection_name=METADATA_COLLECTION_NAME,
                vectors_config=VectorParams(size=METADATA_VECTOR_DIM, distance=Distance.COSINE),
            )
            logger.info("Metadata collection created", collection=METADATA_COLLECTION_NAME)

    def get_last_indexed_commit(self, branch: str) -> Optional[str]:
        """Get the last indexed commit hash for a branch.

        Args:
            branch: Branch name

        Returns:
            Commit hash if branch has been indexed, None otherwise
        """
        try:
            point_id = self._branch_to_point_id(branch)
            point = self._qdrant.client.retrieve(
                collection_name=METADATA_COLLECTION_NAME,
                ids=[point_id],
            )

            if not point:
                logger.debug("No indexed commit found for branch", branch=branch)
                return None

            commit_hash = point[0].payload.get("last_commit")
            logger.debug(
                "Retrieved last indexed commit",
                branch=branch,
                commit_hash=commit_hash,
            )
            return commit_hash

        except Exception as e:
            logger.warning(
                "Failed to retrieve last indexed commit",
                branch=branch,
                error=str(e),
            )
            return None

    def set_last_indexed_commit(
        self, branch: str, commit_hash: str, timestamp: datetime
    ) -> None:
        """Set the last indexed commit hash for a branch.

        Args:
            branch: Branch name
            commit_hash: Commit hash that was indexed
            timestamp: Timestamp when indexing completed
        """
        point_id = self._branch_to_point_id(branch)
        point = PointStruct(
            id=point_id,
            vector=[0.0],
            payload={
                "branch": branch,
                "last_commit": commit_hash,
                "last_indexed_timestamp": timestamp.isoformat(),
            },
        )

        self._qdrant.client.upsert(
            collection_name=METADATA_COLLECTION_NAME,
            points=[point],
        )

        logger.info(
            "Updated last indexed commit",
            branch=branch,
            commit_hash=commit_hash,
            timestamp=timestamp.isoformat(),
        )

    def get_all_tracked_branches(self) -> list[str]:
        """Get list of all branches that have been indexed.

        Returns:
            List of branch names
        """
        try:
            scroll_result = self._qdrant.client.scroll(
                collection_name=METADATA_COLLECTION_NAME,
                limit=1000,
            )

            points = scroll_result[0]
            branches = [point.payload.get("branch") for point in points if point.payload.get("branch")]

            logger.debug("Retrieved tracked branches", count=len(branches))
            return branches

        except Exception as e:
            logger.error("Failed to retrieve tracked branches", error=str(e))
            return []

    def _branch_to_point_id(self, branch: str) -> str:
        """Convert branch name to Qdrant point ID.

        Args:
            branch: Branch name

        Returns:
            Point ID string
        """
        return f"branch_{branch}"
