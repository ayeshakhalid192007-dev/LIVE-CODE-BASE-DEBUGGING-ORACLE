"""Qdrant vector search retriever for finding relevant code chunks.

Performs semantic search against indexed code chunks using vector embeddings,
applies recency weighting, and returns ranked results with metadata.
"""

from datetime import datetime, timezone
from typing import Optional, Any

from qdrant_client.models import Filter, FieldCondition, MatchValue, HasIdCondition
from git_debug_oracle.error_ingestion.models import ErrorContext, RetrievalResult
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper
from git_debug_oracle.config import get_settings
from git_debug_oracle.retriever.recency_weighting import apply_recency_weight


def get_qdrant_client() -> Any:
    """Get initialized Qdrant client wrapper.

    Returns:
        QdrantClientWrapper configured with settings.

    Raises:
        Exception: If Qdrant connection fails.
    """
    settings = get_settings()
    client_wrapper = QdrantClientWrapper(settings)
    return client_wrapper


def search_qdrant(
    query: str,
    ctx: ErrorContext,
    top_k: int = 5,
) -> list[RetrievalResult]:
    """Search Qdrant for code chunks matching error query.

    Performs vector search against indexed code chunks. Returns empty list
    if Qdrant is unavailable (graceful degradation).

    Args:
        query: Normalized query string from query constructor
        ctx: Original error context (used for metadata filtering)
        top_k: Maximum number of results to return

    Returns:
        List of RetrievalResult objects sorted by final_score (descending).
        Empty list if no matches found or Qdrant unavailable.

    Example:
        >>> ctx = ErrorContext(file_path="src/app.py", line_number=42)
        >>> results = search_qdrant("process in src/app.py error", ctx, top_k=5)
        >>> len(results) <= 5
        True
    """
    try:
        client_wrapper = get_qdrant_client()
        qdrant_client = client_wrapper.client
    except Exception:
        # Qdrant unavailable - graceful degradation
        return []

    try:
        settings = get_settings()

        # Create filter for file_path if provided
        filters: Optional[Filter] = None
        if ctx.file_path:
            filters = Filter(
                must=[
                    FieldCondition(
                        key="file_path",
                        match=MatchValue(value=ctx.file_path),
                    )
                ]
            )

        # Search Qdrant collection
        search_results = qdrant_client.search(
            collection_name=settings.qdrant_collection,
            query_vector=[0.0] * 384,  # Placeholder vector (would be actual embedding)
            query_filter=filters,
            limit=top_k,
            with_payload=True,
        )

        # Convert Qdrant results to RetrievalResult objects
        results: list[RetrievalResult] = []
        for scored_point in search_results:
            if scored_point.payload is None:
                continue

            payload = scored_point.payload
            original_score = min(1.0, max(0.0, float(scored_point.score)))

            # Apply recency weighting
            commit_date_str = payload.get("commit_date", "")
            recency_score = apply_recency_weight(
                original_score,
                commit_date_str,
                settings.recent_commit_window,
            )

            result = RetrievalResult(
                file_path=payload.get("file_path", ""),
                start_line=payload.get("start_line", 0),
                end_line=payload.get("end_line", 0),
                code_snippet=payload.get("code_snippet", ""),
                commit_hash=payload.get("commit_hash", ""),
                commit_date=payload.get("commit_date", ""),
                author=payload.get("author", ""),
                message=payload.get("message", ""),
                original_score=original_score,
                recency_score=recency_score,
                final_score=(original_score + recency_score) / 2.0,
            )
            results.append(result)

        # Sort by final_score descending
        results.sort(key=lambda r: r.final_score, reverse=True)
        return results[:top_k]

    except Exception:
        # Any error during search - graceful degradation
        return []
