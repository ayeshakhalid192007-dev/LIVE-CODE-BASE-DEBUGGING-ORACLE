# Configuration Reference

Complete documentation of all environment variables and configuration options.

## Required Configuration

These must be set before the server starts.

### ANTHROPIC_API_KEY

**Type:** String (API key)
**Required:** Yes
**Description:** API key for Claude API to generate fix proposals

**How to get:**
1. Go to https://console.anthropic.com/account/keys
2. Create a new API key
3. Copy and paste into `.env`

**Example:**
```bash
ANTHROPIC_API_KEY=sk-ant-v0xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### EMBEDDING_API_KEY

**Type:** String (API key)
**Required:** Yes
**Description:** API key for embedding provider (Voyage AI or OpenAI)

**Voyage AI:**
- Go to https://www.voyageai.com
- Sign up and create API key
- Works with `EMBEDDING_MODEL=voyage-code-2`

**OpenAI:**
- Go to https://platform.openai.com/api-keys
- Create new secret key
- Works with `EMBEDDING_MODEL=text-embedding-3-small`

**Example:**
```bash
# Voyage AI
EMBEDDING_API_KEY=pa-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI
EMBEDDING_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### REPO_PATH

**Type:** String (filesystem path)
**Required:** Yes
**Description:** Absolute path to Git repository to index

**Requirements:**
- Must be absolute path (start with `/`)
- Must exist and be readable
- Must be a valid Git repository (has `.git` directory)
- User must have read permissions

**Examples:**
```bash
REPO_PATH=/home/user/my-project
REPO_PATH=/path/to/git-debug-oracle
REPO_PATH=/var/projects/python-app
```

## Optional Configuration

These have sensible defaults but can be customized.

### EMBEDDING_MODEL

**Type:** String (enum)
**Default:** `voyage-code-2`
**Description:** Which embedding model to use

**Valid values:**
- `voyage-code-2` — Voyage AI optimized for code (recommended)
- `text-embedding-3-small` — OpenAI general-purpose embeddings

**Performance:**
- `voyage-code-2` — Better accuracy on code, larger model
- `text-embedding-3-small` — Faster, smaller model

**Example:**
```bash
EMBEDDING_MODEL=voyage-code-2
```

### QDRANT_HOST

**Type:** String (hostname or IP)
**Default:** `localhost`
**Description:** Hostname or IP address of Qdrant vector database

**Docker Compose:** Use `qdrant` (service name)
**Local:** Use `localhost` or `127.0.0.1`

**Example:**
```bash
QDRANT_HOST=qdrant              # Docker Compose
QDRANT_HOST=localhost           # Local development
QDRANT_HOST=192.168.1.100       # Remote server
```

### QDRANT_PORT

**Type:** Integer (port number)
**Default:** `6333`
**Description:** Port number for Qdrant API

**Valid range:** 1-65535

**Example:**
```bash
QDRANT_PORT=6333
```

### QDRANT_COLLECTION

**Type:** String (collection name)
**Default:** `git_debug_oracle`
**Description:** Name of Qdrant collection to store code chunks

**Naming:** Lowercase, alphanumeric, underscores allowed

**Example:**
```bash
QDRANT_COLLECTION=git_debug_oracle
QDRANT_COLLECTION=my_project_index
```

### QDRANT_API_KEY

**Type:** String (API key)
**Default:** Empty (no auth)
**Description:** API key for Qdrant Cloud (optional)

**When needed:** Only if using Qdrant Cloud with authentication

**Example:**
```bash
QDRANT_API_KEY=your-qdrant-api-key
```

### CHUNK_SIZE

**Type:** Integer (characters)
**Default:** `1000`
**Description:** Maximum characters per code chunk

**Valid range:** 100-10000
**Tuning:**
- Smaller (100-500): More chunks, better granularity
- Larger (2000+): Fewer chunks, more context per chunk

**Example:**
```bash
CHUNK_SIZE=1000
```

### CHUNK_OVERLAP

**Type:** Integer (characters)
**Default:** `200`
**Description:** Overlapping characters between adjacent chunks

**Valid range:** 0-1000
**Tuning:**
- 0: No overlap, fastest
- 200-400: Good balance (recommended)
- > 400: More overlap, slower indexing

