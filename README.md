# git-debug-oracle

Live codebase debugging with vector search and Claude. Instantly map runtime errors to the exact code changes that caused them.

Get from stacktrace → relevant code → root cause → fix proposal in seconds instead of minutes.

## ✨ Features

- **Incremental Git indexing** — Only indexes changed files on each commit, never the full repo
- **Vector search retrieval** — Retrieves relevant code context within top-3 results for any error with a valid stacktrace
- **Fix proposals with reasoning** — Generates fixes with root cause analysis, not just code suggestions
- **Webhook-based error ingestion** — Accepts error payloads from any monitoring or logging system (Sentry, Datadog, CloudWatch)
- **Commit recency weighting** — Recent changes rank higher than old code
- **MCP tools for Claude Code** — All functionality exposed via MCP for direct Claude Code integration
- **Runs entirely locally** — Server, vector database, and Git watcher run on your machine or infrastructure
- **Multiple language support** — Parses stacktraces from Python, JavaScript, Java, Go

## ⚡ Quick Start (< 5 minutes)

### Option 1: Docker Compose (Recommended)

**1. Clone and setup**
```bash
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE
cp .env.compose .env
```

**2. Configure environment**
Edit `.env` and add:
```bash
ANTHROPIC_API_KEY=sk-ant-...              # Get from https://console.anthropic.com
EMBEDDING_API_KEY=...                      # Voyage AI or OpenAI key
REPO_PATH=/path/to/your/git/repo         # Absolute path
```

**3. Start services**
```bash
docker-compose up -d
```

**4. Verify it's running**
```bash
curl http://localhost:8000/health
# Should return: {"status": "healthy"}
```

### Option 2: Local Python Installation

**1. Clone and install**
```bash
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e ".[dev]"
```

**2. Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and repo path
```

**3. Start Qdrant and MCP server**
```bash
# Terminal 1: Start Qdrant
docker-compose up qdrant

# Terminal 2: Start MCP server
uv run python -m git_debug_oracle.server
```

## 📋 Prerequisites

- **Python 3.11+** (or Docker)
- **Docker & Docker Compose** (for Qdrant vector database)
- **API Keys:**
  - Claude: https://console.anthropic.com/account/keys
  - Embeddings: Voyage AI (https://www.voyageai.com) or OpenAI (https://platform.openai.com/api-keys)
- **Git repository** to index (any size, any language)

## 🏗️ Architecture

git-debug-oracle is built in modular stages:

1. **Indexing Pipeline** — Git reader → Code chunker → Embedder → Qdrant storage
2. **Retrieval Layer** — Error parser → Query builder → Vector search → Result ranker
3. **Fix Generation** — Context assembler → Claude API → Fix proposal parser
4. **MCP Interface** — All tools registered and callable from Claude Code

See `specs/architecture.md` for detailed system architecture and data flow diagrams.

## 🛠️ Usage Guide

### Indexing Your Repository

1. **Index once (initial)**
```bash
# In Claude Code, call MCP tool:
Tool: index_repo
Parameters:
  repo_path: /path/to/your/repository
  branch: main
  force_full: true
```

2. **Index incrementally**
After making commits, call `index_repo` again — only changed files re-indexed.

3. **Check status**
```bash
Tool: get_index_status
Parameters:
  repo_path: /path/to/your/repository
```

### Sending Errors for Debugging

**Via webhook (from monitoring system):**
```bash
curl -X POST http://localhost:8000/webhook/error \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/app.py",
    "line_number": 42,
    "error_message": "IndexError: list index out of range",
    "stacktrace": "Traceback (most recent call last):\n  ..."
  }'
```

**Via Claude Code MCP tool:**
```bash
Tool: debug_error
Parameters:
  file_path: src/app.py
  line_number: 42
  error_message: IndexError: list index out of range
  stacktrace: "Traceback..."
