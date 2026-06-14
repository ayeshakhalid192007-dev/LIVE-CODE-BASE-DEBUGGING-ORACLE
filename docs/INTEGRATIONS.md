# Integrations

How to set up Git Debug Oracle across different development platforms.

---

## Claude Code (Recommended)

**Most seamless experience.** Tools appear directly in Claude Code's MCP tools list.

### Setup

1. **Start the MCP server** (in repo directory):
```bash
uv run git-debug-oracle
```

2. **Register globally** (in another terminal):
```bash
claude mcp add --scope user live-code-oracle -- \
  /path/to/uv --directory /path/to/LIVE-CODE-BASE-DEBUGGING-ORACLE run git-debug-oracle
```

Replace `/path/to/uv` with output of `which uv` and `/path/to/...` with your repo directory.

3. **Verify** (in Claude Code):
```bash
claude mcp list
```

Should show: `live-code-oracle - ✔ Connected`

### Usage

1. Index repository:
   - Tool: `index_repo`
   - Parameters: `repo_path: /path/to/your/repo`, `branch: main`, `force_full: true`

2. When error occurs, call `debug_error`:
   - `file_path`, `line_number`, `error_message`, `stacktrace`

3. Claude returns FixProposal with root cause and fix.

---

## Claude Desktop

Works on macOS, Linux, Windows.

### Prerequisites

- Claude Desktop installed (https://claude.ai/download)
- Qdrant running locally
- `.env` file configured with API keys

### Setup

1. **Find paths**:
```bash
which uv                    # e.g., /Users/you/.local/bin/uv
pwd                         # your repo directory
```

2. **Edit config file**:
   - **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
   - **Linux**: `~/.config/Claude/claude_desktop_config.json`

3. **Add MCP server entry**:
```json
{
  "mcpServers": {
    "live-code-oracle": {
      "command": "/Users/you/.local/bin/uv",
      "args": [
        "--directory",
        "/path/to/LIVE-CODE-BASE-DEBUGGING-ORACLE",
        "run",
        "git-debug-oracle"
      ],
      "env": {
        "ANTHROPIC_API_KEY": "sk-ant-xxxxx",
        "EMBEDDING_API_KEY": "xxxxx",
        "REPO_PATH": "/path/to/your/repo",
        "QDRANT_HOST": "localhost",
        "QDRANT_PORT": "6333"
      }
    }
  }
}
```

4. **Restart Claude Desktop** completely.

5. **Verify**: Tools appear in Claude's tool panel.

### Usage

Same as Claude Code: call `index_repo`, then `debug_error`.

---

## Webhook Integration (Sentry, Datadog, CloudWatch, etc.)

Send errors directly to Oracle without Claude.

### Endpoint

```
POST http://localhost:8000/webhook/error
```

### Headers

```
Content-Type: application/json
X-Webhook-Signature: (optional, if WEBHOOK_SECRET set)
```

### Payload

```json
{
  "file_path": "src/api.py",
  "line_number": 105,
  "error_message": "ConnectionError: failed to connect",
  "stacktrace": "Traceback (most recent call last):\n  File \"src/api.py\", line 105...",
  "error_type": "ConnectionError",
  "timestamp": "2026-06-14T14:27:39Z",
  "source_system": "sentry"
}
```

### Example: Sentry Integration

1. **In Sentry dashboard**, go to Integrations → Custom
2. **Create webhook** pointing to `http://your-server:8000/webhook/error`
3. **Enable** for errors matching your filters
4. **Test**: Trigger an error in your app, verify it POSTs to Oracle

### Example: Datadog Integration

1. **In Datadog**, go to Integrations → Webhooks
2. **Create custom webhook** with URL: `http://your-server:8000/webhook/error`
3. **Add monitor** that triggers webhook on error threshold

---

## Webhook Authentication

If you set `WEBHOOK_SECRET` in `.env`:

```bash
export WEBHOOK_SECRET="your-shared-secret-here"
```

Then all webhook requests must include valid signature:

```
X-Webhook-Signature: sha256=<hmac-signature>
```

Signature is HMAC-SHA256 of request body with secret as key.

---

## Local Testing

Test the webhook endpoint locally:

```bash
# Terminal 1: Start server
uv run git-debug-oracle

# Terminal 2: Send test error
curl -X POST http://localhost:8000/webhook/error \
  -H "Content-Type: application/json" \
  -d '{
    "file_path": "src/test.py",
    "line_number": 42,
    "error_message": "ValueError: invalid value",
    "stacktrace": "Traceback (most recent call last):\n  File \"src/test.py\", line 42, in func\n    x.split()"
  }'
```

Should return:
```json
{
  "root_cause": "...",
  "affected_file": "src/test.py",
  "code_patch": "...",
  "confidence": 0.85,
  "explanation": "..."
}
```

---

## Troubleshooting Integrations

**Tools don't appear in Claude Code?**
- Run `claude mcp list` — should show your server connected
- Check `.env` is properly configured
- Restart Claude Code completely

**"Cannot connect to MCP server"?**
- Verify server is running: `uv run git-debug-oracle` in repo directory
- Check ports: default is port 8000 for webhook
- Check logs for startup errors

**Webhook requests failing?**
- Verify Qdrant is running: `curl http://localhost:6333/health`
- Check `.env` has all required keys
- Check firewall allows localhost:8000

**MCP server crashes on startup?**
- Check `.env.example` for all required variables
- Verify all API keys are valid
- Check `REPO_PATH` exists and is a valid Git repository

---

## Next Steps

- **[QUICKSTART.md](QUICKSTART.md)** — Detailed setup walkthrough
- **[CONFIGURATION.md](CONFIGURATION.md)** — All configuration options
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** — Common issues and solutions
