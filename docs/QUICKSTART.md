# Quick Start Guide

Get git-debug-oracle running and indexed in under 5 minutes.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Git installed (`git --version`)
- [ ] Python 3.11+ (`python --version`)
- [ ] uv package manager (`uv --version` or install from https://docs.astral.sh/uv/)
- [ ] Qdrant running (see Step 1 below)
- [ ] Claude API key (https://console.anthropic.com/account/keys)
- [ ] Embedding API key:
  - Voyage AI: https://www.voyageai.com
  - OpenAI: https://platform.openai.com/api-keys
- [ ] A Git repository to index (local or remote)

## Step 1: Start Qdrant (1 min)

Choose one option and start Qdrant in a terminal:

**Option A: Local Docker (easiest)**
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest
```

**Option B: Qdrant Cloud**
Sign up at https://qdrant.tech/cloud/ and get your API key (you'll set it in .env)

**Option C: Local Python**
```bash
pip install qdrant-client
# Configure for local mode in .env
```

Verify Qdrant is running:
```bash
curl http://localhost:6333/health
```

## Step 2: Clone and Install (1 min)

In a new terminal:

```bash
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE
uv pip install -e ".[dev]"
```

## Step 3: Configure Environment (1 min)

Copy the example environment file:

```bash
cp .env.example .env
```

Edit `.env` and fill in your API keys:

```bash
nano .env
```

Required fields to update:

```bash
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
EMBEDDING_API_KEY=YOUR_EMBEDDING_KEY_HERE
REPO_PATH=/path/to/your/git/repository
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

If using Qdrant Cloud, also set:
```bash
QDRANT_API_KEY=your-cloud-api-key
```

## Step 4: Start MCP Server (1 min)

```bash
uv run python -m git_debug_oracle.server
```

Verify it's running (in another terminal):

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "healthy"}
```

## Step 5: Index Your Repository (1-2 min)

In Claude Code, call the MCP tool:

```
Tool: index_repo
Parameters:
  repo_path: /path/to/your/repository
  branch: main
  force_full: true
```

The tool will:
1. Extract Python files from the repository
2. Chunk code into functions and classes
3. Generate embeddings for each chunk
4. Store in Qdrant with commit metadata

Watch the logs (from the terminal running the server):

```bash
# Logs will show in the terminal where you ran: uv run python -m git_debug_oracle.server
# Look for lines with "index", "chunk", "embed"
```

## Step 6: Send an Error (Optional)

Test the system with a sample error:

```bash
curl -X POST http://localhost:8000/webhook/error \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/app.py",
    "line_number": 42,
    "error_message": "IndexError: list index out of range",
    "stacktrace": "Traceback (most recent call last):\n  File \"src/app.py\", line 42, in process\n    return items[index]\nIndexError: list index out of range"
  }'
```

Expected response includes `retrieval_results` and `fix_proposal`.

## Troubleshooting

### Qdrant won't connect

Check Qdrant is running:

```bash
curl http://localhost:6333/health
```

If using Docker:
```bash
docker ps | grep qdrant
```

If not running, restart it (see Step 1).

### Server won't start

Check error message in terminal. Common issues:
- Missing environment variables: Verify all required vars in `.env`
- Port 8000 already in use: Change `WEBHOOK_PORT` in `.env`
- Qdrant not reachable: Check `QDRANT_HOST` and `QDRANT_PORT`

### Indexing fails

Check the server logs for errors. Common issues:
- Invalid `REPO_PATH`: Ensure path exists and is a git repository
- Embedding API error: Verify `EMBEDDING_API_KEY` is correct and valid
- Qdrant connection: Verify Qdrant is running and accessible

## Next Steps

1. **Index more repositories** — Call `index_repo` with different `repo_path` values
2. **Send real errors** — Integrate webhook with your monitoring system
3. **Generate fixes** — Call `debug_error` tool with real error payloads
4. **Read documentation** — See `docs/CONFIGURATION.md` for advanced settings

## Getting Help

- **Setup issues** — See main README "Troubleshooting" section
- **Configuration** — Read `docs/CONFIGURATION.md`
- **Error formats** — Check `docs/ERROR_PAYLOADS.md` for examples
- **MCP setup** — See `docs/MCP_CONFIG.md`

## Performance Tips

- **Faster indexing** — Use `voyage-code-2` embedding model (optimized for code)
- **Better results** — Increase `RECENT_COMMIT_WINDOW` if errors are in old code
- **More context** — Increase `MAX_CONTEXT_CHUNKS` for better fix quality
- **Tuning retrieval** — Adjust `TOP_K` and `CHUNK_SIZE` based on your codebase size
