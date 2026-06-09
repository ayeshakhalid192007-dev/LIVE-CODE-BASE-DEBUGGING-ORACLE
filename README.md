# git-debug-oracle

Live codebase debugging with vector search and Claude. Instantly map runtime errors to the exact code changes that caused them.

## Features

- **Incremental Git indexing** — Only indexes changed files on each commit, never the full repo
- **Vector search retrieval** — Retrieves relevant code context within top-3 results for any error with a valid stacktrace
- **Fix proposals with reasoning** — Generates fixes with root cause analysis, not just code suggestions
- **Webhook-based error ingestion** — Accepts error payloads from any monitoring or logging system
- **Commit recency weighting** — Recent changes rank higher than old code
- **MCP tools for Claude Code** — All functionality exposed via MCP for direct Claude Code integration
- **Runs entirely locally** — Server, vector database, and Git watcher run on your machine

## Prerequisites

- Python 3.11 or higher
- Docker and Docker Compose
- [uv](https://github.com/astral-sh/uv) package manager
- Git repository to index

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE
```

### 2. Install uv

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 3. Create environment configuration

```bash
cp .env.example .env
```

Edit `.env` and set required values:
- `QDRANT_HOST` — Qdrant server hostname (default: localhost)
- `EMBEDDING_API_KEY` — API key for Voyage AI or OpenAI
- `ANTHROPIC_API_KEY` — API key for Claude
- `REPO_PATH` — Absolute path to Git repository to index

### 4. Install dependencies

```bash
uv pip install -e ".[dev]"
```

### 5. Start Qdrant

```bash
docker-compose up -d
```

Verify Qdrant is running:
```bash
docker-compose ps
```

## Quickstart — Phase 2: Indexing Pipeline

### Index a Repository

Once Qdrant is running and dependencies are installed:

```bash
# Set environment variables
export REPO_PATH=/path/to/your/git/repository
export WATCH_BRANCH=main
export EMBEDDING_API_KEY=your_api_key_here
export ANTHROPIC_API_KEY=your_anthropic_key_here

# Start the MCP server
uv run python -m git_debug_oracle.server
```

In Claude Code, call the `index_repo` MCP tool:

```
Tool: index_repo
Parameters:
  repo_path: /path/to/your/repository
  branch: main
  force_full: true
```

The tool will:
1. Extract all Python files from the repository
2. Chunk code into logical units (functions, classes)
3. Generate embeddings for each chunk
4. Store chunks in Qdrant with metadata

### Incremental Indexing

After indexing once, make a commit to your repository:

```bash
cd /path/to/your/repository
echo "# New change" >> file.py
git add file.py
git commit -m "Update file"
```

Call `index_repo` again — only changed files will be re-indexed.

### Check Indexing Status

Call the `get_index_status` MCP tool:

```
Tool: get_index_status
Parameters:
  repo_path: /path/to/your/repository
  branch: main
```

Returns:
- `last_indexed_commit` — Most recent commit indexed
- `total_chunks` — Number of code chunks in Qdrant
- `total_files` — Number of files indexed
- `is_indexing` — Whether indexing is currently running

## MCP Registration

*MCP registration instructions will be added after Phase 3 (Retrieval and Error Ingestion) is complete.*

## Configuration

All configuration is managed via environment variables. See `.env.example` for complete documentation of available options.

Key configuration variables:
- `EMBEDDING_MODEL` — Which embedding model to use (default: voyage-code-2)
- `CHUNK_SIZE` — Maximum characters per code chunk (default: 1000)
- `TOP_K` — Number of retrieval results (default: 5)
- `LOG_LEVEL` — Logging verbosity (default: INFO)

## Development

### Install pre-commit hooks

```bash
pre-commit install
```

### Run tests

```bash
uv run pytest
```

### Run type checking

```bash
uv run mypy src/
```

### Run linting

```bash
uv run ruff check src/
```

### Format code

```bash
uv run ruff format src/
```

## Architecture

See `specs/architecture.md` for complete architecture documentation.

## Roadmap

See `specs/roadmap.md` for development phases and milestones.

## License

MIT

## Contributing

See `CONTRIBUTING.md` for contribution guidelines.
