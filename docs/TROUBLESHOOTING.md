# Troubleshooting Guide

Common issues and solutions for git-debug-oracle.

## Installation & Setup

### Python version issue

**Error:** `Python 3.11+ required`

**Solution:**
```bash
# Check Python version
python --version

# If needed, install Python 3.11+
# macOS: brew install python@3.11
# Ubuntu: sudo apt install python3.11
# Windows: https://www.python.org/downloads/
```

### uv not found

**Error:** `uv: command not found`

**Solution:**
```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify
uv --version
```

### Port already in use

**Error:** `Error: listen EADDRINUSE: address already in use :::8000`

**Solution:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port in .env
WEBHOOK_PORT=8001
```

### Insufficient memory

**Error:** `OOMKilled` or `Cannot allocate memory`

**Solution:**
1. Check available memory: `free -h`
2. Reduce `MAX_CONTEXT_CHUNKS` in `.env`
3. Use smaller embedding model (text-embedding-3-small instead of voyage-code-2)

### REPO_PATH not found

**Error:** `Repository path does not exist: /path/to/repo`

**Solution:**
```bash
# Verify path exists
ls -la /path/to/repo

# Use absolute path, not relative
REPO_PATH=/home/user/my-repo  # ✓ Correct
REPO_PATH=~/my-repo            # ✗ Wrong (use absolute)
```

## Configuration Issues

### Missing required env var

**Error:** `Configuration Error: ANTHROPIC_API_KEY not set`

**Solution:**
```bash
# Edit .env file
nano .env

# Add your keys
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDING_API_KEY=...
REPO_PATH=/absolute/path/to/repo
```

### Invalid API key

**Error:** `Invalid API key for Anthropic` or `Invalid API key for embedding service`

**Solution:**
1. Verify key is correct: `echo $ANTHROPIC_API_KEY`
2. Get new key from:
   - Claude: https://console.anthropic.com/account/keys
   - Voyage AI: https://www.voyageai.com
   - OpenAI: https://platform.openai.com/api-keys
3. Update `.env` and restart server

### Invalid configuration value

**Error:** `Invalid value for CHUNK_SIZE: must be between 100 and 10000`

**Solution:**
```bash
# Check current value
grep CHUNK_SIZE .env

# Fix value
CHUNK_SIZE=1000  # ✓ Valid (100-10000)
CHUNK_SIZE=50    # ✗ Too small
```

## Qdrant Connection Issues

### Cannot connect to Qdrant

**Error:** `Failed to connect to Qdrant at localhost:6333`

**Solution:**
```bash
# Check if Qdrant is running
curl http://localhost:6333/health

# If not, start it (choose one):

# Option A: Docker
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:latest

# Option B: Use Qdrant Cloud (update QDRANT_HOST and QDRANT_API_KEY in .env)

# Option C: Local Python
pip install qdrant-client
```

### Qdrant connection timeout

**Error:** `Connection timeout to Qdrant`

**Solution:**
```bash
# Verify Qdrant is listening
netstat -tuln | grep 6333

# Check firewall
sudo ufw allow 6333

# Verify QDRANT_HOST setting
grep QDRANT_HOST .env

# Restart Qdrant
# If using Docker:
docker ps | grep qdrant
docker restart <container_id>
```

### Collection not found

**Error:** `Collection 'git_debug_oracle' not found`

**Solution:**
1. This is normal on first run — collection is created automatically
2. Run `index_repo` tool to create and populate collection
3. Or verify with: `curl http://localhost:6333/collections`

## Indexing Issues

### Indexing takes too long

**Diagnosis:**
```bash
# Check server logs for progress
# Look for lines with "index", "chunk", "embed"

# Check how many files were processed
grep -i "processed" server.log
```

**Solutions:**
1. Larger repos naturally take longer
2. Incremental indexing is faster than full indexing
3. Increase `CHUNK_SIZE` to reduce number of chunks
4. Use faster embedding model (voyage-code-2 is faster than text-embedding-3-small)

### Embedding API errors

**Error:** `Embedding service error: 503 Service Unavailable`

**Solution:**
1. Check API key is valid: https://www.voyageai.com/account/api-keys
2. Check service status:
   - Voyage AI: https://status.voyageai.com/
   - OpenAI: https://status.openai.com/
3. Retry after a few minutes
4. Check rate limits haven't been exceeded

### File type not supported

**Error:** `Skipping binary file: config.bin` (INFO level, not an error)

**Solution:**
This is expected. Only text code files are indexed:
- Supported: `.py`, `.js`, `.ts`, `.java`, `.go`, `.rs`, etc.
- Not supported: `.bin`, `.png`, `.pdf`, `.zip`, etc.

### Repository not a git repo

**Error:** `Not a git repository: /path/to/directory`

**Solution:**
```bash
# Verify it's a git repo
ls -la /path/to/directory/.git

# If no .git, initialize it
cd /path/to/directory
git init
git add .
git commit -m "initial commit"
```

## MCP Server Issues

### Server won't start

**Error:** `Failed to start MCP server` or server exits immediately

