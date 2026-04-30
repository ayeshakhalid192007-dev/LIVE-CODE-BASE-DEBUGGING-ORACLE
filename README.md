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

## Quickstart

*Quickstart guide will be added after Phase 2 (Indexing Pipeline) is complete.*

## MCP Registration

*MCP registration instructions will be added after Phase 1 Task Group 4 (MCP Server & Tooling) is complete.*

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
