"""MCP tools for Phase 3 retrieval and error ingestion."""

from typing import Optional

from git_debug_oracle.error_ingestion.parsers import parse_error_payload
from git_debug_oracle.retriever.query_constructor import construct_query
from git_debug_oracle.retriever.qdrant_retriever import search_qdrant
from git_debug_oracle.retriever.git_diff_retriever import get_commit_diffs
from git_debug_oracle.retriever.result_formatter import format_results


def debug_error(
    file_path: str,
    line_number: int,
    function_name: Optional[str] = None,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
    stacktrace: Optional[str] = None,
    language: Optional[str] = None,
) -> dict:
    """Debug an error by retrieving relevant code chunks.

    Accepts error information and returns relevant code chunks from the
    indexed repository along with commit context and diffs.

    Args:
        file_path: Path to file where error occurred
        line_number: Line number (must be > 0)
        function_name: Name of function (optional)
        error_type: Exception type (optional)
        error_message: Error message (optional)
        stacktrace: Full stacktrace (optional)
        language: Programming language (optional)

    Returns:
        JSON object with retrieval results, diffs, and metadata

    Example:
        >>> result = debug_error(
        ...     file_path="src/app.py",
        ...     line_number=42,
        ...     function_name="process",
        ...     error_message="division by zero"
        ... )
        >>> "retrieval_results" in result
        True
    """
    # Parse error payload
    payload = {
        "file_path": file_path,
        "line_number": line_number,
        "function_name": function_name,
        "error_type": error_type,
        "error_message": error_message,
        "stacktrace": stacktrace,
        "language": language,
    }

    error_context = parse_error_payload(payload)

    # Construct query
    query = construct_query(error_context)

    # Search
    retrieval_results = search_qdrant(query, error_context, top_k=5)

    # Get diffs
    commit_hashes = [r.commit_hash for r in retrieval_results]
    related_diffs = get_commit_diffs(commit_hashes, ".")

    # Format response
    return format_results(retrieval_results, related_diffs, error_context)


def search_codebase(query: str) -> dict:
    """Search indexed codebase with arbitrary query.

    Performs vector search over all indexed code chunks with a custom query.

    Args:
        query: Search query string

    Returns:
        JSON object with retrieval results

    Example:
        >>> result = search_codebase("database connection pool")
        >>> len(result["retrieval_results"]) > 0
        True
    """
    from git_debug_oracle.error_ingestion.models import ErrorContext

    # Create minimal error context for search
    error_context = ErrorContext(
        file_path="",
        line_number=1,
        error_message=query,
    )

    # Search with custom query
    retrieval_results = search_qdrant(query, error_context, top_k=5)

    # Get diffs
    commit_hashes = [r.commit_hash for r in retrieval_results]
    related_diffs = get_commit_diffs(commit_hashes, ".")

    # Format response
    return format_results(retrieval_results, related_diffs, error_context)


def get_recent_diffs(num_commits: int = 10) -> dict:
    """Get diffs from recent commits.

    Retrieves git diffs from the N most recent commits in the repository.

    Args:
        num_commits: Number of recent commits to retrieve (max 20)

    Returns:
        JSON object with recent diffs

    Example:
        >>> result = get_recent_diffs(5)
        >>> "related_diffs" in result
        True
    """
    from git.repo import Repo
    from git_debug_oracle.error_ingestion.models import ErrorContext

    # Limit to reasonable number
    num_commits = min(num_commits, 20)

    try:
        repo = Repo(".")
        commits = list(repo.iter_commits("HEAD", max_count=num_commits))
        commit_hashes = [c.hexsha for c in commits]
    except Exception:
        commit_hashes = []

    # Get diffs
    related_diffs = get_commit_diffs(commit_hashes, ".")

    # Return with minimal context
    error_context = ErrorContext(
        file_path=".",
        line_number=1,
    )

    return {
        "error_context": {
            "file_path": ".",
            "line_number": 1,
        },
        "retrieval_results": [],
        "related_diffs": [
            {
                "commit_hash": d.commit_hash,
                "author": d.author,
                "message": d.message,
                "timestamp": d.timestamp.isoformat(),
                "files_changed": d.files_changed,
                "diff_content": d.diff_content,
            }
            for d in related_diffs
        ],
        "metadata": {
            "query_used": f"recent {num_commits} commits",
            "total_chunks_searched": 0,
            "search_duration_ms": 0,
            "timestamp": None,
        },
    }