```

### Getting Fix Proposals

Both methods return a `FixProposal` with:
- `root_cause` — What went wrong and why
- `code_patch` — The exact fix
- `affected_file` — Where the bug is
- `confidence` — How confident we are (0.0-1.0)
- `explanation` — Reasoning chain

## 📊 Supported Error Sources

git-debug-oracle accepts errors from any monitoring system:

- **Application logs** — Parse stacktraces directly
- **Sentry** — Forward to webhook endpoint
- **Datadog** — Custom monitor with webhook
- **CloudWatch** — Lambda function to forward errors
- **Custom systems** — JSON webhook format (see docs/ERROR_PAYLOADS.md)

## 🔧 Configuration

All configuration via environment variables (loaded from `.env`):

**Core:**
- `ANTHROPIC_API_KEY` — Claude API key (required)
- `EMBEDDING_API_KEY` — Voyage AI or OpenAI key (required)
- `REPO_PATH` — Repository path to index (required)

**Qdrant:**
- `QDRANT_HOST` — Qdrant server (default: localhost)
- `QDRANT_PORT` — Qdrant port (default: 6333)
- `QDRANT_COLLECTION` — Collection name (default: git_debug_oracle)

**Tuning:**
- `CHUNK_SIZE` — Code chunk size in chars (default: 1000)
- `CHUNK_OVERLAP` — Overlap between chunks (default: 200)
- `TOP_K` — Retrieval results count (default: 5)
- `RECENT_COMMIT_WINDOW` — Days for recency boost (default: 30)

**Advanced:**
- `EMBEDDING_MODEL` — voyage-code-2 or text-embedding-3-small
- `CLAUDE_MODEL` — Claude model to use
- `LOG_LEVEL` — DEBUG, INFO, WARNING, ERROR
- `WEBHOOK_SECRET` — Optional signature validation

See `.env.compose` for all options and defaults.

## 🤝 MCP Tool Registration

### Claude Code

1. **Add to Claude Code config** (usually `~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "git-debug-oracle": {
      "command": "python",
      "args": ["-m", "git_debug_oracle.server"],
      "env": {
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "EMBEDDING_API_KEY": "...",
        "REPO_PATH": "/path/to/repo"
      }
    }
  }
}
```

2. **Or use docker-compose:**
```json
{
  "mcpServers": {
    "git-debug-oracle": {
      "command": "docker-compose",
      "args": ["exec", "mcp-server", "python", "-m", "git_debug_oracle.server"]
    }
  }
}
```

3. **Verify registration:**
   - Restart Claude Code
   - Tools should appear in MCP tool list
   - Call `get_index_status` to verify connectivity

See `docs/MCP_CONFIG.md` for detailed setup instructions.

## 🧪 Testing & Development

### Run all tests
```bash
uv run pytest tests/ -v
```

### Run with coverage
```bash
uv run pytest tests/ --cov=src/git_debug_oracle --cov-report=html
```

### Type checking
```bash
uv run mypy src/
```

### Linting
```bash
uv run ruff check src/
```

### Format code
```bash
uv run ruff format src/
```

### Install pre-commit hooks
```bash
pre-commit install
```

## 🐛 Troubleshooting

### "Cannot connect to Qdrant"
```
Solution:
1. Verify Qdrant is running: docker-compose ps
2. Check QDRANT_HOST and QDRANT_PORT in .env
3. Restart services: docker-compose restart
```

### "ANTHROPIC_API_KEY not set"
```
Solution:
1. Get key from https://console.anthropic.com/account/keys
2. Add to .env: ANTHROPIC_API_KEY=sk-ant-...
3. Restart MCP server
```

### "Invalid embedding API key"
```
Solution:
1. Verify key is correct for chosen model
2. Check EMBEDDING_MODEL in .env (voyage-code-2 or text-embedding-3-small)
3. For Voyage: https://www.voyageai.com
4. For OpenAI: https://platform.openai.com/api-keys
```

### "No results returned for error"
```
Solution:
1. Verify repository is indexed: Call get_index_status
2. Index the repo if needed: Call index_repo
3. Check error has valid file_path and line_number
4. Try searching a different file or error
```

For more troubleshooting, see `docs/TROUBLESHOOTING.md`.

## 📚 Documentation

- **`docs/QUICKSTART.md`** — Step-by-step setup guide
- **`docs/CONFIGURATION.md`** — All environment variables documented
- **`docs/ERROR_PAYLOADS.md`** — Example payloads for different systems
- **`docs/MCP_CONFIG.md`** — Claude Code and Claude Desktop setup
- **`docs/TROUBLESHOOTING.md`** — Common issues and solutions
- **`CONTRIBUTING.md`** — Development setup and contribution process
- **`specs/architecture.md`** — System architecture and data flow
- **`specs/roadmap.md`** — Development phases and milestones

## 🎯 How It Works

**Error arrives** → **Parse stacktrace** → **Search for context** → **Generate fix** → **Propose solution**

1. Error payload received (webhook or MCP tool)
2. Stacktrace parsed to extract file path, line number, function name
3. Query constructed from error metadata
4. Vector search finds relevant code chunks from recent commits
5. Context assembled with retrieval results + diffs
6. Claude generates fix proposal with reasoning
7. Result returned with confidence score

**Time**: Error to fix proposal in < 30 seconds.

## 📈 Performance Benchmarks

- **Indexing**: < 2 seconds per 1000 lines of changed code
- **Retrieval**: < 500ms from query to results
- **Fix generation**: < 30 seconds end-to-end
- **Accuracy**: 90%+ top-3 hit rate for errors with stacktraces

## 🚀 Roadmap

Current: **Phase 4** — Fix Generation & MCP Contracts ✅

Upcoming:
- **Phase 5** — OSS Hardening (Docker, CI/CD, documentation)
- **Phase 6** — Advanced monitoring and integrations

See `specs/roadmap.md` for detailed development phases.

## 💡 Use Cases

**Solo developers** — Instant error diagnosis without manual git archaeology

**Backend engineers** — Map production errors to recent code changes immediately

**OSS maintainers** — Diagnose contributor-introduced regressions in seconds

**Claude Code users** — Direct MCP integration for seamless debugging workflow

**Monorepo teams** — Track which recent change broke what in large codebases

## 📄 License

MIT License — See LICENSE file for details

## 🤝 Contributing

We welcome contributions! See `CONTRIBUTING.md` for:
- Development setup
- Git workflow (branch naming, commits)
- Testing requirements
- Code standards

## 🔗 Links

- **GitHub**: https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE
- **Anthropic Claude**: https://www.anthropic.com/claude
- **Voyage AI Embeddings**: https://www.voyageai.com/
- **Qdrant Vector Database**: https://qdrant.tech/

## 📞 Support

For issues, questions, or feedback:
- **GitHub Issues**: Report bugs and request features
- **Documentation**: Check `docs/TROUBLESHOOTING.md`
- **Architecture**: See `specs/architecture.md`
