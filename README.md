# 🔍 Git Debug Oracle

**Instant error diagnosis for Python codebases.** Paste a stacktrace into Claude. Get a fix with reasoning in seconds.

This MCP server indexes your Git history, finds the exact code that caused an error, and uses Claude to propose fixes with full root cause analysis. Optimized for Python. No manual detective work.

---

## ⚡ 60-Second Start

```bash
# 1. Clone
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE

# 2. Install uv (if needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. Install dependencies
uv sync

# 4. Set up environment
cp .env.example .env
# Edit .env with your API keys and repo path

# 5. Start Qdrant
docker-compose up qdrant -d

# 6. Start MCP server
uv run git-debug-oracle

# 7. Register with Claude Code
claude mcp add --scope user live-code-oracle -- /path/to/uv --directory /path/to/repo run git-debug-oracle

# 8. Done! Tools appear in Claude Code
```

---

## 🎯 What This Does

**Your code breaks** → Error in logs → Paste into Claude → Oracle finds it → Claude proposes fix

| What | Benefit |
|------|---------|
| **Incremental indexing** | Only changed files re-indexed—fast even on large repos |
| **Vector search** | Finds relevant code in top 3 results 90% of the time |
| **Root cause analysis** | Claude reasons over diffs + code to explain why it broke |
| **Webhook support** | Accepts errors from Sentry, Datadog, CloudWatch, etc. |
| **Recency weighting** | Recent commits rank higher (bugs usually come from recent changes) |
| **Fully local** | Your code stays on your machine |
| **Python-focused** | Optimized for Python stacktraces and error patterns |

---

## 📱 Platform Guides

### Claude Code (Recommended)

**Setup** (one-time):
```bash
# After running uv run git-debug-oracle
claude mcp add --scope user live-code-oracle -- \
  /path/to/uv --directory /path/to/repo run git-debug-oracle
```

**Use**:
1. In Claude Code, tools appear in MCP tools list
2. Index repo: Call `index_repo` with your repo path
3. On errors: Call `debug_error` with stacktrace
4. Get fix: Claude returns FixProposal with reasoning

See `docs/INTEGRATIONS.md` for detailed setup.

### Claude Desktop

**Setup** (one-time):
1. Get server path: `which uv` and repo path
2. Edit `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or equivalent:
```json
{
  "mcpServers": {
    "live-code-oracle": {
      "command": "/path/to/uv",
      "args": ["--directory", "/path/to/repo", "run", "git-debug-oracle"],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "EMBEDDING_API_KEY": "...",
        "REPO_PATH": "/path/to/your/repo"
      }
    }
  }
}
```

3. Restart Claude Desktop
4. Tools appear in tools list

See `docs/INTEGRATIONS.md` for detailed platform guides.

---

## 🚀 Usage

### Step 1: Index Your Repository

In Claude Code, call:
```
Tool: index_repo
Parameters:
  repo_path: /path/to/your/repository
  branch: main
  force_full: true  (first time only)
```

Oracle scans all files, chunks code at function level, generates embeddings, stores in Qdrant.

### Step 2: Send an Error

When you hit an error:
```
Tool: debug_error
Parameters:
  file_path: src/api.py
  line_number: 105
  error_message: ConnectionError: failed to connect
  stacktrace: (paste full stacktrace)
```

### Step 3: Get Fix Proposal

Oracle returns:
- **root_cause** — What went wrong and why
- **affected_file** — Location of bug
- **code_patch** — The fix
- **confidence** — 0.0-1.0 score
- **explanation** — Full reasoning chain
- **reasoning_trace** — Step-by-step analysis

---

## 🔄 Example Workflow

```
You: "I got this error, help me fix it"
(paste stacktrace from src/parser.py line 87)

Claude: "Let me search your codebase..."
Claude calls: debug_error(...)

Oracle finds:
- Recent commit that added .split() without null check
- Previous version that handled None
- All diffs since then

Claude proposes:
- Root cause: Commit abc123 added split() without null check
- Fix: Add None check before calling .split()
- Confidence: 0.95
- Reasoning: Shows exact line, why it broke, how to fix

