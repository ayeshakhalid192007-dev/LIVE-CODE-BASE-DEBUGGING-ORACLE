"""MCP server entry point for git-debug-oracle."""

import os
from typing import Any

from mcp.server import Server
import mcp.server.stdio

from git_debug_oracle.config import Config
from git_debug_oracle.utils.logging import configure_logging, get_logger
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper
from git_debug_oracle.embedder.voyage_client import VoyageEmbedder
from git_debug_oracle.mcp_tools.index_repo import index_repo, index_incremental
from git_debug_oracle.mcp_tools.get_index_status import get_index_status, get_all_indexed_branches

# Global state for server components
_config: Config | None = None
_qdrant_client: QdrantClientWrapper | None = None
_logger = None

# Create MCP server instance
server = Server("git-debug-oracle")


def create_server() -> Server:
    """Create and initialize the MCP server with all components.

    Returns:
        Configured MCP Server instance
    """
    global _config, _qdrant_client, _logger

    # Load configuration
    _config = Config()

    # Configure logging
    # Use development mode by default, production if ENVIRONMENT=production
    is_development = os.getenv("ENVIRONMENT", "development") != "production"
    # LogLevel enum inherits from str, so can be used directly
    configure_logging(log_level=str(_config.log_level), development=is_development)

    _logger = get_logger(__name__)
    _logger.info(
        "Starting git-debug-oracle MCP server",
        version="0.1.0",
        environment="development" if is_development else "production",
    )

    # Initialize Qdrant client
    _qdrant_client = QdrantClientWrapper(_config)

    # Test Qdrant connection
    if _qdrant_client.test_connection():
        _logger.info("Qdrant connection successful")
    else:
        _logger.warning(
            "Qdrant connection failed - server will start but functionality may be limited"
        )

    _logger.info("MCP server initialized successfully")
    return server


def health_check() -> dict[str, Any]:
    """Check health status of the server and its dependencies.

    Returns:
        Dictionary containing health status information
    """
    if _qdrant_client is None:
        return {
            "status": "unhealthy",
            "qdrant_connected": False,
            "message": "Server not initialized",
        }

    # Test Qdrant connection
    qdrant_connected = _qdrant_client.test_connection()

    if qdrant_connected:
        status = "healthy"
    else:
        status = "degraded"

    return {
        "status": status,
        "qdrant_connected": qdrant_connected,
        "version": "0.1.0",
    }


@server.list_tools()
async def list_tools() -> list[dict[str, Any]]:
    """List available MCP tools.

    Returns:
        List of tool definitions
    """
    return [
        {
            "name": "health_check",
            "description": "Check health status of the server and its dependencies",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
        {
            "name": "index_repo",
            "description": "Index a Git repository or specific commit with full or incremental indexing",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Absolute path to repository"},
                    "commit_hash": {"type": "string", "description": "Commit hash to index (default: HEAD)"},
                    "branch": {"type": "string", "description": "Branch name for tracking (default: main)"},
                    "force_full": {"type": "boolean", "description": "Force full re-index (default: false)"},
                    "commit_range": {"type": "array", "description": "Tuple of [start_commit, end_commit] to index range"},
                },
                "required": [],
            },
        },
        {
            "name": "index_incremental",
            "description": "Incrementally index repository (only new commits since last index)",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Absolute path to repository"},
                    "branch": {"type": "string", "description": "Branch name (default: main)"},
                },
                "required": [],
            },
        },
        {
            "name": "get_index_status",
            "description": "Get the current index status for a repository and branch",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "repo_path": {"type": "string", "description": "Absolute path to repository"},
                    "branch": {"type": "string", "description": "Branch name"},
                },
                "required": [],
            },
        },
        {
            "name": "get_all_indexed_branches",
            "description": "Get list of all branches that have been indexed",
            "inputSchema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[dict[str, Any]]:
    """Handle tool execution requests.

    Args:
        name: Name of the tool to execute
        arguments: Tool arguments

    Returns:
        List of tool results
    """
    if name == "health_check":
        result = health_check()
        return [{"type": "text", "text": str(result)}]
    elif name == "index_repo":
        result = index_repo(
            repo_path=arguments.get("repo_path"),
            commit_hash=arguments.get("commit_hash"),
            branch=arguments.get("branch"),
            force_full=arguments.get("force_full", False),
            commit_range=tuple(arguments.get("commit_range")) if arguments.get("commit_range") else None,
            config=_config,
            qdrant_wrapper=_qdrant_client,
            embedder=VoyageEmbedder(_config.embedding_api_key),
        )
        return [{"type": "text", "text": str(result)}]
    elif name == "index_incremental":
        result = index_incremental(
            repo_path=arguments.get("repo_path"),
            branch=arguments.get("branch"),
            config=_config,
            qdrant_wrapper=_qdrant_client,
            embedder=VoyageEmbedder(_config.embedding_api_key),
        )
        return [{"type": "text", "text": str(result)}]
    elif name == "get_index_status":
        result = get_index_status(
            repo_path=arguments.get("repo_path"),
            branch=arguments.get("branch"),
            config=_config,
            qdrant_wrapper=_qdrant_client,
        )
        return [{"type": "text", "text": str(result)}]
    elif name == "get_all_indexed_branches":
        result = get_all_indexed_branches(
            config=_config,
            qdrant_wrapper=_qdrant_client,
        )
        return [{"type": "text", "text": str(result)}]
    else:
        raise ValueError(f"Unknown tool: {name}")


def main() -> None:
    """Main entry point for the MCP server."""
    # Initialize server components
    create_server()

    # Run the MCP server using stdio transport
    mcp.server.stdio.run(server)


if __name__ == "__main__":
    main()
