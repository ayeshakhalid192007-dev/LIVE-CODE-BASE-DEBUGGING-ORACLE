"""Voyage AI embedding client with retry logic."""

import time

import voyageai

from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)

MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0
MAX_BACKOFF = 10.0


class VoyageEmbedder:
    """Embed code chunks using Voyage AI API."""

    def __init__(self, api_key: str) -> None:
        """Initialize Voyage AI embedder.

        Args:
            api_key: Voyage AI API key
        """
        self.client = voyageai.Client(api_key=api_key)
        self.model = "voyage-code-2"
        logger.info("Voyage AI embedder initialized", model=self.model)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts using Voyage AI with retry logic.

        Args:
            texts: List of code chunk texts to embed

        Returns:
            List of embedding vectors (each vector is list of floats)

        Raises:
            Exception: If all retries fail
        """
        if not texts:
            logger.warning("Empty text list provided to embed_batch")
            return []

        logger.info(
            "Embedding batch with Voyage AI",
            text_count=len(texts),
            model=self.model,
        )

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.embed(
                    texts=texts,
                    model=self.model,
                    input_type="code",
                )

                embeddings = [item.embedding for item in response.embeddings]

                logger.info(
                    "Successfully embedded batch",
                    text_count=len(texts),
                    embedding_dim=len(embeddings[0]) if embeddings else 0,
                    attempt=attempt + 1,
                )

                return embeddings

            except Exception as e:
                backoff_time = min(INITIAL_BACKOFF * (2 ** attempt), MAX_BACKOFF)

                if attempt < MAX_RETRIES - 1:
                    logger.warning(
                        "Voyage AI embedding failed, retrying",
                        attempt=attempt + 1,
                        max_retries=MAX_RETRIES,
                        backoff_seconds=backoff_time,
                        error=str(e),
                    )
                    time.sleep(backoff_time)
                else:
                    logger.error(
                        "Voyage AI embedding failed after all retries",
                        max_retries=MAX_RETRIES,
                        error=str(e),
                    )
                    raise Exception(
                        f"Failed to embed batch after {MAX_RETRIES} retries: {str(e)}"
                    ) from e

        raise Exception("Unexpected error in embed_batch")

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model.

        Returns:
            Embedding dimension (1536 for voyage-code-2)
        """
        return 1536
