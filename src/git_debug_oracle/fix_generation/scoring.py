"""Confidence scoring: rate quality of fix proposals based on multiple factors."""

from typing import Optional


def calculate_confidence(
    retrieval_score: float,
    claude_certainty: float,
    patch_validity: float,
    error_coverage: float,
) -> float:
    """Calculate overall confidence score for fix proposal.

    Combines multiple factors with weighted average:
    - Retrieval score (40%): How relevant were code chunks
    - Claude certainty (30%): Confidence markers in response
    - Patch validity (20%): Code syntax and structure
    - Error coverage (10%): Does fix address root cause

    Args:
        retrieval_score: 0-1 score from vector search
        claude_certainty: 0-1 certainty from response text
        patch_validity: 0-1 validity of code patch
        error_coverage: 0-1 coverage of error

    Returns:
        Combined confidence score 0-1

    """
    weights = {
        "retrieval": 0.4,
        "claude": 0.3,
        "patch": 0.2,
        "coverage": 0.1,
    }

    # Clamp all inputs to 0-1
    retrieval_score = max(0.0, min(1.0, retrieval_score))
    claude_certainty = max(0.0, min(1.0, claude_certainty))
    patch_validity = max(0.0, min(1.0, patch_validity))
    error_coverage = max(0.0, min(1.0, error_coverage))

    confidence = (
        retrieval_score * weights["retrieval"]
        + claude_certainty * weights["claude"]
        + patch_validity * weights["patch"]
        + error_coverage * weights["coverage"]
    )

    return max(0.0, min(1.0, confidence))


def extract_claude_certainty(response: str) -> float:
    """Extract certainty markers from Claude response text.

    Analyzes response for confidence indicators:
    - "confident" → 0.9
    - "likely" → 0.7
    - "probably" → 0.6
    - "uncertain" → 0.3
    - "unclear" → 0.2

    Args:
        response: Claude response text

    Returns:
        Certainty score 0-1

    """
    response_lower = response.lower()

    certainty_indicators = {
        "confident": 0.9,
        "highly confident": 0.95,
        "definitely": 0.9,
        "certain": 0.85,
        "almost certainly": 0.85,
        "likely": 0.7,
        "probably": 0.6,
        "should": 0.65,
        "may": 0.5,
        "might": 0.45,
        "could": 0.4,
        "uncertain": 0.3,
        "unclear": 0.2,
        "unsure": 0.25,
    }

    max_certainty = 0.5  # Default if no markers found

    for marker, score in certainty_indicators.items():
        if marker in response_lower:
            max_certainty = max(max_certainty, score)

    return min(max_certainty, 1.0)


def validate_code_patch(code_patch: str, language: str = "python") -> float:
    """Validate code patch syntax and structure.

    Basic validation checks:
    - Patch is not empty
    - Contains keywords appropriate for language
    - Doesn't have obvious syntax errors

    Args:
        code_patch: Code snippet to validate
        language: Programming language

    Returns:
        Validity score 0-1

    """
    if not code_patch or not code_patch.strip():
        return 0.0

    patch_lines = code_patch.strip().split("\n")

    # Check for reasonable length
    if len(patch_lines) > 100:
        return 0.7  # Long patches less reliable

    validity = 0.8  # Start with baseline

    # Language-specific checks
    if language == "python":
        validity = _validate_python(code_patch, validity)
    elif language in ("javascript", "typescript"):
        validity = _validate_javascript(code_patch, validity)
    elif language == "java":
        validity = _validate_java(code_patch, validity)
    elif language == "go":
        validity = _validate_go(code_patch, validity)

    return min(max(validity, 0.0), 1.0)


def _validate_python(code_patch: str, base_validity: float) -> float:
    """Validate Python code patch."""
    validity = base_validity

    # Check for common patterns
    if any(x in code_patch for x in ["def ", "class ", "if ", "for ", "while "]):
        validity = min(1.0, validity + 0.1)

    # Check for obvious errors
    if code_patch.count("(") != code_patch.count(")"):
        validity -= 0.2

    if code_patch.count("[") != code_patch.count("]"):
        validity -= 0.2

    return validity


def _validate_javascript(code_patch: str, base_validity: float) -> float:
    """Validate JavaScript code patch."""
    validity = base_validity

    if any(x in code_patch for x in ["function ", "const ", "let ", "if ", "for "]):
        validity = min(1.0, validity + 0.1)

    if code_patch.count("{") != code_patch.count("}"):
        validity -= 0.2

    if code_patch.count("(") != code_patch.count(")"):
        validity -= 0.2

    return validity


def _validate_java(code_patch: str, base_validity: float) -> float:
    """Validate Java code patch."""
    validity = base_validity

    if any(x in code_patch for x in ["public ", "private ", "class ", "if ", "for "]):
        validity = min(1.0, validity + 0.1)

    if code_patch.count("{") != code_patch.count("}"):
        validity -= 0.2

    return validity


def _validate_go(code_patch: str, base_validity: float) -> float:
    """Validate Go code patch."""
    validity = base_validity

    if any(x in code_patch for x in ["func ", "if ", "for ", "package "]):
        validity = min(1.0, validity + 0.1)

    if code_patch.count("{") != code_patch.count("}"):
        validity -= 0.2

    return validity


def calculate_error_coverage(
    root_cause: str,
    error_type: Optional[str] = None,
    error_message: Optional[str] = None,
) -> float:
    """Calculate how well fix addresses the error.

    Args:
        root_cause: Root cause statement
        error_type: Original error type
        error_message: Original error message

    Returns:
        Coverage score 0-1

    """
    coverage = 0.5  # Baseline

    if not root_cause or not root_cause.strip():
        return 0.0

    # Match error type in root cause
    if error_type and error_type.lower() in root_cause.lower():
        coverage += 0.25

    # Match error message keywords in root cause
    if error_message:
        keywords = error_message.lower().split()[:3]
        matches = sum(1 for kw in keywords if kw in root_cause.lower())
        coverage += (matches / len(keywords)) * 0.25

    return min(coverage, 1.0)
