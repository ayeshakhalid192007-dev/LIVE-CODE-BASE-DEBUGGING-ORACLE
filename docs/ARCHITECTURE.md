# Architecture

System design, data flow, and component interactions.

---

## System Overview

Git Debug Oracle is an MCP server that debugs errors in Python codebases by:
1. Indexing your Git repository incrementally
2. Embedding code at function granularity
3. Storing chunks with commit metadata in Qdrant
4. Retrieving relevant code + diffs when errors occur
5. Using Claude to generate fixes with reasoning

**Deployment model**: Runs on developer's machine or in their infrastructure. No data leaves except API calls to Claude and embedding providers.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Claude Code / Claude Desktop            │
│                    (MCP Client - Calls Tools)                   │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                    MCP Protocol (stdio)
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                         MCP Server                              │
│                   (git_debug_oracle/server.py)                  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ MCP Tools Layer                                          │   │
│  │  • index_repo                                            │   │
│  │  • debug_error                                           │   │
│  │  • search_codebase                                       │   │
│  │  • get_index_status                                      │   │
│  │  • get_recent_diffs                                      │   │
│  └──────┬─────────────────────────────────────────────────┬─┘   │
│         │                                                 │     │
│  ┌──────▼──────────────┐  ┌────────────────────────────┐ │     │
│  │ Indexing Pipeline   │  │ Retrieval Pipeline         │ │     │
│  │                     │  │                            │ │     │
│  │ • Repo Reader       │  │ • Query Constructor        │ │     │
│  │ • File Filter       │  │ • Qdrant Retriever         │ │     │
│  │ • Chunker           │  │ • Recency Weighting        │ │     │
│  │ • Metadata          │  │ • Result Formatter         │ │     │
│  │ • Embedder          │  │ • Diff Retriever           │ │     │
│  │ • Qdrant Upserter   │  │                            │ │     │
│  └──────┬──────────────┘  └────────────┬───────────────┘ │     │
│         │                              │                 │     │
│         │  ┌───────────────────────────┴──────────────┐  │     │
│         │  │                                          │  │     │
│         └──▶ Fix Generation Pipeline  ◀──────────────┘  │     │
│            │                                             │     │
│            │ • Context Assembler                         │     │
│            │ • Claude Client                             │     │
│            │ • Proposal Parser                           │     │
│            │ • Confidence Scorer                         │     │
│            └──────────────────┬──────────────────────────┘     │
│                               │                                 │
└───────────────────────────────┼─────────────────────────────────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
    ┌───────▼────────┐  ┌──────▼──────┐  ┌────────▼────────┐
    │  Git Watcher   │  │  Qdrant     │  │  Claude API     │
    │  (Local Repo)  │  │  (Local DB) │  │  (Remote Call)  │
    └────────────────┘  └─────────────┘  └─────────────────┘
```

---

## Component Organization

### Core Layers

**1. MCP Tools Layer** (`src/git_debug_oracle/mcp_tools/`)

Exposes all functionality as MCP tools. Each tool is a thin adapter:
- Accepts tool input (Pydantic model)
- Delegates to appropriate pipeline
- Returns structured output

**2. Indexing Pipeline** (`src/git_debug_oracle/indexer/`)

Processes repository and stores code in Qdrant:
- `repo_reader.py` — Extracts files from Git commits
- `file_filter.py` — Filters non-code files (images, binaries)
- `chunker.py` — Splits code into function-level chunks with overlap
- `metadata.py` — Extracts commit hash, author, timestamp, line ranges
- `pipeline.py` — Orchestrates flow: read → filter → chunk → embed → upsert

**3. Retrieval Pipeline** (`src/git_debug_oracle/retriever/`)

Finds relevant code when error occurs:
- `query_constructor.py` — Builds vector search query from error metadata
- `qdrant_retriever.py` — Performs vector search in Qdrant
- `recency_weighting.py` — Boosts scores for recent commits
- `result_formatter.py` — Structures results for downstream use
- `git_diff_retriever.py` — Fetches diffs for top results

**4. Fix Generation Pipeline** (`src/git_debug_oracle/fix_generation/`)

Generates fix proposals using Claude:
- `context.py` — Assembles prompt context from retrieval results
- `claude_client.py` — Calls Claude API with prompt caching
- `parser.py` — Parses fix proposal from Claude response
- `scoring.py` — Calculates confidence score
- `fallback.py` — Graceful degradation if Claude unavailable

**5. Infrastructure Layers**

- `embedder/` — Embedding generation (Voyage AI or OpenAI)
- `git_watcher/` — Git repository reading and diff tracking
- `utils/` — Qdrant client wrapper, logging setup
- `webhook/` — FastAPI webhook endpoint for error ingestion
- `error_ingestion/` — Error payload parsing and stacktrace handling

---

## Data Flow

### Indexing Flow

```
User calls: index_repo(repo_path="/path/to/repo", force_full=true)
                │
                ▼
    MCP Tools: index_repo.py
                │
                ▼
    Repo Reader: Extract files from Git commits
                │
                ▼
    File Filter: Skip binary, images, non-code
                │
                ▼
    Chunker: Split into function-level chunks (size=1000, overlap=200)
                │
                ▼
    Metadata Extractor: Capture commit hash, author, timestamp, file path, lines
                │
                ▼
    Embedder: Batch chunks, call Voyage/OpenAI API
                │
                ▼
    Qdrant Upserter: Create collection if missing, upsert chunks with metadata
                │
                ▼
    Return: IndexStatus { repo_path, total_chunks, last_indexed_commit, ... }
