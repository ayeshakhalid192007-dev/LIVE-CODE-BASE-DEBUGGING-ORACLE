# Architecture Specification

## Directory Layout

```
git-debug-oracle/
├── src/
│   └── git_debug_oracle/
│       ├── __init__.py
│       ├── server.py                 # MCP server entry point
│       ├── config.py                 # Configuration loading and validation
│       ├── mcp_tools/
│       │   ├── __init__.py
│       │   ├── index_repo.py         # Full repository indexing tool
│       │   ├── debug_error.py        # Error debugging and fix generation tool
│       │   ├── search_codebase.py    # Arbitrary code search tool
│       │   ├── get_recent_diffs.py   # Recent commit diffs tool
│       │   └── get_index_status.py   # Index status query tool
│       ├── indexer/
│       │   ├── __init__.py
│       │   ├── chunker.py            # Code chunking logic
│       │   ├── file_filter.py        # File type filtering
│       │   ├── metadata.py           # Chunk metadata extraction
│       │   └── pipeline.py           # Indexing orchestration
│       ├── retriever/
│       │   ├── __init__.py
│       │   ├── query_builder.py      # Query construction from errors
│       │   ├── vector_search.py      # Qdrant search execution
│       │   ├── recency_weighting.py  # Commit recency scoring
│       │   └── result_ranker.py      # Result ranking and filtering
│       ├── git_watcher/
│       │   ├── __init__.py
│       │   ├── repo_reader.py        # Git repository file reading
│       │   ├── diff_extractor.py     # Commit diff extraction
│       │   └── commit_tracker.py     # Last indexed commit tracking
│       ├── embedder/
│       │   ├── __init__.py
│       │   ├── voyage_client.py      # Voyage AI embedding client
│       │   ├── openai_client.py      # OpenAI embedding client
│       │   └── batch_processor.py    # Batch embedding processing
│       ├── fix_generator/
│       │   ├── __init__.py
│       │   ├── context_assembler.py  # Context block assembly for Claude
│       │   ├── claude_client.py      # Claude API client
│       │   └── proposal_parser.py    # Fix proposal parsing
│       ├── webhook/
│       │   ├── __init__.py
│       │   ├── app.py                # FastAPI application
│       │   ├── error_parser.py       # Error payload parsing
│       │   └── auth.py               # Webhook authentication
│       └── utils/
│           ├── __init__.py
│           ├── logging.py            # Logging configuration
│           └── qdrant_client.py      # Qdrant client wrapper
├── tests/
│   ├── __init__.py
│   ├── unit/
│   │   ├── test_chunker.py
│   │   ├── test_file_filter.py
│   │   ├── test_metadata.py
│   │   ├── test_query_builder.py
│   │   ├── test_recency_weighting.py
│   │   ├── test_error_parser.py
│   │   └── test_context_assembler.py
│   ├── integration/
│   │   ├── test_indexing_pipeline.py
│   │   ├── test_retrieval_pipeline.py
│   │   └── test_fix_generation.py
│   └── fixtures/
│       ├── sample_repo/              # Small test repository
│       ├── error_payloads.json       # Sample error payloads
│       └── expected_chunks.json      # Expected indexing results
├── docs/
│   ├── mcp_tools.md                  # MCP tool documentation
│   ├── error_formats.md              # Supported error payload formats
│   └── architecture_diagram.png      # System architecture diagram
├── .env.example                      # Example environment variables
├── .gitignore
├── .pre-commit-config.yaml
├── pyproject.toml
├── README.md
├── LICENSE
└── CONTRIBUTING.md
```

## Domain Types

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class CodeChunk:
    """A chunk of code extracted from a repository file."""
    content: str
    file_path: str
    start_line: int
    end_line: int
    commit_hash: str
    commit_author: str
    commit_timestamp: datetime
    function_name: Optional[str]
    embedding: Optional[list[float]]
    chunk_id: str


