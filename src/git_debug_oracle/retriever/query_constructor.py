"""Query constructor for building vector search queries from error context.

Converts structured error information into optimized vector search queries
by prioritizing the most specific fields (function name, file path, error details)
and normalizing the result for consistent embedding generation.
"""

from git_debug_oracle.error_ingestion.models import ErrorContext


def construct_query(ctx: ErrorContext) -> str:
    """Build vector search query from error context.

    Constructs a query string optimized for vector embedding by combining
    the most relevant error information in priority order: function name,
    file path, error type, and error message.

    Args:
        ctx: Normalized error context from webhook payload

    Returns:
        Query string (max 500 chars) with normalized whitespace

    Example:
        >>> ctx = ErrorContext(
        ...     file_path="src/app.py",
        ...     line_number=42,
        ...     function_name="process_data",
        ...     error_message="division by zero"
        ... )
        >>> construct_query(ctx)
        'process_data in src/app.py division by zero'
    """
    parts: list[str] = []

    # Priority 1: Function name (most specific)
    if ctx.function_name:
        parts.append(ctx.function_name)
        parts.append("in")

    # Priority 2: File path
    parts.append(ctx.file_path)

    # Priority 3: Error type
    if ctx.error_type:
        parts.append(ctx.error_type)

    # Priority 4: Error message
    if ctx.error_message:
        parts.append(ctx.error_message)

    # Combine and normalize
    query = " ".join(parts)

    # Normalize whitespace
    query = " ".join(query.split())

    # Truncate to 500 chars
    if len(query) > 500:
        query = query[:500].rsplit(" ", 1)[0]

    return query
