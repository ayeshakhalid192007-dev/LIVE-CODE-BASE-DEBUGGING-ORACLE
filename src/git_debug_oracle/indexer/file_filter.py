"""File type filtering for indexing pipeline."""

import re
from pathlib import Path
from typing import Optional

from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = 1_048_576
PYTHON_EXTENSION = ".py"


def should_index_file(file_path: str, file_content: str) -> bool:
    """Determine if a file should be indexed.

    Args:
        file_path: Relative path to file in repository
        file_content: Content of the file

    Returns:
        True if file should be indexed, False otherwise
    """
    if not has_python_extension(file_path):
        logger.debug("Skipping non-Python file", file_path=file_path, reason="extension")
        return False

    if is_binary_file(file_content):
        logger.debug("Skipping binary file", file_path=file_path, reason="binary")
        return False

    if is_file_too_large(file_content):
        logger.debug(
            "Skipping large file",
            file_path=file_path,
            reason="size",
            size=len(file_content),
        )
        return False

    logger.debug("File accepted for indexing", file_path=file_path)
    return True


def has_python_extension(file_path: str) -> bool:
    """Check if file has Python extension.

    Args:
        file_path: Relative path to file

    Returns:
        True if file has .py extension, False otherwise
    """
    return file_path.endswith(PYTHON_EXTENSION)


def is_binary_file(file_content: str) -> bool:
    """Check if file content is binary.

    Args:
        file_content: Content of the file

    Returns:
        True if file contains null bytes (binary), False otherwise
    """
    return "\x00" in file_content


def is_file_too_large(file_content: str) -> bool:
    """Check if file exceeds maximum size.

    Args:
        file_content: Content of the file

    Returns:
        True if file exceeds 1MB, False otherwise
    """
    file_size = len(file_content.encode("utf-8"))
    return file_size > MAX_FILE_SIZE_BYTES


def get_gitignore_patterns(repo_path: str) -> list[str]:
    """Load gitignore patterns from repository.

    Args:
        repo_path: Absolute path to repository

    Returns:
        List of gitignore patterns
    """
    gitignore_path = Path(repo_path) / ".gitignore"

    if not gitignore_path.exists():
        logger.debug("No .gitignore file found", repo_path=repo_path)
        return []

    try:
        with open(gitignore_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        patterns = []
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)

        logger.debug(
            "Loaded gitignore patterns",
            repo_path=repo_path,
            pattern_count=len(patterns),
        )
        return patterns

    except Exception as e:
        logger.error(
            "Failed to read .gitignore",
            repo_path=repo_path,
            error=str(e),
        )
        return []


def matches_gitignore(file_path: str, patterns: list[str]) -> bool:
    """Check if file path matches any gitignore pattern.

    Args:
        file_path: Relative path to file
        patterns: List of gitignore patterns

    Returns:
        True if file matches any pattern, False otherwise
    """
    for pattern in patterns:
        if matches_pattern(file_path, pattern):
            logger.debug(
                "File matches gitignore pattern",
                file_path=file_path,
                pattern=pattern,
            )
            return True

    return False


def matches_pattern(file_path: str, pattern: str) -> bool:
    """Check if file path matches a gitignore pattern.

    Args:
        file_path: Relative path to file
        pattern: Gitignore pattern

    Returns:
        True if file matches pattern, False otherwise
    """
    if pattern.endswith("/"):
        pattern = pattern.rstrip("/")
        return file_path.startswith(pattern + "/")

    if "/" in pattern:
        regex_pattern = pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
        return bool(re.match(regex_pattern, file_path))

    filename = Path(file_path).name
    regex_pattern = pattern.replace(".", r"\.").replace("*", ".*").replace("?", ".")
    return bool(re.match(regex_pattern, filename))


def should_index_file_with_gitignore(
    file_path: str, file_content: str, repo_path: str
) -> bool:
    """Determine if file should be indexed, respecting gitignore.

    Args:
        file_path: Relative path to file in repository
        file_content: Content of the file
        repo_path: Absolute path to repository

    Returns:
        True if file should be indexed, False otherwise
    """
    if not should_index_file(file_path, file_content):
        return False

    patterns = get_gitignore_patterns(repo_path)
    if matches_gitignore(file_path, patterns):
        logger.debug(
            "Skipping file matching gitignore",
            file_path=file_path,
            reason="gitignore",
        )
        return False

    return True