@dataclass
class CommitDiff:
    """A diff from a single commit."""
    commit_hash: str
    commit_author: str
    commit_timestamp: datetime
    commit_message: str
    file_path: str
    diff_content: str
    additions: int
    deletions: int


@dataclass
class ErrorPayload:
    """Structured error information from external systems."""
    error_type: str
    error_message: str
    file_path: Optional[str]
    line_number: Optional[int]
    function_name: Optional[str]
    stacktrace: str
    timestamp: datetime
    source_system: Optional[str]
    additional_context: dict[str, str]


@dataclass
class RetrievalResult:
    """A single result from vector search."""
    chunk: CodeChunk
    score: float
    recency_score: float
    combined_score: float
    rank: int


@dataclass
class FixProposal:
    """A proposed fix for an error with reasoning."""
    root_cause: str
    affected_file: str
    affected_lines: tuple[int, int]
    introducing_commit: str
    code_patch: str
    explanation: str
    confidence: float
    reasoning_trace: list[str]


@dataclass
class IndexStatus:
    """Current state of the repository index."""
    repo_path: str
    branch: str
    last_indexed_commit: str
    last_indexed_timestamp: datetime
    total_chunks: int
    total_files: int
    collection_name: str
    is_indexing: bool


@dataclass
class RepoConfig:
    """Repository-specific configuration."""
    repo_path: str
    watch_branch: str
    file_extensions: list[str]
    exclude_patterns: list[str]
    chunk_size: int
    chunk_overlap: int
```

## Data Flow

### 1. Indexing Flow

**Step 1: Trigger Detection**
`mcp_tools/index_repo.py` receives MCP tool call with repo path and optional commit hash. Validates parameters and initiates indexing.

**Step 2: Commit Identification**
`git_watcher/commit_tracker.py` reads last indexed commit from Qdrant metadata. `git_watcher/repo_reader.py` compares with current HEAD to identify new commits.

**Step 3: File Extraction**
`git_watcher/repo_reader.py` extracts changed files from new commits using GitPython. `indexer/file_filter.py` filters out binary files, images, and non-code files based on extension and content.

**Step 4: Chunking**
`indexer/chunker.py` splits each file into function-level chunks with configured overlap. `indexer/metadata.py` extracts commit hash, author, timestamp, file path, and line range for each chunk.

**Step 5: Embedding Generation**
`indexer/pipeline.py` batches chunks and sends to `embedder/voyage_client.py` or `embedder/openai_client.py`. Embeddings are generated in batches of 100 chunks.

**Step 6: Qdrant Upsert**
`utils/qdrant_client.py` upserts chunks with embeddings and metadata into Qdrant collection. Chunk ID is hash of file path + line range + commit hash.

**Step 7: Status Update**
`git_watcher/commit_tracker.py` updates last indexed commit in Qdrant metadata. `utils/logging.py` logs completion with chunk count and duration.

---

### 2. Error-to-Fix Flow

**Step 1: Error Ingestion**
`webhook/app.py` receives POST request at /webhook/error. `webhook/auth.py` validates WEBHOOK_SECRET header. `webhook/error_parser.py` parses JSON payload into ErrorPayload.

**Step 2: Query Construction**
`retriever/query_builder.py` extracts file path, line number, function name, and error message from ErrorPayload. Constructs natural language query combining error context.

**Step 3: Vector Search**
`retriever/vector_search.py` generates embedding for query using same embedding model as indexing. Queries Qdrant with metadata filters for file path if available.

**Step 4: Recency Weighting**
`retriever/recency_weighting.py` applies time-based score boost to chunks from recent commits. Boost factor decays exponentially based on commit age.

**Step 5: Result Ranking**
`retriever/result_ranker.py` combines vector similarity score with recency score. Sorts results by combined score and returns top K chunks.

**Step 6: Diff Retrieval**
`git_watcher/diff_extractor.py` fetches full diffs for commits containing top-ranked chunks. Extracts context around affected lines.

**Step 7: Context Assembly**
`fix_generator/context_assembler.py` combines error info, top chunks, and diffs into structured prompt for Claude. Includes file paths, line numbers, and commit messages.

**Step 8: Fix Generation**
`fix_generator/claude_client.py` sends prompt to Claude API with prompt caching enabled. `fix_generator/proposal_parser.py` extracts root cause, patch, and reasoning from response.

**Step 9: Response Return**
`mcp_tools/debug_error.py` wraps FixProposal in MCP tool response and returns to client. `utils/logging.py` logs fix generation with confidence and duration.

## Retrieval Path

**Query Construction**
When an ErrorPayload arrives, the query builder extracts structured fields (file_path, line_number, function_name, error_type) and unstructured text (error_message, stacktrace). It constructs a natural language query that combines these elements:

```
"Error in {file_path} at line {line_number} in function {function_name}: {error_type} - {error_message}"
```

If file_path is missing, the query focuses on error_type and error_message. If function_name is present, it is weighted heavily in the query.

**Qdrant Query Execution**
The query text is embedded using the same model used during indexing. The embedding vector is sent to Qdrant with:
- Vector similarity search over the embedding field
- Metadata filter for file_path if available (exact match)
- Metadata filter for commit_timestamp within RECENT_COMMIT_WINDOW if recency weighting is enabled
- Limit set to TOP_K * 2 to allow for post-filtering

**Recency Weighting Application**
Each result from Qdrant has a base similarity score (0-1). The recency weighting module calculates a time-based boost:

```python
days_since_commit = (now - chunk.commit_timestamp).days
if days_since_commit <= RECENT_COMMIT_WINDOW:
    recency_boost = 1.0 - (days_since_commit / RECENT_COMMIT_WINDOW) * 0.5
