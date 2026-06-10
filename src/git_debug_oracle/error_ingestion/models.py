"""Domain models for error ingestion pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass
class StackFrame:
    """Represents a single frame in a stacktrace.

    Attributes:
        file_path: Path to the source file where the frame occurred.
        function_name: Name of the function or method.
        line_number: Line number where the error occurred (must be > 0).
    """

    file_path: str
    function_name: str
    line_number: int

    def __post_init__(self) -> None:
        """Validate that line_number is positive."""
        if self.line_number <= 0:
            raise ValueError(
                f"line_number must be > 0, got {self.line_number}"
            )


@dataclass
class ErrorContext:
    """Normalized error information from webhook payload.

    Represents a structured representation of an error that can be used for
    querying the indexed codebase and generating fix proposals.

    Attributes:
        file_path: Path to the file where the error occurred (required).
        line_number: Line number where the error occurred (required, > 0).
        function_name: Name of the function where error occurred (optional).
        error_type: Exception type (e.g., "ValueError", "NullPointerException").
        error_message: Human-readable error message.
        stacktrace: Raw stacktrace string or None.
        language: Programming language (python, javascript, java, go).
        parsed_frames: List of StackFrame objects extracted from stacktrace.
    """

    file_path: str
    line_number: int
    function_name: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None
    stacktrace: Optional[str] = None
    language: Optional[str] = None
    parsed_frames: list[StackFrame] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate required fields."""
        if not self.file_path or not self.file_path.strip():
            raise ValueError("file_path must not be empty")
        if self.line_number <= 0:
            raise ValueError(f"line_number must be > 0, got {self.line_number}")


@dataclass
class RetrievalResult:
    """Single code chunk retrieved from Qdrant.

    Represents a chunk of code that matched the error query, with scoring
    information and commit context.

    Attributes:
        rank: Position in result list (1-indexed).
        file_path: Path to the source file containing this chunk.
        start_line: Starting line number of the chunk.
        end_line: Ending line number of the chunk.
        code_snippet: The actual code content (truncated to 500 chars).
        commit_hash: Git commit hash where this chunk originated.
        commit_author: Author of the commit.
        commit_timestamp: When the commit was created (UTC).
        function_name: Name of the function containing this chunk (optional).
        original_score: Vector similarity score before weighting (0-1).
        recency_score: Recency boost factor applied (0-1).
        final_score: Final score after applying recency weighting (0-1).
    """

    rank: int
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str
    commit_hash: str
    commit_author: str
    commit_timestamp: datetime
    function_name: Optional[str] = None
    original_score: float = 0.0
    recency_score: float = 1.0
    final_score: float = 0.0

    def __post_init__(self) -> None:
        """Validate that scores are in valid range."""
        if not 0 <= self.original_score <= 1:
            raise ValueError(
                f"original_score must be in [0, 1], got {self.original_score}"
            )
        if not 0 <= self.recency_score <= 1:
            raise ValueError(
                f"recency_score must be in [0, 1], got {self.recency_score}"
            )
        if not 0 <= self.final_score <= 1:
            raise ValueError(
                f"final_score must be in [0, 1], got {self.final_score}"
            )
        if self.rank < 1:
            raise ValueError(f"rank must be >= 1, got {self.rank}")
        if self.start_line < 1:
            raise ValueError(f"start_line must be >= 1, got {self.start_line}")
        if self.end_line < self.start_line:
            raise ValueError(
                f"end_line ({self.end_line}) must be >= "
                f"start_line ({self.start_line})"
            )


@dataclass
class CommitDiff:
    """Diff information for a single commit.

    Represents changes made in a commit, used to provide context around
    retrieved code chunks.

    Attributes:
        commit_hash: Git commit SHA.
        author: Commit author name.
        message: Commit message/description.
        timestamp: When the commit was created (UTC).
        files_changed: List of file paths modified in this commit.
        diff_content: Full diff content for top commits, None for others.
    """

    commit_hash: str
    author: str
    message: str
    timestamp: datetime
    files_changed: list[str]
    diff_content: Optional[str] = None


@dataclass
class RetrievalResultList:
    """Complete response to webhook request.

    Top-level response object containing error context, retrieval results,
    related diffs, and metadata about the search operation.

    Attributes:
        error_context: The normalized error that was queried.
        retrieval_results: List of code chunks matching the error.
        related_diffs: Commit diffs for context.
        metadata: Search metadata including query, duration, timestamp.
    """

    error_context: ErrorContext
    retrieval_results: list[RetrievalResult]
    related_diffs: list[CommitDiff]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to JSON-serializable dictionary.

        Returns:
            Dictionary with all fields converted to JSON-compatible types.
        """
        return {
            "error_context": {
                "file_path": self.error_context.file_path,
                "line_number": self.error_context.line_number,
                "function_name": self.error_context.function_name,
                "error_type": self.error_context.error_type,
                "error_message": self.error_context.error_message,
            },
            "retrieval_results": [
                {
                    "rank": r.rank,
                    "file_path": r.file_path,
                    "start_line": r.start_line,
                    "end_line": r.end_line,
                    "code_snippet": r.code_snippet,
                    "commit_hash": r.commit_hash,
                    "commit_author": r.commit_author,
                    "commit_timestamp": r.commit_timestamp.isoformat(),
                    "function_name": r.function_name,
                    "score": r.final_score,
                    "recency_score": r.recency_score,
                }
                for r in self.retrieval_results
            ],
            "related_diffs": [
                {
                    "commit_hash": d.commit_hash,
                    "author": d.author,
                    "message": d.message,
                    "timestamp": d.timestamp.isoformat(),
                    "files_changed": d.files_changed,
                    "diff_content": d.diff_content,
                }
                for d in self.related_diffs
            ],
            "metadata": self.metadata,
        }
