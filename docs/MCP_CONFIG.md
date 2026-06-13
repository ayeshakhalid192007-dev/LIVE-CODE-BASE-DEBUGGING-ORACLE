# MCP Configuration Guide

Set up git-debug-oracle as an MCP server in Claude Code and Claude Desktop.

## Claude Code Setup

### Step 1: Add to Claude Code config

Find your Claude Code settings file:

**Linux/macOS:**
```bash
~/.claude/settings.json
```

**Windows:**
```
%APPDATA%\Claude\settings.json
```

### Step 2: Configure MCP server

Add this to `settings.json`:

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
        "REPO_PATH": "/path/to/your/repository"
      }
    }
  }
}
```

### Step 3: Or use Docker Compose

If running via Docker Compose:

```json
{
  "mcpServers": {
    "git-debug-oracle": {
      "command": "docker-compose",
      "args": ["exec", "-T", "mcp-server", "python", "-m", "git_debug_oracle.server"],
      "env": {
        "COMPOSE_PROJECT_NAME": "git-debug-oracle"
      }
    }
  }
}
```

### Step 4: Restart Claude Code

- Close Claude Code completely
- Reopen Claude Code
- Tools should appear in MCP tool list

### Step 5: Verify

Call the health check:

```
Tool: get_index_status
Parameters:
  repo_path: /path/to/your/repository
```

Should return status information without errors.

## Claude Desktop Setup

### Step 1: Find Claude config

**macOS:**
```bash
~/Library/Application\ Support/Claude/claude_desktop_config.json
```

**Linux:**
```bash
~/.config/Claude/claude_desktop_config.json
```

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

### Step 2: Add MCP server config

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
        "REPO_PATH": "/path/to/your/repository"
      }
    }
  }
}
```

### Step 3: Restart Claude Desktop

- Close Claude Desktop completely
- Reopen Claude Desktop
- Look for hammer icon (🔨) to see available tools

### Step 4: Verify in Claude

In a conversation, type:

```
What MCP tools are available?
```

Claude should list git-debug-oracle tools:
- index_repo
- debug_error
- search_codebase
- get_recent_diffs
- get_index_status

## Docker Compose Variants

### Pre-started services

If Docker Compose services already running:

```json
{
  "mcpServers": {
    "git-debug-oracle": {
      "command": "docker",
      "args": [
        "exec",
        "git-debug-oracle-mcp",
        "python",
        "-m",
        "git_debug_oracle.server"
      ]
    }
  }
}
```

### Remote server

If Qdrant/MCP running on different machine:

```json
{
  "mcpServers": {
    "git-debug-oracle": {
      "command": "python",
      "args": ["-m", "git_debug_oracle.server"],
      "env": {
        "QDRANT_HOST": "192.168.1.100",
        "QDRANT_PORT": "6333",
        "ANTHROPIC_API_KEY": "sk-ant-...",
        "EMBEDDING_API_KEY": "...",
        "REPO_PATH": "/path/to/repository"
      }
    }
  }
}
```

## Troubleshooting

### Tools not appearing

1. Check Claude config syntax (valid JSON)
2. Verify Python path: `which python` or `python --version`
3. Verify environment variables are set correctly
4. Check logs:
   ```bash
   docker-compose logs -f mcp-server
   ```

### Connection errors

1. Verify Qdrant is running:
   ```bash
   curl http://localhost:6333/health
   ```

2. Check port conflicts:
   ```bash
   lsof -i :8000
   lsof -i :6333
   ```

3. Verify API keys are correct:
   - ANTHROPIC_API_KEY from https://console.anthropic.com/account/keys
   - EMBEDDING_API_KEY from Voyage AI or OpenAI

### Tool calls failing

1. Verify repository is indexed:
   ```bash
   Tool: get_index_status
   ```

2. Check logs for errors:
   ```bash
   docker-compose logs mcp-server | grep ERROR
   ```

3. Verify repository path exists and is readable

## Available MCP Tools

### index_repo

Index a Git repository

```
Parameters:
  repo_path: (string) Path to repository
  branch: (string, optional) Branch to index (default: main)
  force_full: (boolean, optional) Force full reindex (default: false)
```

### debug_error

Debug an error and get fix proposal

```
Parameters:
  file_path: (string) File where error occurred
  line_number: (integer) Line number
  error_message: (string, optional) Error message
  function_name: (string, optional) Function name
  stacktrace: (string, optional) Full stacktrace
```

### search_codebase

Search indexed code

```
Parameters:
  query: (string) Search query
  top_k: (integer, optional) Number of results (default: 5)
```

### get_recent_diffs

Get diffs from recent commits

```
Parameters:
  repo_path: (string) Repository path
  num_commits: (integer, optional) Number of commits (default: 5)
```

### get_index_status

Get current index status

```
Parameters:
  repo_path: (string) Repository path
```

Returns: Indexing status, last indexed commit, chunk count

## Tips & Best Practices

1. **Always index first** — Call `index_repo` before calling `debug_error`
2. **Keep API keys secure** — Never commit credentials to git
3. **Use .env files** — Store secrets in `.env` and load via Docker
4. **Monitor logs** — Check logs when tools return unexpected results
5. **Update configs** — When adding new repos, update `REPO_PATH`

## Advanced Configuration

### Multiple repositories

Create multiple MCP server entries:

```json
{
  "mcpServers": {
    "git-debug-oracle-app": {
      "command": "python",
      "args": ["-m", "git_debug_oracle.server"],
      "env": {
        "REPO_PATH": "/path/to/app"
      }
    },
    "git-debug-oracle-lib": {
      "command": "python",
      "args": ["-m", "git_debug_oracle.server"],
      "env": {
        "REPO_PATH": "/path/to/lib"
      }
    }
  }
}
```

### Custom Qdrant instance

Point to custom Qdrant:

```json
{
  "env": {
    "QDRANT_HOST": "qdrant.example.com",
    "QDRANT_PORT": "6333",
    "QDRANT_API_KEY": "your-api-key"
  }
}
```

### Logging

Enable debug logging:

```json
{
  "env": {
    "LOG_LEVEL": "DEBUG"
  }
}
```

Check logs:

```bash
docker-compose logs -f mcp-server --tail 100
```
