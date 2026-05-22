"""Qdrant client wrapper with connection testing."""

from typing import Optional

from qdrant_client import QdrantClient

from git_debug_oracle.config import Config
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
        self._client = QdrantClient(
            host=config.qdrant_host,
            port=config.qdrant_port,
            api_key=config.qdrant_api_key,
        )

        logger.info(
            "Qdrant client initialized",
            host=config.qdrant_host,
            port=config.qdrant_port,
            collection=config.qdrant_collection,
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
