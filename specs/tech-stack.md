# Tech Stack Specification

## Runtime

**mcp 1.x**
MCP Python SDK for building the server. Chosen because it is the official SDK from Anthropic, has stable tool registration APIs, and integrates directly with Claude Code and Claude Desktop.

**qdrant-client 1.x**
Python client for Qdrant vector database. Chosen over alternatives (Pinecone, Weaviate, Chroma) because Qdrant runs locally via Docker with no external dependencies, supports metadata filtering natively, and has a clean Python API.

**GitPython 3.x**
Python library for Git repository interaction. Chosen because it provides high-level APIs for reading commits, diffs, and file history without shelling out to git commands, and handles edge cases like merge commits and renames.

**fastapi 0.115.x**
Web framework for the webhook endpoint that receives error payloads. Chosen over Flask because it has native async support, automatic OpenAPI schema generation, and built-in request validation via Pydantic.

**anthropic 0.40.x**
Official Anthropic SDK for calling Claude API to generate fix proposals. Chosen because it is the official client, supports prompt caching, and handles retries and rate limiting automatically.

**openai 1.x**
OpenAI Python client for text-embedding-3-small if using OpenAI embeddings. Chosen because it is the official client and supports batch embedding requests efficiently.

**voyageai 0.x**
Voyage AI Python client for voyage-code-2 embeddings if using Voyage. Chosen because voyage-code-2 is optimized for code and outperforms general-purpose embeddings on code retrieval benchmarks.

**pydantic 2.x**
Data validation and settings management. Chosen because it provides runtime type checking, automatic validation error messages, and integrates with FastAPI for request/response schemas.

**pydantic-settings 2.x**
Environment variable loading and validation. Chosen because it extends Pydantic to load config from .env files with type validation and clear error messages for missing required fields.

**structlog 24.x**
Structured logging library. Chosen over standard logging because it outputs JSON logs by default, supports context binding, and makes log aggregation and searching trivial.

**uvicorn 0.32.x**
ASGI server for running the FastAPI webhook endpoint. Chosen because it is the standard ASGI server for FastAPI, supports async, and has minimal overhead.

## Developer Tooling

**pytest 8.x**
Test framework. Chosen because it is the standard Python test framework, has excellent fixture support, and integrates with all major CI systems.

**pytest-asyncio 0.24.x**
Async test support for pytest. Required because the webhook endpoint and some MCP tools are async functions.

**pytest-cov 6.x**
Coverage reporting for pytest. Generates coverage reports to ensure test completeness.

**ruff 0.8.x**
Linter and formatter. Chosen because it is 10-100x faster than flake8/black, combines linting and formatting in one tool, and has sensible defaults with minimal configuration.

**mypy 1.x**
Static type checker. Chosen because it is the standard Python type checker, catches type errors before runtime, and enforces the type annotation requirements in the constitution.

**pre-commit 4.x**
Git hook manager. Runs ruff and mypy before every commit to catch issues early. Chosen because it is the standard tool for managing Git hooks in Python projects.

**pytest-mock 3.x**
Mocking library for pytest. Simplifies mocking external dependencies like Qdrant, Git, and Claude API in unit tests.

## Packaging and Distribution

**pyproject.toml with pip install support**
The project uses pyproject.toml with setuptools backend. Developers can install it via `pip install -e .` for local development or `pip install git+https://github.com/user/git-debug-oracle.git` for direct installation from GitHub.

**Docker image via docker-compose**
A docker-compose.yml file bundles the MCP server and Qdrant together. Running `docker-compose up` starts both services with correct networking and volume mounts. The MCP server container runs the server process, and the Qdrant container runs the vector database.

**MCP config registration**
Users register the server in their MCP client config. For Claude Desktop, they add an entry to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent on other platforms. For Claude Code, they add it to the MCP servers section of their config. The entry specifies the command to run the server (either `python -m git_debug_oracle.server` or `docker-compose up` depending on installation method) and any required environment variables.

**Environment variable passing**
When running via Docker, environment variables are passed through docker-compose.yml or a .env file. When running directly via Python, they are loaded from a .env file in the repo root or set in the shell environment.

