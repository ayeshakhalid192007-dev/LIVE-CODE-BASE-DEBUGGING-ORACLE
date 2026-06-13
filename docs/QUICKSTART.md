# Quick Start Guide

Get git-debug-oracle running and indexed in under 5 minutes.

## Prerequisites Checklist

Before starting, ensure you have:

- [ ] Git installed (`git --version`)
- [ ] Docker and Docker Compose (`docker --version`, `docker-compose --version`)
- [ ] Claude API key (https://console.anthropic.com/account/keys)
- [ ] Embedding API key:
  - Voyage AI: https://www.voyageai.com
  - OpenAI: https://platform.openai.com/api-keys
- [ ] A Git repository to index (local or remote)

## Step 1: Clone the Repository (1 min)

```bash
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE
```

## Step 2: Configure Environment (1 min)

Copy the example environment file:

```bash
cp .env.compose .env
```

Edit `.env` and fill in your API keys:

```bash
# Edit .env with your preferred editor
nano .env
```

Required fields to update:

```bash
ANTHROPIC_API_KEY=sk-ant-YOUR_KEY_HERE
EMBEDDING_API_KEY=YOUR_EMBEDDING_KEY_HERE
REPO_PATH=/path/to/your/git/repository
```

Optional but recommended:

```bash
EMBEDDING_MODEL=voyage-code-2     # or text-embedding-3-small
WATCH_BRANCH=main
LOG_LEVEL=INFO
```

## Step 3: Start Services (1 min)

```bash
docker-compose up -d
```

Verify services are running:

```bash
docker-compose ps
```

You should see:
- `git-debug-oracle-mcp` — Running (status: Up)
- `git-debug-oracle-qdrant` — Running (status: Up)

Verify health:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status": "healthy"}
```

## Step 4: Index Your Repository (1-2 min)

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

Watch the logs:

```bash
docker-compose logs -f mcp-server | grep -i "index\|chunk\|embed"
```

## Step 5: Send an Error (Optional)

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

### Services won't start

Check logs:

```bash
docker-compose logs mcp-server
docker-compose logs qdrant
```

Common issues:
- Missing environment variables: Check `.env` has all required keys
- Port conflicts: Ensure 8000 and 6333 are available
- Docker not running: Start Docker daemon

### Indexing fails

```bash
docker-compose logs -f mcp-server
```

Common issues:
- Invalid `REPO_PATH`: Ensure path exists and is a git repository
- Embedding API error: Verify `EMBEDDING_API_KEY` is correct
- Qdrant connection: Verify qdrant service is healthy

### Health check fails

```bash
docker-compose ps
```

If services show `Exited`:

```bash
docker-compose down
docker-compose up -d
```

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

## Docker Compose Tips

View logs in real-time:

```bash
docker-compose logs -f
```

Restart services:

```bash
docker-compose restart
```

Stop services:

```bash
docker-compose down
```

Stop and remove volumes (reset everything):

```bash
docker-compose down -v
```
