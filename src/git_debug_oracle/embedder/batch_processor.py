"""Batch embedding processor for code chunks."""

from typing import Protocol

from git_debug_oracle.types import CodeChunk
from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)

BATCH_SIZE = 100


class EmbedderProtocol(Protocol):
    """Protocol for embedding clients."""

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        ...


def batch_embed(
    chunks: list[CodeChunk], embedder: EmbedderProtocol
) -> list[CodeChunk]:
    """Embed chunks in batches using provided embedder.

    Args:
        chunks: List of CodeChunk objects to embed
        embedder: Embedder instance with embed_batch method

    Returns:
        List of CodeChunk objects with embeddings attached

    Raises:
        Exception: If embedding fails
    """
    if not chunks:
        logger.warning("Empty chunk list provided to batch_embed")
        return []

    logger.info(
        "Starting batch embedding",
        total_chunks=len(chunks),
        batch_size=BATCH_SIZE,
    )

    embedded_chunks: list[CodeChunk] = []
    batch_count = (len(chunks) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_num in range(batch_count):
        start_idx = batch_num * BATCH_SIZE
        end_idx = min(start_idx + BATCH_SIZE, len(chunks))
        batch_chunks = chunks[start_idx:end_idx]

        chunk_texts = [chunk.content for chunk in batch_chunks]

        logger.info(
            "Embedding batch",
            batch_num=batch_num + 1,
            total_batches=batch_count,
            chunk_count=len(batch_chunks),
        )

        embeddings = embedder.embed_batch(chunk_texts)

        for chunk, embedding in zip(batch_chunks, embeddings):
            embedded_chunk = CodeChunk(
                content=chunk.content,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                commit_hash=chunk.commit_hash,
                commit_author=chunk.commit_author,
                commit_timestamp=chunk.commit_timestamp,
                function_name=chunk.function_name,
                embedding=embedding,
                chunk_id=chunk.chunk_id,
            )
            embedded_chunks.append(embedded_chunk)

        logger.info(
            "Batch embedding completed",
            batch_num=batch_num + 1,
            total_batches=batch_count,
        )

    logger.info("Batch embedding completed for all chunks", total_chunks=len(embedded_chunks))

    return embedded_chunks
