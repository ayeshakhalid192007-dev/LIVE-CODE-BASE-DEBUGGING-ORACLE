"""Error payload parser for ingesting error reports from external systems.

This module validates and normalizes error payloads received from webhooks,
extracting structured error information and preparing it for vector search
and code retrieval.
"""

from typing import Any, Optional

from git_debug_oracle.error_ingestion.models import ErrorContext, StackFrame
from git_debug_oracle.error_ingestion.stacktrace import normalize_stacktrace


def parse_error_payload(payload: dict[str, Any]) -> ErrorContext:
    """Parse and validate error payload from webhook request.

    Extracts structured error information from a raw JSON payload,
    validating required fields and normalizing optional fields. Automatically
    detects and parses stacktraces if present.

    Args:
        payload: Raw error payload dictionary

    Returns:
        Normalized ErrorContext with validated fields

    Raises:
        ValueError: If required fields are missing, invalid, or malformed
            - "file_path is required" if missing
            - "file_path must not be empty" if empty string
            - "line_number is required" if missing
            - "line_number must be > 0" if not positive integer
            - "stacktrace must be string or list" if invalid type

    Example:
        >>> payload = {
        ...     "file_path": "src/app.py",
        ...     "line_number": 42,
        ...     "function_name": "process_data",
        ...     "error_message": "division by zero"
        ... }
        >>> ctx = parse_error_payload(payload)
        >>> ctx.file_path
        'src/app.py'
        >>> ctx.line_number
        42
    """
    # Validate required fields
    if "file_path" not in payload:
        raise ValueError("file_path is required")

    file_path = payload["file_path"]
    if not isinstance(file_path, str) or not file_path.strip():
        raise ValueError("file_path must not be empty")

    if "line_number" not in payload:
        raise ValueError("line_number is required")

    line_number = payload["line_number"]
    if not isinstance(line_number, int) or line_number <= 0:
        raise ValueError("line_number must be > 0")

    # Extract optional fields
    function_name: Optional[str] = payload.get("function_name")
    error_type: Optional[str] = payload.get("error_type")
    error_message: Optional[str] = payload.get("error_message")
    language: Optional[str] = payload.get("language")

    # Normalize stacktrace
    raw_stacktrace = payload.get("stacktrace")
    stacktrace: Optional[str] = None
    parsed_frames: list[StackFrame] = []

    if raw_stacktrace is not None:
        # Validate stacktrace type
        if not isinstance(raw_stacktrace, (str, list)):
            raise ValueError(
                "stacktrace must be string or list, got "
                f"{type(raw_stacktrace).__name__}"
            )

        # Normalize to string
        stacktrace = normalize_stacktrace(raw_stacktrace)

    return ErrorContext(
        file_path=file_path,
        line_number=line_number,
        function_name=function_name,
        error_type=error_type,
        error_message=error_message,
        stacktrace=stacktrace,
        language=language,
        parsed_frames=parsed_frames,
    )