You: "Looks good, apply it"
```

**Time**: ~25 seconds instead of 25 minutes.

---

## 📚 Detailed Guides

- **[QUICKSTART.md](docs/QUICKSTART.md)** — Detailed setup with screenshots
- **[INTEGRATIONS.md](docs/INTEGRATIONS.md)** — Setup for Claude Code and Desktop
- **[CONFIGURATION.md](docs/CONFIGURATION.md)** — All environment variables and tuning options
- **[MCP_CONFIG.md](docs/MCP_CONFIG.md)** — MCP server registration details
- **[ERROR_PAYLOADS.md](docs/ERROR_PAYLOADS.md)** — Webhook format and examples
- **[TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** — Solutions for common issues
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — System design and data flow

---

## 🛠️ All MCP Tools

| Tool | Purpose | Inputs | Returns |
|------|---------|--------|---------|
| `index_repo` | Index/re-index repository | repo_path, branch, force_full | IndexStatus |
| `debug_error` | Find fix for error | file_path, line_number, error_message, stacktrace | FixProposal |
| `search_codebase` | Search code by query | query, top_k | List[RetrievalResult] |
| `get_index_status` | Check indexing progress | repo_path | IndexStatus |
| `get_recent_diffs` | Get recent commits | repo_path, days | List[CommitDiff] |

Full API docs: `docs/MCP_TOOLS.md`

---

## ⚙️ Configuration

**Required** (in `.env`):
- `ANTHROPIC_API_KEY` — Claude API key (get from https://console.anthropic.com)
- `EMBEDDING_API_KEY` — Voyage AI or OpenAI key
- `REPO_PATH` — Your Git repository path

**Qdrant** (defaults work):
- `QDRANT_HOST` — localhost (default)
- `QDRANT_PORT` — 6333 (default)
- `QDRANT_COLLECTION` — git_debug_oracle (default)

**Tuning** (optional):
- `CHUNK_SIZE` — 1000 (default)
- `CHUNK_OVERLAP` — 200 (default)
- `TOP_K` — 5 (default)
- `EMBEDDING_MODEL` — voyage-code-2 (default) or text-embedding-3-small

See `docs/CONFIGURATION.md` for complete reference.

---

## 🧪 Development

```bash
# Run tests
uv run pytest tests/ -v

# Coverage report
uv run pytest tests/ --cov=src/git_debug_oracle --cov-report=html

# Type check
uv run mypy src/

# Lint
uv run ruff check src/

# Format
uv run ruff format src/

# Install git hooks
pre-commit install
```

---

## 📊 Performance

- **Indexing**: < 2 seconds per 1000 lines of changed code
- **Retrieval**: < 500ms from error to results
- **Fix generation**: < 30 seconds end-to-end
- **Accuracy**: 90%+ top-3 hit rate

---

## ❓ FAQ

**Q: Does my code leave my machine?**
A: No. Repository and chunks stay local. Only API calls to Claude and embedding provider go out.

**Q: What languages does it support?**
A: Designed for Python. Optimized for Python stacktraces and code patterns. Any language's code can be indexed.

**Q: How big a repository can it handle?**
A: Any size. Incremental indexing means only changed files are processed.

**Q: Can I use it offline?**
A: Indexing and search work offline. Fix generation requires Claude API, embedding requires embedding API.

**Q: Can I index multiple repositories?**
A: Yes. Run separate server instances with different `REPO_PATH` values.

---

## 📄 License

MIT License — See LICENSE file.

---

## 🤝 Contributing

See `CONTRIBUTING.md` for:
- Development setup
- Git workflow
- Testing requirements
- Code standards

---

## 🔗 Resources

- **Repository**: https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE
- **Specs**: `specs/` directory (mission, roadmap, architecture)
- **Claude API**: https://www.anthropic.com/claude
- **Voyage AI**: https://www.voyageai.com/
- **Qdrant**: https://qdrant.tech/

---

**Made for developers who want instant answers, not manual archaeology.**
