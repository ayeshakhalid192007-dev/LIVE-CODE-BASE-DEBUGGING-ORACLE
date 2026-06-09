"""AST-based code chunking for Python files."""

import ast
from typing import Any, Optional

from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)


def parse_python_file(content: str) -> Optional[ast.Module]:
    """Parse Python file content into AST.

    Args:
        content: Python source code

    Returns:
        AST Module if parsing succeeds, None if parsing fails
    """
    try:
        tree = ast.parse(content)
        logger.debug("Successfully parsed Python file")
        return tree
    except SyntaxError as e:
        logger.error(
            "Failed to parse Python file",
            error=str(e),
            line=e.lineno,
            offset=e.offset,
        )
        return None
    except Exception as e:
        logger.error("Unexpected error parsing Python file", error=str(e))
        return None


def extract_functions(ast_tree: ast.Module) -> list[ast.FunctionDef]:
    """Extract all function and method definitions from AST.

    Args:
        ast_tree: Parsed AST module

    Returns:
        List of FunctionDef nodes
    """
    functions: list[ast.FunctionDef] = []

    for node in ast.walk(ast_tree):
        if isinstance(node, ast.FunctionDef):
            functions.append(node)

    logger.debug("Extracted functions from AST", count=len(functions))
    return functions


def get_function_lines(func_node: ast.FunctionDef, source_lines: list[str]) -> tuple[int, int]:
    """Get start and end line numbers for a function.

    Args:
        func_node: FunctionDef AST node
        source_lines: List of source code lines

    Returns:
        Tuple of (start_line, end_line) (1-indexed)
    """
    start_line = func_node.lineno
    end_line = func_node.end_lineno if func_node.end_lineno else start_line

    return start_line, end_line


def get_function_content(
    func_node: ast.FunctionDef, source_lines: list[str]
) -> str:
    """Extract function content from source lines.

    Args:
        func_node: FunctionDef AST node
        source_lines: List of source code lines

    Returns:
        Function content as string
    """
    start_line, end_line = get_function_lines(func_node, source_lines)

    function_lines = source_lines[start_line - 1 : end_line]
    content = "".join(function_lines)

    return content


def chunk_function(
    func_node: ast.FunctionDef,
    source_lines: list[str],
    chunk_size: int,
    overlap: int,
) -> list[dict[str, Any]]:
    """Chunk a function into smaller pieces if it exceeds chunk_size.

    Args:
        func_node: FunctionDef AST node
        source_lines: List of source code lines
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of chunk dictionaries with keys: content, start_line, end_line, function_name
    """
    start_line, end_line = get_function_lines(func_node, source_lines)
    content = get_function_content(func_node, source_lines)
    function_name = func_node.name

    if len(content) <= chunk_size:
        return [
            {
                "content": content,
                "start_line": start_line,
                "end_line": end_line,
                "function_name": function_name,
            }
        ]

    logger.debug(
        "Function exceeds chunk size, keeping as single chunk",
        function_name=function_name,
        size=len(content),
        chunk_size=chunk_size,
    )

    return [
        {
            "content": content,
            "start_line": start_line,
            "end_line": end_line,
            "function_name": function_name,
        }
    ]


def chunk_file(
    file_path: str, content: str, chunk_size: int, overlap: int
) -> list[dict[str, Any]]:
    """Chunk a Python file into logical units based on AST.

    Args:
        file_path: Path to file (for error reporting)
        content: File content
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of chunk dictionaries, or list with single error dict if parsing fails
    """
    ast_tree = parse_python_file(content)

    if ast_tree is None:
        logger.error("Failed to parse file, returning error chunk", file_path=file_path)
        return [
            {
                "content": "",
                "start_line": 0,
                "end_line": 0,
                "function_name": None,
                "error": "Failed to parse Python file",
                "file_path": file_path,
            }
        ]

    source_lines = content.splitlines(keepends=True)
    functions = extract_functions(ast_tree)

    if not functions:
        logger.debug("No functions found, chunking entire file", file_path=file_path)
        return chunk_entire_file(content, chunk_size, overlap)

    chunks: list[dict[str, Any]] = []

    for func_node in functions:
        func_chunks = chunk_function(func_node, source_lines, chunk_size, overlap)
        chunks.extend(func_chunks)

    logger.info(
        "Chunked file",
        file_path=file_path,
        function_count=len(functions),
        chunk_count=len(chunks),
    )

    return chunks


def chunk_entire_file(content: str, chunk_size: int, overlap: int) -> list[dict[str, Any]]:
    """Chunk entire file when no functions are found.

    Args:
        content: File content
        chunk_size: Maximum characters per chunk
        overlap: Number of overlapping characters between chunks

    Returns:
        List of chunk dictionaries
    """
    if len(content) <= chunk_size:
        return [
            {
                "content": content,
                "start_line": 1,
                "end_line": len(content.splitlines()),
                "function_name": None,
            }
        ]

    chunks: list[dict[str, Any]] = []
    lines = content.splitlines(keepends=True)
    current_chunk_lines: list[str] = []
    current_chunk_start = 1
    current_chunk_size = 0

    for line_num, line in enumerate(lines, start=1):
        current_chunk_lines.append(line)
        current_chunk_size += len(line)

        if current_chunk_size >= chunk_size:
            chunk_content = "".join(current_chunk_lines)
            chunks.append(
                {
                    "content": chunk_content,
                    "start_line": current_chunk_start,
                    "end_line": line_num,
                    "function_name": None,
                }
            )

            overlap_lines = calculate_overlap_lines(current_chunk_lines, overlap)
            current_chunk_lines = overlap_lines
            current_chunk_start = line_num - len(overlap_lines) + 1
            current_chunk_size = sum(len(line) for line in overlap_lines)

    if current_chunk_lines:
        chunk_content = "".join(current_chunk_lines)
        chunks.append(
            {
                "content": chunk_content,
                "start_line": current_chunk_start,
                "end_line": len(lines),
                "function_name": None,
            }
        )

    return chunks


def calculate_overlap_lines(lines: list[str], overlap: int) -> list[str]:
    """Calculate overlap lines for next chunk.

    Args:
        lines: Current chunk lines
        overlap: Number of overlapping characters

    Returns:
        List of lines for overlap
    """
    if overlap == 0:
        return []

    overlap_lines: list[str] = []
    overlap_size = 0

    for line in reversed(lines):
        overlap_lines.insert(0, line)
        overlap_size += len(line)
        if overlap_size >= overlap:
            break

    return overlap_lines
