"""Chunk metadata extraction and ID generation."""

import hashlib
from datetime import datetime
from typing import Any

from git_debug_oracle.types import CodeChunk
from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)


def generate_chunk_id(
    file_path: str, start_line: int, end_line: int, commit_hash: str
) -> str:
    """Generate deterministic chunk ID from file path, line range, and commit hash.

    Args:
        file_path: Relative path to file in repository
        start_line: Starting line number (1-indexed)
        end_line: Ending line number (1-indexed)
        commit_hash: Git commit hash

    Returns:
        SHA256 hash as hexadecimal string
    """
    chunk_key = f"{file_path}:{start_line}-{end_line}:{commit_hash}"
    chunk_id = hashlib.sha256(chunk_key.encode("utf-8")).hexdigest()

    logger.debug(
        "Generated chunk ID",
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        commit_hash=commit_hash[:8],
        chunk_id=chunk_id[:16],
    )

    return chunk_id


def extract_chunk_metadata(
    chunk_dict: dict[str, Any], file_path: str, commit_metadata: dict[str, str]
) -> CodeChunk:
    """Extract chunk metadata and create CodeChunk instance.

    Args:
        chunk_dict: Dictionary from chunker with keys: content, start_line, end_line, function_name
        file_path: Relative path to file in repository
        commit_metadata: Dictionary with keys: hash, author, timestamp, message

    Returns:
        CodeChunk instance with all fields populated
    """
    content = chunk_dict["content"]
    start_line = chunk_dict["start_line"]
    end_line = chunk_dict["end_line"]
    function_name = chunk_dict.get("function_name")

    commit_hash = commit_metadata["hash"]
    commit_author = commit_metadata["author"]
    commit_timestamp_str = commit_metadata["timestamp"]
    commit_timestamp = datetime.fromisoformat(commit_timestamp_str)

    chunk_id = generate_chunk_id(file_path, start_line, end_line, commit_hash)

    chunk = CodeChunk(
        content=content,
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        commit_hash=commit_hash,
        commit_author=commit_author,
        commit_timestamp=commit_timestamp,
        function_name=function_name,
        embedding=None,
        chunk_id=chunk_id,
    )

    logger.debug(
        "Extracted chunk metadata",
        file_path=file_path,
        start_line=start_line,
        end_line=end_line,
        function_name=function_name,
        chunk_id=chunk_id[:16],
    )

    return chunk
