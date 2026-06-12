"""Domain types for Git Debug Oracle."""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CodeChunk:
    """A chunk of code extracted from a repository file."""

    content: str
    file_path: str
    start_line: int
    end_line: int
    commit_hash: str
    commit_author: str
    commit_timestamp: datetime
    function_name: Optional[str]
    embedding: Optional[list[float]]
    chunk_id: str


@dataclass
class CommitDiff:
    """A diff from a single commit."""

    commit_hash: str
    commit_author: str
    commit_timestamp: datetime
    commit_message: str
    file_path: str
    diff_content: str
    additions: int
    deletions: int


@dataclass
class ErrorPayload:
    """Structured error information from external systems."""

    error_type: str
    error_message: str
    file_path: Optional[str]
    line_number: Optional[int]
    function_name: Optional[str]
    stacktrace: str
    timestamp: datetime
    source_system: Optional[str]
    additional_context: dict[str, str]


@dataclass
class RetrievalResult:
    """A single result from vector search."""

    chunk: CodeChunk
    score: float
    recency_score: float
    combined_score: float
    rank: int


@dataclass
class FixProposal:
    """A proposed fix for an error with reasoning."""

    root_cause: str
    affected_file: str
    affected_line_range: tuple[int, int]
    code_patch: str
    patch_language: str
    confidence: float
    explanation: str
    affected_functions: list[str]
    root_cause_category: str
    alternative_fixes: list['FixProposal'] = None

    def __post_init__(self) -> None:
        """Initialize alternative_fixes if None."""
        if self.alternative_fixes is None:
            self.alternative_fixes = []


@dataclass
class IndexStatus:
    """Current state of the repository index."""

    is_indexed: bool
    last_indexed_commit: str
    last_indexed_timestamp: datetime
    total_chunks: int
    total_files: int
    branch: str
    status: str


@dataclass
class RepoConfig:
    """Repository-specific configuration."""

    repo_path: str
    watch_branch: str
    file_extensions: list[str]
    exclude_patterns: list[str]
    chunk_size: int
    chunk_overlap: int
