"""Pydantic schemas for MCP tool contracts (v1.0 stable)."""

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class DebugErrorInput(BaseModel):
    """Input schema for debug_error MCP tool."""

    file_path: str = Field(..., description="Path to file where error occurred")
    line_number: int = Field(..., description="Line number where error occurred", gt=0)
    function_name: Optional[str] = Field(None, description="Function name if available")
    error_type: Optional[str] = Field(None, description="Error type (e.g., ValueError)")
    error_message: Optional[str] = Field(None, description="Error message text")
    stacktrace: Optional[str] = Field(None, description="Full stacktrace")
    language: Optional[str] = Field(None, description="Programming language")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "file_path": "src/app.py",
                "line_number": 42,
                "error_type": "IndexError",
                "error_message": "list index out of range",
                "language": "python",
            }
        }


class ErrorContextOutput(BaseModel):
    """Error context in output."""

    file_path: str
    line_number: int
    function_name: Optional[str] = None
    error_type: Optional[str] = None
    error_message: Optional[str] = None


class RetrievalResultOutput(BaseModel):
    """Single retrieval result in output."""

    rank: int
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str
    commit_hash: str
    commit_author: str
    commit_timestamp: str
    function_name: Optional[str] = None
    score: float


class FixProposalOutput(BaseModel):
    """Fix proposal in output."""

    root_cause: str
    affected_file: str
    affected_line_range: tuple[int, int]
    code_patch: str
    patch_language: str
    confidence: float
    explanation: str
    affected_functions: list[str]
    root_cause_category: str


class DebugErrorOutput(BaseModel):
    """Output schema for debug_error MCP tool."""

    error_context: ErrorContextOutput
    retrieval_results: list[RetrievalResultOutput]
    fix_proposal: Optional[FixProposalOutput] = None
    status: str = Field(..., description="success, partial, or failed")

    @validator("status")
    def status_valid(cls, v: str) -> str:
        """Validate status value."""
        if v not in ("success", "partial", "failed"):
            raise ValueError("status must be 'success', 'partial', or 'failed'")
        return v

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "error_context": {
                    "file_path": "src/app.py",
                    "line_number": 42,
                },
                "retrieval_results": [],
                "fix_proposal": {
                    "root_cause": "Off-by-one error",
                    "affected_file": "src/app.py",
                    "affected_line_range": [42, 45],
                    "code_patch": "for i in range(len(items) - 1):",
                    "patch_language": "python",
                    "confidence": 0.85,
                    "explanation": "...",
                    "affected_functions": ["process_items"],
                    "root_cause_category": "logic",
                },
                "status": "success",
            }
        }


class GetIndexStatusInput(BaseModel):
    """Input schema for get_index_status MCP tool."""

    branch: Optional[str] = Field(None, description="Branch to check (defaults to current)")

    class Config:
        """Pydantic config."""

        schema_extra = {"example": {"branch": "main"}}


class IndexStatusOutput(BaseModel):
    """Output schema for get_index_status MCP tool."""

    is_indexed: bool = Field(..., description="Whether repo is indexed")
    last_indexed_commit: str = Field(..., description="Commit hash of last index")
    last_indexed_timestamp: str = Field(..., description="ISO8601 timestamp of last index")
    total_chunks: int = Field(..., description="Total chunks in index")
    total_files: int = Field(..., description="Total files indexed")
    branch: str = Field(..., description="Branch name")
    status: str = Field(..., description="indexed, not_indexed, indexing, or failed")

    @validator("status")
    def status_valid(cls, v: str) -> str:
        """Validate status value."""
        if v not in ("indexed", "not_indexed", "indexing", "failed"):
            raise ValueError("status must be indexed, not_indexed, indexing, or failed")
        return v

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "is_indexed": True,
                "last_indexed_commit": "abc123def456",
                "last_indexed_timestamp": "2026-06-12T10:30:00Z",
                "total_chunks": 5000,
                "total_files": 150,
                "branch": "main",
                "status": "indexed",
            }
        }


class SearchCodebaseInput(BaseModel):
    """Input schema for search_codebase MCP tool (v1.0 stable)."""

    query: str = Field(..., description="Search query text")
    top_k: Optional[int] = Field(5, description="Number of results", ge=1, le=20)
    file_filter: Optional[str] = Field(None, description="Optional file path filter")

    class Config:
        """Pydantic config."""

        schema_extra = {
            "example": {
                "query": "authentication error handling",
                "top_k": 5,
            }
        }


class SearchCodebaseOutput(BaseModel):
    """Output schema for search_codebase MCP tool (v1.0 stable)."""

    results: list[RetrievalResultOutput]
    query_used: str
    total_searched: int
    status: str

    @validator("status")
    def status_valid(cls, v: str) -> str:
        """Validate status."""
        if v not in ("success", "partial", "failed"):
            raise ValueError("status must be success, partial, or failed")
        return v


class CommitDiffOutput(BaseModel):
    """Single commit diff."""

    commit_hash: str
    author: str
    message: str
    timestamp: str
    files_changed: list[str]
    diff_content: Optional[str] = None


class GetRecentDiffsInput(BaseModel):
    """Input schema for get_recent_diffs MCP tool (v1.0 stable)."""

    num_commits: Optional[int] = Field(5, description="Number of commits", ge=1, le=20)
    branch: Optional[str] = Field(None, description="Branch name")

    class Config:
        """Pydantic config."""

        schema_extra = {"example": {"num_commits": 5, "branch": "main"}}


class GetRecentDiffsOutput(BaseModel):
    """Output schema for get_recent_diffs MCP tool (v1.0 stable)."""

    diffs: list[CommitDiffOutput]
    branch: str
    status: str

    @validator("status")
    def status_valid(cls, v: str) -> str:
        """Validate status."""
        if v not in ("success", "partial", "failed"):
            raise ValueError("status must be success, partial, or failed")
        return v