```

### Retrieval Flow

```
User calls: debug_error(file_path="src/api.py", line_number=105, 
                        error_message="...", stacktrace="...")
                │
                ▼
    MCP Tools: debug_error.py
                │
                ├─────────────────────────────────────┐
                │                                     │
                ▼                                     ▼
    Error Parser              Query Constructor
    Extract: file, line,      Build: combined query from
    error_type, function      file, line, error message
                │                                     │
                │             ┌───────────────────────┘
                │             │
                ▼             ▼
    Qdrant Retriever: Vector search + metadata filtering
                │
                ▼
    Recency Weighting: Boost recent commits
                │
                ▼
    Git Diff Retriever: Fetch diffs for top N results
                │
                ▼
    Result Formatter: Structure results with code + diffs
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
Return to Claude    Context Assembler
(if webhook)        (for fix generation)
                    │
                    ▼
            Claude Client: Call Claude API
                    │
                    ▼
            Proposal Parser: Extract root_cause, patch, confidence
                    │
                    ▼
            Return: FixProposal { root_cause, affected_file, 
                                  code_patch, confidence, ... }
```

---

## Dependency Direction

**Strict unidirectional dependency flow:**

```
MCP Tools Layer
    ↑
    │ (delegates to)
Indexing ←────────────────┐
    ↑                     │
    │ (stores in)         │
Qdrant                    │
    ↑ (queries)           │
    │                     │
Retrieval ←──────┐        │
    ↑            │        │
    │ (sends to) │        │
Fix Generation   │        │
    ↑            │        │
    │ (returns)  │        │
Claude API       │        │
                 │        │
    └────────────┴────────┘
    (no circular deps)