## Logging

**structlog 24.x**
All logging uses structlog. Logs are structured JSON in production and human-readable key-value format in development.

**Log levels used**
- DEBUG: Detailed information for diagnosing issues (chunk content, embedding vectors, query construction details)
- INFO: Normal operation events (index started, index completed, retrieval query received, fix generated)
- WARNING: Unexpected but handled situations (missing file in Git, unsupported file type, Qdrant connection retry)
- ERROR: Operation failures that prevent completion (Qdrant connection failed, embedding API error, Claude API error)

**Events that must always be logged at INFO level**
- Index operation started: log repo path, branch, commit range
- Index operation completed: log commit hash, files processed, chunks upserted, duration
- Retrieval query received: log error type, file path, line number, query text
- Retrieval results returned: log number of results, top result score, duration
- Fix generation started: log error summary, number of context chunks
- Fix generation completed: log fix confidence, duration
- Webhook request received: log source IP, payload size
- MCP tool called: log tool name, parameters

**Log output format**
- Development: human-readable key-value format with colors via structlog.dev.ConsoleRenderer
- Production: JSON lines via structlog.processors.JSONRenderer for ingestion by log aggregation systems

**Log configuration**
Logging is configured at server startup in the main entry point. Log level is controlled by LOG_LEVEL environment variable (default: INFO). All loggers use the same structlog configuration for consistency.

## Environment Variables

**QDRANT_HOST**
- Type: string
- Required: Yes
- Default: None
- Description: Hostname or IP address of Qdrant server

**QDRANT_PORT**
- Type: integer
- Required: No
- Default: 6333
- Description: Port number for Qdrant gRPC API

**QDRANT_COLLECTION**
- Type: string
- Required: No
- Default: git_debug_oracle
- Description: Name of Qdrant collection to store code chunks

**QDRANT_API_KEY**
- Type: string
- Required: No
- Default: None
- Description: API key for Qdrant Cloud (not needed for local Docker instance)

**EMBEDDING_MODEL**
- Type: string (enum: voyage-code-2, text-embedding-3-small)
- Required: No
- Default: voyage-code-2
- Description: Which embedding model to use for code chunks

**EMBEDDING_API_KEY**
- Type: string
- Required: Yes
- Default: None
- Description: API key for embedding provider (Voyage AI or OpenAI)

**ANTHROPIC_API_KEY**
- Type: string
- Required: Yes
- Default: None
- Description: API key for Claude API to generate fix proposals

**REPO_PATH**
- Type: string (filesystem path)
- Required: Yes
- Default: None
- Description: Absolute path to Git repository to index

**WATCH_BRANCH**
- Type: string
- Required: No
- Default: main
- Description: Git branch to watch for new commits during incremental indexing

**WEBHOOK_SECRET**
- Type: string
- Required: No
- Default: None
- Description: Shared secret for validating webhook requests (if None, no validation)

**WEBHOOK_PORT**
- Type: integer
- Required: No
- Default: 8000
- Description: Port number for FastAPI webhook server

**CHUNK_SIZE**
- Type: integer
- Required: No
- Default: 1000
- Description: Maximum number of characters per code chunk

**CHUNK_OVERLAP**
- Type: integer
- Required: No
- Default: 200
- Description: Number of overlapping characters between adjacent chunks

**TOP_K**
- Type: integer
- Required: No
- Default: 5
- Description: Number of top results to retrieve from Qdrant for each query

**RECENT_COMMIT_WINDOW**
- Type: integer
- Required: No
- Default: 30
- Description: Number of days to consider a commit "recent" for recency weighting

**LOG_LEVEL**
- Type: string (enum: DEBUG, INFO, WARNING, ERROR)
- Required: No
- Default: INFO
- Description: Minimum log level to output

**CLAUDE_MODEL**
- Type: string
- Required: No
- Default: claude-sonnet-4-20250514
- Description: Claude model to use for fix generation

**MAX_CONTEXT_CHUNKS**
- Type: integer
- Required: No
- Default: 10
- Description: Maximum number of code chunks to include in fix generation context
