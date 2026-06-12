"""Context assembler: combine error info and retrieval results into Claude prompt."""

from datetime import datetime, timezone
from typing import Optional

from git_debug_oracle.types import CommitDiff, ErrorPayload, RetrievalResult


def assemble_context(
    error: ErrorPayload,
    retrieval_results: list[RetrievalResult],
    diffs: list[CommitDiff],
    max_tokens: int = 4000,
) -> str:
    """Assemble error context and retrieval results into prompt context.

    Args:
        error: The error payload containing error metadata
        retrieval_results: Top code chunks from vector search
        diffs: Recent commit diffs for context
        max_tokens: Maximum tokens in output (approximate)

    Returns:
        Formatted context string suitable for Claude API

    """
    parts: list[str] = []

    # Error metadata section
    parts.append("## ERROR INFORMATION")
    parts.append(f"File: {error.file_path}")
    if error.line_number:
        parts.append(f"Line: {error.line_number}")
    if error.function_name:
        parts.append(f"Function: {error.function_name}")
    if error.error_type:
        parts.append(f"Error Type: {error.error_type}")
    if error.error_message:
        parts.append(f"Error Message: {error.error_message}")

    # Stacktrace section
    if error.stacktrace:
        parts.append("\n## STACKTRACE")
        parts.append(error.stacktrace)

    # Retrieved code sections
    if retrieval_results:
        parts.append("\n## RELEVANT CODE CHUNKS")
        for i, result in enumerate(retrieval_results[:3], 1):
            chunk = result.chunk
            parts.append(f"\n### Chunk {i} (Score: {result.combined_score:.2f})")
            parts.append(f"File: {chunk.file_path} ({chunk.start_line}-{chunk.end_line})")
            if chunk.function_name:
                parts.append(f"Function: {chunk.function_name}")
            parts.append(f"Author: {chunk.commit_author}")
            parts.append(f"Commit: {chunk.commit_hash}")
            parts.append("```")
            parts.append(chunk.content)
            parts.append("```")

    # Recent changes section
    if diffs:
        parts.append("\n## RECENT CHANGES")
        for diff in diffs[:3]:
            parts.append(f"\nCommit: {diff.commit_hash[:7]}")
            parts.append(f"Author: {diff.commit_author}")
            parts.append(f"File: {diff.file_path}")
            parts.append(f"Message: {diff.commit_message}")
            if diff.diff_content:
                parts.append("```diff")
                # Truncate large diffs
                diff_lines = diff.diff_content.split("\n")[:20]
                parts.append("\n".join(diff_lines))
                if len(diff.diff_content.split("\n")) > 20:
                    parts.append("... (truncated)")
                parts.append("```")

    context = "\n".join(parts)

    # Truncate if exceeds token limit (approximate: 1 token ≈ 4 chars)
    max_chars = max_tokens * 4
    if len(context) > max_chars:
        context = context[:max_chars] + "\n... (truncated)"

    return context


def format_claude_prompt(
    error: ErrorPayload,
    retrieval_results: list[RetrievalResult],
    diffs: list[CommitDiff],
) -> str:
    """Format complete Claude API prompt with system and context.

    Args:
        error: Error payload
        retrieval_results: Retrieved code chunks
        diffs: Recent commit diffs

    Returns:
        Complete prompt string for Claude API

    """
    system_prompt = (
        "You are a debugging expert. Analyze the error and provided code context "
        "to identify the root cause and propose a fix.\n\n"
        "Respond with:\n"
        "1. ROOT CAUSE: Single sentence explaining why the error occurred\n"
        "2. FIX: Code patch showing the fix\n"
        "3. CONFIDENCE: Number 0-1 or percentage indicating fix quality\n"
        "4. EXPLANATION: Brief explanation of the fix\n\n"
        "Format code patches between triple backticks with language specified."
    )

    context = assemble_context(error, retrieval_results, diffs)

    return f"{system_prompt}\n\n{context}"


def extract_error_context_dict(error: ErrorPayload) -> dict[str, any]:
    """Convert ErrorPayload to output dict for API response.

    Args:
        error: Error payload

    Returns:
        Dictionary with error context fields

    """
    return {
        "file_path": error.file_path,
        "line_number": error.line_number,
        "function_name": error.function_name,
        "error_type": error.error_type,
        "error_message": error.error_message,
    }
