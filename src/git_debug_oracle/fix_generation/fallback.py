"""Fallback strategies: graceful degradation when Claude API unavailable."""

import logging
from typing import Optional

from git_debug_oracle.types import FixProposal, RetrievalResult

logger = logging.getLogger(__name__)


def create_fallback_fix(
    affected_file: str,
    affected_line: int,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> FixProposal:
    """Create minimal fallback fix when Claude API unavailable.

    Args:
        affected_file: File where error occurred
        affected_line: Line number
        error_type: Optional error type
        error_message: Optional error message

    Returns:
        FixProposal with low confidence and generic explanation

    """
    explanation = f"Unable to generate fix due to API unavailability. "
    explanation += f"Review {affected_file} around line {affected_line}. "
    if error_type:
        explanation += f"Error type: {error_type}. "
    if error_message:
        explanation += f"Message: {error_message}"

    return FixProposal(
        root_cause="Unknown (API unavailable)",
        affected_file=affected_file,
        affected_line_range=(affected_line, affected_line + 5),
        code_patch="",
        patch_language="python",
        confidence=0.2,
        explanation=explanation,
        affected_functions=[],
        root_cause_category="unknown",
        alternative_fixes=[],
    )


def create_retrieval_only_fix(
    retrieval_results: list[RetrievalResult],
    affected_file: str,
    affected_line: int,
) -> Optional[FixProposal]:
    """Create fix proposal from retrieval results only (no Claude analysis).

    Args:
        retrieval_results: Retrieved code chunks
        affected_file: File where error occurred
        affected_line: Line number

    Returns:
        FixProposal based on top retrieval result, or None if no results

    """
    if not retrieval_results:
        return None

    top_result = retrieval_results[0]
    chunk = top_result.chunk

    explanation = (
        f"Based on similar code patterns in {chunk.file_path} "
        f"(author: {chunk.commit_author}). "
        f"Review retrieved code chunks for context. "
        f"Manual fix proposal needed."
    )

    return FixProposal(
        root_cause=f"Error in {affected_file} line {affected_line}",
        affected_file=affected_file,
        affected_line_range=(affected_line, affected_line + 5),
        code_patch=chunk.content[:500],  # Truncate
        patch_language="python",
        confidence=top_result.combined_score * 0.6,  # Reduce confidence
        explanation=explanation,
        affected_functions=chunk.function_name and [chunk.function_name] or [],
        root_cause_category="unknown",
        alternative_fixes=[],
    )


def handle_parse_failure(response: str) -> FixProposal:
    """Handle fix proposal parser failure.

    Args:
        response: Claude response that failed to parse

    Returns:
        FixProposal with full response as explanation, low confidence

    """
    logger.warning("Fix proposal parsing failed, returning raw response")

    return FixProposal(
        root_cause="Unable to parse fix proposal",
        affected_file="",
        affected_line_range=(0, 0),
        code_patch="",
        patch_language="python",
        confidence=0.3,
        explanation=f"Unparseable response: {response[:500]}",
        affected_functions=[],
        root_cause_category="unknown",
        alternative_fixes=[],
    )


def handle_context_assembly_failure(
    affected_file: str,
    affected_line: int,
    error: Exception,
) -> FixProposal:
    """Handle context assembly failure.

    Args:
        affected_file: File where error occurred
        affected_line: Line number
        error: Exception that occurred

    Returns:
        FixProposal with error message

    """
    logger.error(f"Context assembly failed: {error}")

    return FixProposal(
        root_cause="Unable to assemble context",
        affected_file=affected_file,
        affected_line_range=(affected_line, affected_line + 5),
        code_patch="",
        patch_language="python",
        confidence=0.1,
        explanation=f"Failed to assemble error context: {str(error)[:200]}. "
        f"Please manually review {affected_file} around line {affected_line}.",
        affected_functions=[],
        root_cause_category="unknown",
        alternative_fixes=[],
    )
