"""Qdrant vector search retriever for finding relevant code chunks.

Performs semantic search against indexed code chunks using vector embeddings,
applies recency weighting, and returns ranked results with metadata.
"""

from datetime import datetime, timezone
from typing import Optional

from git_debug_oracle.error_ingestion.models import ErrorContext, RetrievalResult
from git_debug_oracle.utils.qdrant_client import get_qdrant_client
from git_debug_oracle.embedder.batch_processor import embed_text
from git_debug_oracle.retriever.recency_weighting import apply_recency_weight


def search_qdrant(
    query: str,
    ctx: ErrorContext,
    top_k: int = 5,
) -> list[RetrievalResult]:
    """Search Qdrant for code chunks matching error query.

    Converts query to embedding, searches Qdrant collection with optional
    metadata filtering, applies recency weighting to results, and returns
    ranked RetrievalResult objects.

    Args:
        query: Normalized query string from query constructor
        ctx: Original error context (used for metadata filtering)
        top_k: Maximum number of results to return

    Returns:
        List of RetrievalResult objects sorted by final_score (descending).
        Empty list if no matches found or collection does not exist.

    Example:
        >>> ctx = ErrorContext(file_path="src/app.py", line_number=42)
        >>> results = search_qdrant("process in src/app.py error", ctx, top_k=5)
        >>> len(results) <= 5
        True
    """
    client = get_qdrant_client()

    # Embed query using same model as indexing
    try:
        query_embedding = embed_text(query)
    except Exception:
        # If embedding fails, return empty results
        return []

    # Prepare metadata filter if file_path provided
    filter_dict: Optional[dict] = None
    if ctx.file_path:
        filter_dict = {"file_path": ctx.file_path}

    # Search Qdrant collection
    try:
        search_results = client.search(
            collection_name="code_chunks",
            query_vector=query_embedding,
            query_filter=filter_dict,
            limit=top_k * 2,  # Fetch more to account for deduplication
        )
    except Exception:
        # Collection doesn't exist or search error
        return []

    # Convert search results to RetrievalResult objects
    retrieval_results: list[RetrievalResult] = []
    now = datetime.now(timezone.utc)

    for rank, hit in enumerate(search_results, start=1):
        payload = hit.payload

        # Extract metadata from payload
        file_path: str = payload.get("file_path", "unknown")
        start_line: int = payload.get("start_line", 0)
        end_line: int = payload.get("end_line", 0)
        code_snippet: str = payload.get("content", "")
        commit_hash: str = payload.get("commit_hash", "")
        commit_author: str = payload.get("commit_author", "")
        commit_timestamp_str: str = payload.get("commit_timestamp", "")
        function_name: Optional[str] = payload.get("function_name")

        # Parse commit timestamp
        try:
            commit_timestamp = datetime.fromisoformat(commit_timestamp_str)
        except (ValueError, TypeError):
            commit_timestamp = now

        # Original score from vector similarity
        original_score: float = hit.score

        # Apply recency weighting
        final_score, recency_boost = apply_recency_weight(
            original_score, commit_timestamp, now
        )

        result = RetrievalResult(
            rank=rank,
            file_path=file_path,
            start_line=start_line,
            end_line=end_line,
            code_snippet=code_snippet,
            commit_hash=commit_hash,
            commit_author=commit_author,
            commit_timestamp=commit_timestamp,
            function_name=function_name,
            original_score=original_score,
            recency_score=recency_boost,
            final_score=final_score,
        )
        retrieval_results.append(result)

    # Deduplicate by file_path + start_line, keep highest score
    seen: dict[tuple[str, int], RetrievalResult] = {}
    for result in retrieval_results:
        key = (result.file_path, result.start_line)
        if key not in seen or result.final_score > seen[key].final_score:
            seen[key] = result

    # Sort by final_score descending and re-rank
    final_results = sorted(seen.values(), key=lambda r: r.final_score, reverse=True)
    for i, result in enumerate(final_results[:top_k], start=1):
        result.rank = i

    return final_results[:top_k]
