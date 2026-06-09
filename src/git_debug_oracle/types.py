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
    affected_lines: tuple[int, int]
    introducing_commit: str
    code_patch: str
    explanation: str
    confidence: float
    reasoning_trace: list[str]


@dataclass
class IndexStatus:
    """Current state of the repository index."""

    repo_path: str
    branch: str
    last_indexed_commit: str
    last_indexed_timestamp: datetime
    total_chunks: int
    total_files: int
    collection_name: str
    is_indexing: bool


@dataclass
class RepoConfig:
    """Repository-specific configuration."""

    repo_path: str
    watch_branch: str
    file_extensions: list[str]
    exclude_patterns: list[str]
    chunk_size: int
    chunk_overlap: int
