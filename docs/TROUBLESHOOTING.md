# Troubleshooting Guide

Common issues and solutions for git-debug-oracle.

## Installation & Setup

### Docker not found

**Error:** `docker: command not found`

**Solution:**
1. Install Docker: https://docs.docker.com/get-docker/
2. Verify: `docker --version`
3. On Linux, add user to docker group: `sudo usermod -aG docker $USER`
4. Restart shell: `exec $SHELL`

### Port already in use

**Error:** `Error: listen EADDRINUSE: address already in use :::8000`

**Solution:**
```bash
# Find what's using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use different port
WEBHOOK_PORT=8001 docker-compose up
```

### Insufficient memory

**Error:** `OOMKilled` or `Cannot allocate memory`

**Solution:**
1. Check available memory: `free -h`
2. Increase Docker memory limit
3. Reduce `MAX_CONTEXT_CHUNKS` in `.env`
4. Use smaller embedding model

### REPO_PATH not found

**Error:** `Repository path does not exist: /path/to/repo`

**Solution:**
```bash
# Verify path exists
ls -la /path/to/repo

# Use absolute path, not relative
REPO_PATH=/home/user/my-repo  # ✓ Correct
REPO_PATH=~/my-repo            # ✗ Wrong
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
```

### Invalid API key

**Error:** `Invalid API key for Anthropic` or `Invalid API key for embedding service`

**Solution:**
1. Verify key is correct: `echo $ANTHROPIC_API_KEY`
2. Get new key from:
   - Claude: https://console.anthropic.com/account/keys
   - Voyage AI: https://www.voyageai.com
   - OpenAI: https://platform.openai.com/api-keys
3. Update `.env` and restart services

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
# Check if service is running
docker-compose ps

# If not running, start it
docker-compose up -d qdrant

# Verify connection
curl http://localhost:6333/health

# Check logs
docker-compose logs qdrant
```

### Qdrant health check failing

**Error:** `Health check FAILED` in docker-compose ps

**Solution:**
```bash
# Restart service
docker-compose restart qdrant

# Wait 30 seconds and check again
sleep 30
docker-compose ps

# If still failing, check logs
docker-compose logs -f qdrant --tail 50
```

### Collection not found

**Error:** `Collection 'git_debug_oracle' not found`

**Solution:**
1. This is normal on first run — collection is created automatically
2. Run `index_repo` to create and populate collection
3. Or verify with: `curl http://localhost:6333/collections`

## Indexing Issues

### Indexing takes too long

**Diagnosis:**
```bash
# Monitor progress
docker-compose logs -f mcp-server | grep -i "chunk\|embed"
```

**Solutions:**
1. Reduce `CHUNK_SIZE` (faster processing, more chunks)
2. Reduce `MAX_CONTEXT_CHUNKS` (less context to generate)
3. Use faster embedding model (`text-embedding-3-small`)
4. Increase `CHUNK_OVERLAP` to 0 (no overlap)

### Indexing fails with OutOfMemory

**Error:** `MemoryError` or `OOMKilled`

**Solutions:**
1. Reduce chunk size: `CHUNK_SIZE=500`
2. Reduce batch size in embedder
3. Increase Docker memory limit
4. Index smaller repositories first

### No chunks indexed

**Error:** `total_chunks: 0` from `get_index_status`

**Solution:**
1. Verify repository has Python files: `find /repo -name "*.py" | head`
2. Check file filter settings
3. View logs: `docker-compose logs mcp-server | grep -i "chunk\|skip"`

## Retrieval Issues

### No results returned

**Diagnosis:**
```bash
# Verify index status
Tool: get_index_status
# Should show total_chunks > 0
```

**Solutions:**
1. Index the repository first
2. Increase `TOP_K` parameter
3. Adjust query (more specific error messages work better)
4. Check if file exists in repository

### Poor result quality

**Solutions:**
1. Increase `TOP_K` to get more candidates
2. Adjust `RECENT_COMMIT_WINDOW` if errors are old
3. Use better embedding model (`voyage-code-2`)
4. Increase `CHUNK_SIZE` for more context

## Fix Generation Issues

### Claude API errors

**Error:** `Authentication failed for Claude API`

**Solution:**
1. Verify API key: `echo $ANTHROPIC_API_KEY`
2. Check key is valid at: https://console.anthropic.com/account/keys
3. Verify key format starts with `sk-ant-`

