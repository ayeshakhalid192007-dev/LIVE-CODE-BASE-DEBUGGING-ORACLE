"""Result formatter for converting retrieval results to JSON response.

Formats RetrievalResult objects into a structured JSON response with error
context, code chunks, related diffs, and search metadata.
"""

from datetime import datetime, timezone
from typing import Any

from git_debug_oracle.error_ingestion.models import (
    ErrorContext,
    RetrievalResult,
    CommitDiff,
)
from git_debug_oracle.retriever.query_constructor import construct_query


def format_results(
    retrieval_results: list[RetrievalResult],
    related_diffs: list[CommitDiff],
    error_context: ErrorContext,
    search_duration_ms: float = 0.0,
) -> dict[str, Any]:
    """Format retrieval results as JSON response.

    Converts RetrievalResult and CommitDiff objects into a structured JSON
    response suitable for webhook endpoint and MCP tools. Includes error
    context, ranked code chunks, related commits, and search metadata.

    Args:
        retrieval_results: List of RetrievalResult from vector search
        related_diffs: List of CommitDiff from git retrieval
        error_context: Original error that was queried
        search_duration_ms: How long the search took (milliseconds)

    Returns:
        Dictionary with error_context, retrieval_results, related_diffs,
        and metadata fields, ready for JSON serialization.

    Example:
        >>> ctx = ErrorContext(file_path="app.py", line_number=1)
        >>> formatted = format_results([], [], ctx)
        >>> list(formatted.keys())
        ['error_context', 'retrieval_results', 'related_diffs', 'metadata']
    """
    now = datetime.now(timezone.utc)

    # Format error context
    error_dict = {
        "file_path": error_context.file_path,
        "line_number": error_context.line_number,
        "function_name": error_context.function_name,
        "error_type": error_context.error_type,
        "error_message": error_context.error_message,
    }

    # Format retrieval results
    results_list = []
    for result in retrieval_results:
        # Truncate code snippet to 500 chars at word boundary
        code_snippet = result.code_snippet
        if len(code_snippet) > 500:
            code_snippet = code_snippet[:500].rsplit(" ", 1)[0]

        result_dict = {
            "rank": result.rank,
            "file_path": result.file_path,
            "start_line": result.start_line,
            "end_line": result.end_line,
            "code_snippet": code_snippet,
            "commit_hash": result.commit_hash,
            "commit_author": result.commit_author,
            "commit_timestamp": result.commit_timestamp.isoformat(),
            "function_name": result.function_name,
            "score": round(result.final_score, 4),
            "recency_score": round(result.recency_score, 4),
        }
        results_list.append(result_dict)

    # Format related diffs
    diffs_list = []
    for diff in related_diffs:
        diff_dict = {
            "commit_hash": diff.commit_hash,
            "author": diff.author,
            "message": diff.message,
            "timestamp": diff.timestamp.isoformat(),
            "files_changed": diff.files_changed,
            "diff_content": diff.diff_content,
        }
        diffs_list.append(diff_dict)

    # Format metadata
    query_used = construct_query(error_context)
    metadata = {
        "query_used": query_used,
        "total_chunks_searched": len(retrieval_results),
        "search_duration_ms": round(search_duration_ms, 2),
        "timestamp": now.isoformat(),
    }

    return {
        "error_context": error_dict,
        "retrieval_results": results_list,
        "related_diffs": diffs_list,
        "metadata": metadata,
    }
