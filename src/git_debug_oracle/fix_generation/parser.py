"""Fix proposal parser: extract structured fixes from Claude API responses."""

import re
from typing import Optional

from git_debug_oracle.types import FixProposal


def parse_fix_response(response: str) -> FixProposal:
    """Parse Claude API response into FixProposal.

    Extracts root cause, code patch, confidence, and explanation from Claude response.
    Handles various formatting variations and malformed responses gracefully.

    Args:
        response: Raw text response from Claude API

    Returns:
        FixProposal with extracted data

    """
    root_cause = _extract_root_cause(response)
    code_patch, patch_language = _extract_code_patch(response)
    confidence = _extract_confidence(response)
    explanation = _extract_explanation(response)

    # Determine confidence quality based on extracted data
    if not code_patch or not root_cause:
        confidence = min(confidence, 0.4)

    return FixProposal(
        root_cause=root_cause or "Unable to determine root cause",
        affected_file="",
        affected_line_range=(0, 0),
        code_patch=code_patch or "",
        patch_language=patch_language,
        confidence=confidence,
        explanation=explanation or response[:500],
        affected_functions=[],
        root_cause_category="unknown",
        alternative_fixes=[],
    )


def _extract_root_cause(response: str) -> Optional[str]:
    """Extract root cause from response.

    Args:
        response: Claude response text

    Returns:
        Root cause string or None

    """
    patterns = [
        r"ROOT CAUSE:\s*(.+?)(?:\n|$)",
        r"ROOT CAUSE[:\s]*(.+?)(?:\n|$)",
        r"root cause:\s*(.+?)(?:\n|$)",
        r"The root cause is:\s*(.+?)(?:\n|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def _extract_code_patch(response: str) -> tuple[Optional[str], str]:
    """Extract code patch from response.

    Looks for code blocks marked with triple backticks and language specifiers.
    Returns first code block found.

    Args:
        response: Claude response text

    Returns:
        Tuple of (code_patch, language) where language defaults to 'python'

    """
    # Pattern: ```language ... ```
    pattern = r"```(\w+)?\s*\n(.*?)\n```"
    matches = re.findall(pattern, response, re.DOTALL)

    if matches:
        language, code = matches[0]
        return code.strip(), language or "python"

    # Fallback: any triple backtick block
    pattern_fallback = r"```\s*\n(.*?)\n```"
    match = re.search(pattern_fallback, response, re.DOTALL)
    if match:
        return match.group(1).strip(), "python"

    return None, "python"


def _extract_confidence(response: str) -> float:
    """Extract confidence score from response.

    Handles formats like:
    - Confidence: 0.85
    - Confidence: 85%
    - confidence: 85

    Args:
        response: Claude response text

    Returns:
        Confidence float 0-1, defaults to 0.5 if not found

    """
    patterns = [
        r"CONFIDENCE:\s*([\d.]+)%?",
        r"confidence:\s*([\d.]+)%?",
        r"Confidence:\s*([\d.]+)%?",
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE)
        if match:
            value = float(match.group(1))
            # Convert percentage to decimal if needed
            if value > 1.0:
                value = value / 100.0
            return min(max(value, 0.0), 1.0)

    # Try to extract from text like "I'm 90% confident"
    percentage_pattern = r"(\d+)%\s*confident"
    match = re.search(percentage_pattern, response, re.IGNORECASE)
    if match:
        value = float(match.group(1)) / 100.0
        return min(max(value, 0.0), 1.0)

    return 0.5


def _extract_explanation(response: str) -> Optional[str]:
    """Extract explanation text from response.

    Looks for explanation after specific markers or uses response text.

    Args:
        response: Claude response text

    Returns:
        Explanation string or None

    """
    patterns = [
        r"EXPLANATION:\s*(.+?)(?:\n[A-Z]|$)",
        r"explanation:\s*(.+?)(?:\n[A-Z]|$)",
        r"Explanation:\s*(.+?)(?:\n[A-Z]|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, response, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()

    # Extract paragraphs after code block
    lines = response.split("\n")
    explanation_lines = []
    in_code = False

    for line in lines:
        if "```" in line:
            in_code = not in_code
            continue
        if not in_code and line.strip() and not re.match(r"^[A-Z\d]+:", line):
            explanation_lines.append(line)

    if explanation_lines:
        return " ".join(explanation_lines).strip()[:500]

    return None