else:
    recency_boost = 0.5

combined_score = base_score * recency_boost
```

Recent commits get up to 1.0x boost, older commits get 0.5x penalty. This ensures recent changes rank higher when similarity scores are close.

**Result Ranking and Assembly**
Results are sorted by combined_score descending. The top K results are selected. For each result, the system fetches:
- Full chunk content
- Commit metadata (hash, author, message, timestamp)
- Diff for the commit that introduced this chunk
- Surrounding context (chunks immediately before and after in the same file)

Results are packaged into RetrievalResult objects with all metadata intact.

## MCP Tool Contracts

### index_repo

**Input Schema**
```python
{
    "repo_path": str,           # Required: Absolute path to Git repository
    "commit_hash": str | None,  # Optional: Specific commit to index (default: HEAD)
    "force_full": bool          # Optional: Force full re-index (default: False)
}
```

**Output Schema**
```python
{
    "status": str,              # "success" or "error"
    "chunks_indexed": int,      # Number of chunks upserted
    "files_processed": int,     # Number of files indexed
    "last_commit": str,         # Commit hash that was indexed
    "duration_seconds": float,  # Time taken for indexing
    "error_message": str | None # Error details if status is "error"
}
```

**Internal Behavior**
Reads repo_path from config or input. If force_full is True, indexes entire repository from commit_hash or HEAD. If False, compares commit_hash to last indexed commit and indexes only changed files. Calls indexing pipeline, waits for completion, returns statistics.

**Errors**
- `repo_not_found`: repo_path does not exist or is not a Git repository
- `commit_not_found`: commit_hash does not exist in repository
- `qdrant_connection_failed`: Cannot connect to Qdrant
- `embedding_api_failed`: Embedding API returned error

---

### debug_error

**Input Schema**
```python
{
    "error_type": str,                    # Required: Type of error (e.g., "TypeError")
    "error_message": str,                 # Required: Error message text
    "stacktrace": str,                    # Required: Full stacktrace
    "file_path": str | None,              # Optional: File where error occurred
    "line_number": int | None,            # Optional: Line number of error
    "function_name": str | None,          # Optional: Function where error occurred
    "additional_context": dict[str, str]  # Optional: Extra metadata
}
```

**Output Schema**
```python
{
    "status": str,                  # "success" or "error"
    "fix_proposal": {
        "root_cause": str,          # Root cause analysis
        "affected_file": str,       # File to modify
        "affected_lines": [int, int], # Line range to modify
        "introducing_commit": str,  # Commit that introduced bug
        "code_patch": str,          # Proposed code change
        "explanation": str,         # Why this fix works
        "confidence": float,        # Confidence score 0-1
        "reasoning_trace": list[str] # Step-by-step reasoning
    } | None,
    "retrieval_results": list[dict], # Top chunks that informed fix
    "error_message": str | None      # Error details if status is "error"
}
```

**Internal Behavior**
Parses input into ErrorPayload. Constructs retrieval query. Performs vector search with recency weighting. Fetches diffs for top results. Assembles context for Claude. Calls Claude API to generate fix. Parses response into FixProposal. Returns structured output.

**Errors**
- `invalid_error_payload`: Required fields missing or malformed
- `no_retrieval_results`: Vector search returned no results
- `claude_api_failed`: Claude API returned error or timeout
- `fix_parsing_failed`: Could not parse fix from Claude response

---

### search_codebase

**Input Schema**
```python
{
    "query": str,                  # Required: Natural language search query
    "file_path_filter": str | None, # Optional: Filter to specific file
    "top_k": int                   # Optional: Number of results (default: 5)
}
```

**Output Schema**
```python
{
    "status": str,                 # "success" or "error"
    "results": list[{
        "content": str,            # Chunk content
        "file_path": str,          # File path
        "line_range": [int, int],  # Start and end line
        "commit_hash": str,        # Commit hash
        "commit_author": str,      # Commit author
        "commit_timestamp": str,   # ISO 8601 timestamp
        "score": float             # Similarity score
    }],
    "error_message": str | None    # Error details if status is "error"
}
```

**Internal Behavior**
Embeds query text. Performs vector search over Qdrant with optional file_path metadata filter. Returns top_k results sorted by similarity score. Does not apply recency weighting or fetch diffs.

**Errors**
- `empty_query`: query is empty or whitespace only
- `qdrant_connection_failed`: Cannot connect to Qdrant
- `embedding_api_failed`: Embedding API returned error

---

### get_recent_diffs

**Input Schema**
```python
{
    "num_commits": int,            # Optional: Number of recent commits (default: 10)
    "file_path_filter": str | None # Optional: Filter to specific file
}
```

**Output Schema**
```python
{
    "status": str,                 # "success" or "error"
    "diffs": list[{
        "commit_hash": str,        # Commit hash
        "commit_author": str,      # Commit author
        "commit_timestamp": str,   # ISO 8601 timestamp
        "commit_message": str,     # Commit message
        "file_path": str,          # File path
        "diff_content": str,       # Unified diff
        "additions": int,          # Lines added
        "deletions": int           # Lines deleted
    }],
    "error_message": str | None    # Error details if status is "error"
}
```

**Internal Behavior**
Reads last num_commits from repository using GitPython. For each commit, extracts diffs for all files or filtered file. Returns diffs in reverse chronological order.

**Errors**
- `repo_not_found`: Repository path not configured or invalid
- `git_error`: GitPython raised exception reading commits

---

### get_index_status

**Input Schema**
```python
{}  # No input parameters
```

**Output Schema**
```python
{
    "status": str,                 # "success" or "error"
    "index_status": {
        "repo_path": str,          # Repository path
        "branch": str,             # Watched branch
        "last_indexed_commit": str, # Last indexed commit hash
        "last_indexed_timestamp": str, # ISO 8601 timestamp
        "total_chunks": int,       # Total chunks in Qdrant
        "total_files": int,        # Total files indexed
        "collection_name": str,    # Qdrant collection name
        "is_indexing": bool        # Whether indexing is in progress
    } | None,
    "error_message": str | None    # Error details if status is "error"
}
```

**Internal Behavior**
Queries Qdrant for collection metadata. Reads last indexed commit from metadata store. Counts total chunks in collection. Checks if indexing operation is currently running. Returns current state.

**Errors**
- `qdrant_connection_failed`: Cannot connect to Qdrant
- `collection_not_found`: Collection does not exist (never indexed)

## Runtime Configuration

**Configuration Loading**
Configuration is loaded at server startup in `server.py` entry point. The `config.py` module uses `pydantic-settings` to load environment variables from `.env` file and system environment. All variables are parsed into a `Config` Pydantic model with type validation.

**Validation at Boot**
When the `Config` model is instantiated, Pydantic validates all fields. Required fields without values raise `ValidationError` with a message listing the missing field name and expected type. Invalid types (e.g., string for integer field) raise `ValidationError` with the field name and type mismatch. The server catches `ValidationError` at startup, logs the error with structlog, and exits with status code 1.

**Error Message Format**
Validation errors are formatted as:
```
Configuration error: Missing required field 'ANTHROPIC_API_KEY' (type: str)
Set this value in .env file or environment variable.
```

For invalid types:
```
Configuration error: Field 'QDRANT_PORT' has invalid type. Expected int, got 'abc'.
```

**Config Injection**
The validated `Config` object is passed as a parameter to all modules that need configuration. No global variables are used. The MCP server holds the config instance and passes it to tool handlers. Tool handlers pass it to business logic modules. This makes testing easier and prevents hidden dependencies.

**No Defaults for Critical Fields**
Fields like `ANTHROPIC_API_KEY`, `EMBEDDING_API_KEY`, and `REPO_PATH` have no defaults. If not set, the server refuses to start. Optional fields like `CHUNK_SIZE` and `TOP_K` have sensible defaults but can be overridden.

## Dependency Direction

**Layer Diagram**
```
┌─────────────────────────────────────────┐
│         MCP Tools Layer                 │  ← Entry points, tool handlers
│  (index_repo, debug_error, etc.)        │
└─────────────────────────────────────────┘
              ↓ calls