**Example:**
```bash
CHUNK_OVERLAP=200
```

### TOP_K

**Type:** Integer (count)
**Default:** `5`
**Description:** Number of top retrieval results to return

**Valid range:** 1-50
**Tuning:**
- Smaller (1-3): Fastest, most confident results
- Larger (5-10): More context, more computation

**Example:**
```bash
TOP_K=5
```

### RECENT_COMMIT_WINDOW

**Type:** Integer (days)
**Default:** `30`
**Description:** Number of days to consider a commit "recent" for recency weighting

**Valid range:** 1-365
**Tuning:**
- Smaller (7-14): Recent changes rank much higher
- Larger (30-90): More balanced weighting

**Example:**
```bash
RECENT_COMMIT_WINDOW=30
```

### MAX_CONTEXT_CHUNKS

**Type:** Integer (count)
**Default:** `10`
**Description:** Maximum code chunks to include in fix generation context

**Valid range:** 1-50
**Tuning:**
- Smaller (3-5): Faster generation, less context
- Larger (10-20): More context, slower generation

**Example:**
```bash
MAX_CONTEXT_CHUNKS=10
```

### WATCH_BRANCH

**Type:** String (branch name)
**Default:** `main`
**Description:** Git branch to watch for incremental indexing

**Example:**
```bash
WATCH_BRANCH=main
WATCH_BRANCH=master
WATCH_BRANCH=develop
```

### WEBHOOK_PORT

**Type:** Integer (port number)
**Default:** `8000`
**Description:** Port number for webhook endpoint

**Valid range:** 1-65535

**Example:**
```bash
WEBHOOK_PORT=8000
```

### WEBHOOK_SECRET

**Type:** String (secret)
**Default:** Empty (no validation)
**Description:** Shared secret for webhook signature validation

**When to use:** When webhook comes from external system (Sentry, Datadog, etc.)

**Validation:**
- If set: Webhook must include `X-Webhook-Signature` header
- Signature format: `sha256=<hexdigest>`
- Computed using HMAC-SHA256 with this secret

**Example:**
```bash
WEBHOOK_SECRET=your-shared-secret-key
```

### LOG_LEVEL

**Type:** String (enum)
**Default:** `INFO`
**Description:** Minimum log level to output

**Valid values:**
- `DEBUG` — Detailed debug information
- `INFO` — Normal operation (recommended)
- `WARNING` — Warnings and errors only
- `ERROR` — Errors only

**Example:**
```bash
LOG_LEVEL=INFO
```

### CLAUDE_MODEL

**Type:** String (model name)
**Default:** `claude-sonnet-4-20250514`
**Description:** Claude model to use for fix generation

**Valid models:**
- `claude-sonnet-4-20250514` — Latest Sonnet (recommended)
- `claude-opus-4-1` — Opus model (slower, more capable)

**Example:**
```bash
CLAUDE_MODEL=claude-sonnet-4-20250514
```

## Configuration File Format

Load from `.env` file in project root:

```bash
# Comments start with #
ANTHROPIC_API_KEY=sk-ant-...
EMBEDDING_API_KEY=...

# Empty lines are ignored
REPO_PATH=/path/to/repo

# No spaces around = sign
CHUNK_SIZE=1000
```

## Environment Variable Precedence

Variables are loaded in this order (later overrides earlier):

1. `.env` file (if exists)
2. `.env.local` file (if exists, not committed)
3. Shell environment variables
4. Docker environment variables

## Validation

Configuration is validated at startup:

- Required fields missing → Clear error message with fix instructions
- Invalid port numbers → Error with valid range
- Invalid paths → Error with current working directory
- Type mismatches → Error with expected type

**Example:**
```
Configuration Error: ANTHROPIC_API_KEY not set.
This is required to generate fix proposals using Claude.
Set it: export ANTHROPIC_API_KEY="sk-..."
Get it: https://console.anthropic.com/account/keys
```

## Docker Compose

Override variables in docker-compose.yml:

```yaml
services:
  mcp-server:
    environment:
      CHUNK_SIZE: "2000"
      TOP_K: "10"
```

Or use `.env` file (docker-compose loads automatically):

```bash
cp .env.compose .env
# Edit .env
docker-compose up
```