### Low confidence score

**Issue:** Fix proposal has confidence < 0.5

**Explanation:** This can happen when:
- Retrieval results are poor matches
- Error information is incomplete
- Code context is limited

**Solutions:**
1. Provide more error context (stacktrace)
2. Index more of the repository
3. Increase `MAX_CONTEXT_CHUNKS` for more context

### Fix not compiling

**Issue:** Suggested code patch has syntax errors

**Solutions:**
1. This shouldn't happen — report as bug
2. Use suggestion as starting point
3. Increase `MAX_CONTEXT_CHUNKS` for better understanding
4. Try with different Claude model

## Webhook Issues

### Webhook not receiving requests

**Diagnosis:**
```bash
# Check if MCP server is running
docker-compose ps mcp-server

# Check if port is exposed
netstat -tulpn | grep 8000
```

**Solutions:**
1. Verify MCP server is running: `docker-compose up -d mcp-server`
2. Verify firewall allows port 8000
3. Verify webhook URL is correct in monitoring system
4. Check logs: `docker-compose logs mcp-server`

### Invalid signature error

**Error:** `Invalid signature` when calling webhook

**Solutions:**
1. If `WEBHOOK_SECRET` not set, remove signature header
2. If `WEBHOOK_SECRET` is set:
   - Verify header format: `X-Webhook-Signature: sha256=<hex>`
   - Recalculate signature with correct secret
   - Verify body hasn't been modified

### Webhook timeout

**Error:** Request times out after 30 seconds

**Solutions:**
1. Verify repository is indexed (speeds up retrieval)
2. Reduce `MAX_CONTEXT_CHUNKS` (less processing)
3. Increase timeout in your monitoring system
4. Check server logs for slow operations

## Docker Issues

### Container exits immediately

**Error:** `Container exited with code 1`

**Solution:**
```bash
# Check logs
docker-compose logs mcp-server --tail 50

# Likely missing env var or invalid config
# Edit .env and restart
docker-compose restart mcp-server
```

### Volumes not mounting

**Error:** Permission denied when accessing mounted files

**Solution:**
```bash
# Check volume permissions
ls -la /path/to/repo

# Ensure readable by user
chmod 755 /path/to/repo

# Restart services
docker-compose down
docker-compose up -d
```

### Network issues

**Error:** `Cannot reach service from container`

**Solution:**
```bash
# Verify network exists
docker network ls | grep git-debug-oracle

# Inspect network
docker network inspect git-debug-oracle

# Restart services to recreate network
docker-compose down
docker-compose up -d
```

## MCP Registration Issues

### Tools not appearing

**Solution:**
1. Verify MCP config syntax is valid JSON
2. Restart Claude Code / Claude Desktop completely
3. Check server logs: `docker-compose logs mcp-server`
4. Verify environment variables are set

### Tool calls failing

**Error:** `Tool execution failed`

**Solutions:**
1. Check server is running: `docker-compose ps`
2. Verify connectivity: `curl http://localhost:8000/health`
3. Check logs for error details
4. Verify repository is indexed

## Performance Issues

### Slow indexing

**Causes:**
- Network latency to embedding API
- Large repository with many files
- Low system resources

**Solutions:**
- Use faster embedding model
- Index smaller portions first
- Reduce `CHUNK_OVERLAP`
- Increase system RAM/CPU

### Slow retrieval

**Causes:**
- Large number of chunks (slow search)
- Network latency

**Solutions:**
- Reduce `TOP_K` parameter
- Optimize `CHUNK_SIZE`
- Use faster model

### Slow fix generation

**Causes:**
- Large context (many chunks)
- API latency

**Solutions:**
- Reduce `MAX_CONTEXT_CHUNKS`
- Use faster Claude model
- Reduce context size

## Getting Help

If none of these solutions work:

1. **Check logs:**
   ```bash
   docker-compose logs -f --tail 100
   ```

2. **Verify configuration:**
   ```bash
   echo $ANTHROPIC_API_KEY
   echo $EMBEDDING_API_KEY
   echo $REPO_PATH
   ```

3. **Test connectivity:**
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:6333/health
   ```

4. **Report issue on GitHub:**
   - Include error message and logs
   - Include system info (OS, Docker version)
   - Include configuration (redact API keys)