┌─────────────────────────────────────────┐
│       Business Logic Layer              │  ← Core domain logic
│  (indexer, retriever, fix_generator)    │
└─────────────────────────────────────────┘
              ↓ calls
┌─────────────────────────────────────────┐
│      Infrastructure Layer               │  ← External integrations
│  (git_watcher, embedder, utils)         │
└─────────────────────────────────────────┘
              ↓ calls
┌─────────────────────────────────────────┐
│       External Services                 │  ← Qdrant, APIs, Git
└─────────────────────────────────────────┘
```

**Dependency Rules**

**Rule 1: MCP Tools Layer**
- May import from Business Logic Layer
- May import from Infrastructure Layer for direct integrations (e.g., Qdrant client for status queries)
- May NOT import from other MCP tools (no cross-tool dependencies)
- May NOT contain business logic (only request/response handling)

**Rule 2: Business Logic Layer**
- May import from Infrastructure Layer
- May import from other Business Logic modules in the same layer
- May NOT import from MCP Tools Layer
- May NOT import from External Services directly (must go through Infrastructure Layer)

**Rule 3: Infrastructure Layer**
- May import from External Services (Qdrant, embedding APIs, Git)
- May import from other Infrastructure modules
- May NOT import from Business Logic Layer
- May NOT import from MCP Tools Layer

**Rule 4: External Services**
- Third-party libraries only (qdrant-client, GitPython, anthropic, etc.)
- No imports from project code

**Enforcement**
These rules prevent circular dependencies and keep the core domain logic independent of MCP and HTTP concerns. If a Business Logic module needs to call an MCP tool, that is a design error — the logic should be extracted into a shared module. If an Infrastructure module needs business logic, that logic should be moved to the Business Logic Layer and called from there.