```

**Rules:**
- Fix Generation can import from Retrieval
- Retrieval CANNOT import from Fix Generation
- Indexing can import from Embedder/Git Watcher
- Indexing CANNOT import from Retrieval

This ensures clean separation and predictable dependencies.

---

## Domain Types

All domain types defined in `src/git_debug_oracle/types.py`:

**CodeChunk** — A piece of code extracted from repository
```python
content: str              # Code text
file_path: str            # src/api.py
start_line: int           # 105
end_line: int             # 120
commit_hash: str          # abc123...
commit_author: str        # alice@example.com
commit_timestamp: datetime
function_name: Optional[str]  # "handle_request"
embedding: Optional[list[float]]
chunk_id: str             # Unique ID in Qdrant
```

**RetrievalResult** — Result from vector search
```python
chunk: CodeChunk
score: float              # Vector similarity (0-1)
recency_score: float      # Recency boost (0-1)
combined_score: float     # Final score
rank: int                 # Position in results
```

**FixProposal** — Proposed fix for error
```python
root_cause: str           # What went wrong
affected_file: str        # src/api.py
affected_lines: tuple[int, int]  # (105, 120)
introducing_commit: str   # abc123
code_patch: str           # The fix
explanation: str          # Why it works
confidence: float         # 0.0-1.0
reasoning_trace: list[str]  # Step-by-step analysis
```

---

## Configuration

All configuration via environment variables (no hardcoded values):

**Required:**
- `ANTHROPIC_API_KEY` — Claude API key
- `EMBEDDING_API_KEY` — Voyage/OpenAI key
- `REPO_PATH` — Git repository path

**Qdrant:**
- `QDRANT_HOST` — localhost (default)
- `QDRANT_PORT` — 6333 (default)
- `QDRANT_COLLECTION` — git_debug_oracle (default)

**Tuning:**
- `CHUNK_SIZE` — 1000 (default)
- `CHUNK_OVERLAP` — 200 (default)
- `TOP_K` — 5 (default)
- `RECENT_COMMIT_WINDOW` — 30 days (default)

See `docs/CONFIGURATION.md` for complete reference.

---

## Performance Characteristics

**Indexing:**
- First indexing: ~30 seconds per 50k lines of code
- Incremental indexing: 1-3 seconds per commit (only changed files)
- Embedding generation: ~0.5 seconds per 100 chunks (batched)

**Retrieval:**
- Vector search: ~50ms (Qdrant local)
- Recency weighting: ~10ms
- Diff retrieval: ~20ms
- Total: ~80ms for search pipeline

**Fix Generation:**
- Context assembly: ~10ms
- Claude API call: 5-15 seconds (depends on context size)
- Proposal parsing: ~5ms
- Total: 5-15 seconds

**Memory:**
- Qdrant: ~100MB for 10k chunks
- MCP server process: ~150MB (Python overhead)
- Embeddings cache: ~5MB

---

## Scalability

**Repository Size:**
- Tested up to 500k lines of code
- Incremental indexing keeps it fast (only changes process)
- No theoretical limit

**Concurrent Users:**
- Single MCP server instance supports one user per machine
- Multiple users → run separate server instances with different `REPO_PATH`
- Each instance needs its own Qdrant collection or separate Qdrant instance

**Chunk Storage:**
- Qdrant handles millions of vectors efficiently
- 10k chunks ≈ 100MB Qdrant storage
- Scales linearly with code size

---

## Error Handling

**Graceful degradation:**
- If Qdrant unavailable → error returned (user sees clear message)
- If embedding API down → indexing paused, retrieval uses cached embeddings
- If Claude API down → fallback to code+diffs only (no fix proposal)
- If Git repository corrupted → clear error with recovery instructions

**Validation:**
- Configuration validated at startup (fails fast)
- Error payloads validated (returns 400 on invalid)
- Stacktraces parsed defensively (partial parsing OK)

---

## Security

**Data residency:**
- Repository code never leaves your machine
- Only API calls to Claude + embedding provider go out
- Qdrant runs locally (no remote connection by default)

**API key handling:**
- Keys loaded from `.env` file only
- Never logged or exposed
- Passed via environment variables to child processes

**Webhook authentication:**
- Optional signature validation via `WEBHOOK_SECRET`
- HMAC-SHA256 signature required if secret set
- Rate limiting recommended (not built-in)

---

## Development

**Testing strategy:**
- Unit tests: All pure functions, mocked external deps
- Integration tests: Real Qdrant instance, real Git repo
- No mock Qdrant in integration tests (use local Docker instance)

**Code organization:**
- Strict layer isolation (no circular imports)
- All public functions typed and documented
- Single responsibility per module

**Git workflow:**
- Feature branches: `phase/*`, `fix/*`, `replan/*`
- All code reviewed before merge
- Pre-commit hooks run linting + type checking

---

## Future Extensibility

**Planned:**
- Support for non-Git VCS (Mercurial, Perforce)
- Multi-language stacktrace support (Java, Go, C++)
- Real-time code analysis
- Custom embedding models
- Cloud Qdrant integration

**Architecture supports:**
- Pluggable embedder backends
- Pluggable Git reader backends
- Pluggable Qdrant backends (local, cloud, self-hosted)
- Configurable chunking strategies

---

## Resources

- **Tech Stack**: `specs/tech-stack.md`
- **Mission & Goals**: `specs/mission.md`
- **Roadmap**: `specs/roadmap.md`
- **Configuration**: `docs/CONFIGURATION.md`
