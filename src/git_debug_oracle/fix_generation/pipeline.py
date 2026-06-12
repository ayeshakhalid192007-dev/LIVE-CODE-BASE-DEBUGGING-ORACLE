"""Main fix generation pipeline: orchestrate all components."""

import logging
from typing import Optional

from git_debug_oracle.fix_generation.claude_client import ClaudeClient
from git_debug_oracle.fix_generation.context import assemble_context, extract_error_context_dict
from git_debug_oracle.fix_generation.fallback import (
    create_fallback_fix,
    create_retrieval_only_fix,
    handle_context_assembly_failure,
    handle_parse_failure,
)
from git_debug_oracle.fix_generation.parser import parse_fix_response
from git_debug_oracle.fix_generation.scoring import (
    calculate_confidence,
    calculate_error_coverage,
    extract_claude_certainty,
    validate_code_patch,
)
from git_debug_oracle.types import CommitDiff, ErrorPayload, FixProposal, RetrievalResult

logger = logging.getLogger(__name__)


class FixGenerationPipeline:
    """Orchestrate fix generation from error to proposal."""

    def __init__(self, claude_client: ClaudeClient):
        """Initialize pipeline.

        Args:
            claude_client: Claude API client

        """
        self.claude = claude_client

    def generate_fix(
        self,
        error: ErrorPayload,
        retrieval_results: list[RetrievalResult],
        diffs: list[CommitDiff],
    ) -> FixProposal:
        """Generate fix proposal from error and retrieval results.

        Full pipeline:
        1. Assemble context
        2. Call Claude API
        3. Parse response
        4. Score confidence
        5. Return fix or fallback

        Args:
            error: Error payload
            retrieval_results: Retrieved code chunks
            diffs: Recent commit diffs

        Returns:
            FixProposal with confidence and explanation

        """
        try:
            # Step 1: Assemble context
            context = assemble_context(error, retrieval_results, diffs)
            system_prompt = self.claude.get_system_prompt()

        except Exception as e:
            logger.error(f"Context assembly failed: {e}")
            return handle_context_assembly_failure(
                error.file_path or "unknown",
                error.line_number or 0,
                e,
            )

        # Step 2: Call Claude API
        if self.claude.is_circuit_open():
            logger.warning("Claude API circuit breaker open, using fallback")
            if retrieval_results:
                fallback = create_retrieval_only_fix(
                    retrieval_results,
                    error.file_path or "unknown",
                    error.line_number or 0,
                )
                if fallback:
                    return fallback

            return create_fallback_fix(
                error.file_path or "unknown",
                error.line_number or 0,
                error.error_type,
                error.error_message,
            )

        response = self.claude.call_with_caching(system_prompt, context)

        if not response:
            logger.warning("Claude API call failed, using fallback")
            if retrieval_results:
                fallback = create_retrieval_only_fix(
                    retrieval_results,
                    error.file_path or "unknown",
                    error.line_number or 0,
                )
                if fallback:
                    return fallback

            return create_fallback_fix(
                error.file_path or "unknown",
                error.line_number or 0,
                error.error_type,
                error.error_message,
            )

        # Step 3: Parse response
        try:
            fix = parse_fix_response(response)
        except Exception as e:
            logger.error(f"Fix parsing failed: {e}")
            return handle_parse_failure(response)

        # Step 4: Update fix with error context
        fix.affected_file = error.file_path or fix.affected_file
        fix.affected_line_range = (
            error.line_number or fix.affected_line_range[0],
            (error.line_number or fix.affected_line_range[0]) + 5,
        )

        # Step 5: Score confidence
        retrieval_score = (
            max([r.combined_score for r in retrieval_results], default=0.5)
            if retrieval_results
            else 0.5
        )
        claude_certainty = extract_claude_certainty(response)
        patch_validity = validate_code_patch(fix.code_patch, fix.patch_language)
        error_coverage = calculate_error_coverage(
            fix.root_cause,
            error.error_type,
            error.error_message,
        )

        fix.confidence = calculate_confidence(
            retrieval_score,
            claude_certainty,
            patch_validity,
            error_coverage,
        )

        logger.info(
            f"Fix generated",
            extra={
                "confidence": fix.confidence,
                "root_cause_category": fix.root_cause_category,
                "patch_length": len(fix.code_patch),
            },
        )

        return fix