**Solution:**
1. Check all required env vars are set:
   ```bash
   grep -E "ANTHROPIC_API_KEY|EMBEDDING_API_KEY|REPO_PATH" .env
   ```
2. Verify Qdrant is running
3. Check logs for specific error:
   ```bash
   uv run python -m git_debug_oracle.server 2>&1 | head -50
   ```

### MCP tools don't appear in Claude Code

**Error:** Tools not listed in MCP tool dropdown

**Solution:**
1. Verify config in `~/.claude/settings.json` is valid JSON
2. Check command is correct:
   ```json
   "command": "python",
   "args": ["-m", "git_debug_oracle.server"]
   ```
3. Verify environment variables are set in config
4. Restart Claude Code completely (not just reload)
5. Check Claude Code logs for MCP errors

### Tool execution times out

**Error:** `Tool call timed out after 30s`

**Solution:**
1. For indexing: Use incremental indexing (don't force full re-index)
2. For retrieval: Reduce `TOP_K` or `MAX_CONTEXT_CHUNKS`
3. For fix generation: Check Claude API status
4. Increase MCP timeout in Claude Code settings

## Retrieval Issues

### No results returned

**Error:** Query returns empty results or very low scores

**Solution:**
1. Verify repository is indexed: Call `get_index_status` tool
2. If not indexed, call `index_repo` with `force_full=true`
3. Check if error matches indexed code:
   - Is the error file in the indexed repo?
   - Is the error in a recent commit?
4. Try broader search terms

### Results are not relevant

**Error:** Top results don't match the error

**Solution:**
1. Increase `TOP_K` to get more candidates
2. Increase `RECENT_COMMIT_WINDOW` if error is in older code
3. Check `EMBEDDING_MODEL` — voyage-code-2 is better than text-embedding-3-small
4. Try re-indexing with `force_full=true`

## Fix Generation Issues

### Fix proposal is low confidence

**Error:** Returned fix has `confidence: 0.2`

**Solution:**
1. Provide more context in the error message
2. Include full stacktrace (not just error message)
3. Increase `MAX_CONTEXT_CHUNKS` to give Claude more code
4. Check if retrieval found relevant code (see Retrieval Issues)

### Claude API rate limited

**Error:** `RateLimitError: Rate limit exceeded`

**Solution:**
1. Wait a few minutes and retry
2. Use fewer concurrent calls
3. Upgrade Claude API plan if needed
4. Check current usage: https://console.anthropic.com/account/usage

### Claude API returns error

**Error:** `APIError: 500 Internal Server Error`

**Solution:**
1. Check Claude API status: https://status.anthropic.com/
2. Retry after a few minutes
3. Check API key is valid and has credits
4. Try with a different model in `CLAUDE_MODEL`

## Performance Issues

### Server is slow to respond

**Solution:**
1. Check CPU/memory usage: `top` or `htop`
2. Check if Qdrant is responsive: `curl http://localhost:6333/health`
3. Check network latency to Qdrant
4. Reduce `CHUNK_SIZE` to process fewer chunks
5. Increase `WEBHOOK_PORT` timeout

### Embedding generation is slow

**Solution:**
1. Voyage AI (voyage-code-2) is faster than OpenAI
2. Use batch processing (automatic)
3. Reduce `CHUNK_SIZE` to embed fewer tokens per chunk
4. Check embedding API rate limits

## Database Issues

### Qdrant data corruption

**Error:** `Collection corrupted` or search returns invalid results

**Solution:**
```bash
# Clear and rebuild index
QDRANT_COLLECTION=git_debug_oracle_new .env
# Call index_repo to rebuild

# Or delete collection via API
curl -X DELETE http://localhost:6333/collections/git_debug_oracle
```

### Running out of disk space

**Error:** `No space left on device`

**Solution:**
```bash
# Check disk usage
df -h

# If using local Qdrant via Docker, you can clean up:
# Find the qdrant container
docker ps | grep qdrant

# Remove old snapshots (if volume mounted)
# Or clear the collection and re-index:
curl -X DELETE http://localhost:6333/collections/git_debug_oracle

# Then re-index
Tool: index_repo
```

## Getting Help

If you can't resolve the issue:

1. **Check the logs:**
   ```bash
   # Server logs show what's happening
   # Look for ERROR or WARNING lines
   ```

2. **Verify configuration:**
   ```bash
   # Print current config
   env | grep -E "ANTHROPIC|EMBEDDING|QDRANT|REPO"
   ```

3. **Test connectivity:**
   ```bash
   # Test Qdrant
   curl http://localhost:6333/health
   
   # Test Claude API
   curl https://api.anthropic.com/v1/messages
   ```

4. **Open an issue:**
   - GitHub: https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE/issues
   - Include: error message, log output, OS version, Python version
   - Include: steps to reproduce the issue

5. **Read related docs:**
   - CONFIGURATION.md — All environment variables
   - docs/MCP_CONFIG.md — MCP setup issues
   - docs/ERROR_PAYLOADS.md — Error format issues
