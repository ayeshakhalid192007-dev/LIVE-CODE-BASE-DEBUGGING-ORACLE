# Phase 2 Indexing Pipeline - Requirements

## Functional Requirements

### FR1: Git Repository Reader
- Extract files from specific commits using GitPython
- Support reading from any commit hash or branch HEAD
- Support reading commit ranges (e.g., "commit A to commit B")
- Extract commit metadata: hash, author, timestamp, message
- Handle merge commits correctly
- Support multiple branches simultaneously

### FR2: File Type Filter
- Index only Python files (.py extension)
- Skip binary files, images, and non-code files
- Skip files larger than 1MB
- Respect .gitignore patterns when indexing
- Log skipped files with reason

### FR3: Function-Level Code Chunker
- Use Python's ast module to parse Python files
- Identify function and class boundaries via AST
- Split code into logical units (functions, methods, classes)
- Apply CHUNK_SIZE limit (default: 1000 characters)
- Apply CHUNK_OVERLAP (default: 200 characters) between adjacent chunks
- When function exceeds CHUNK_SIZE, keep as one large chunk (do not split mid-function)
- Preserve indentation and syntax validity in chunks
- Handle parsing errors gracefully

### FR4: Chunk Metadata Extractor
- Extract for each chunk:
  - content: str (the code text)
  - file_path: str (relative to repo root)
  - start_line: int
  - end_line: int
  - commit_hash: str
  - commit_author: str
  - commit_timestamp: datetime
  - function_name: Optional[str] (extracted from AST)
  - chunk_id: str (hash of file_path + line_range + commit_hash)
- Ensure all fields are populated correctly
- Generate deterministic chunk_id for deduplication

### FR5: Embedding Generator
- Batch chunks into groups of 100
- Call embedding API (Voyage AI or OpenAI) per batch
- Use embedding model from config (voyage-code-2 or text-embedding-3-small)
- Handle API failures: retry entire batch with exponential backoff
- Do not cache embeddings (always generate fresh)
- Log embedding generation progress

### FR6: Qdrant Upserter
- Create Qdrant collection automatically if missing
- Use vector dimension 1536 (for both voyage-code-2 and text-embedding-3-small)
- Use HNSW index with default parameters (m=16, ef_construct=100)
- Upsert chunks with embeddings and metadata
- Use chunk_id as point ID for idempotency
- Handle upsert failures: retry with exponential backoff
- Log upsert progress

### FR7: Incremental Indexing Logic
- Compare target commit to last indexed commit per branch
- Identify changed files between commits
- For modified files: delete old chunks and re-index entire file
- For deleted files: remove chunks from Qdrant
- For renamed files: delete old chunks and index new file
- Track last indexed commit per branch in Qdrant metadata

### FR8: Commit Tracking
- Store last indexed commit per branch in Qdrant metadata collection
- Support multiple branches simultaneously
- Metadata format: {branch_name: {last_commit: str, last_indexed_timestamp: datetime}}
- Create metadata collection automatically if missing

### FR9: Progress Logging
- Log progress every 10 files processed
- Log progress every 100 chunks generated
- Show estimated time remaining during long operations
- Log: files processed, chunks generated, embeddings created, chunks upserted
- Log duration for each major step (chunking, embedding, upsert)

### FR10: Error Handling
- If file parsing fails: stop, log error with file path and reason, fail operation
- If embedding API fails: retry batch 3 times with exponential backoff, then fail
- If Qdrant upsert fails: retry batch 3 times with exponential backoff, then fail
- All errors must include clear messages indicating what failed and why

### FR11: MCP Tool - index_repo
- Input: repo_path (optional, defaults to config), commit_hash (optional, defaults to HEAD), branch (optional, defaults to WATCH_BRANCH), force_full (bool, default False), commit_range (optional, tuple of start/end commits)
- Output: status, chunks_indexed, files_processed, last_commit, duration_seconds, error_message
- Behavior: If force_full=True, index entire repo. If False, incremental index. If commit_range provided, index all commits in range.
- Validate repo_path exists and is Git repo
- Validate commit_hash/branch exists

### FR12: MCP Tool - index_incremental
- Separate tool for incremental indexing
- Input: repo_path (optional), branch (optional)
- Output: same as index_repo
- Behavior: Always incremental, never full re-index

### FR13: Indexing Pipeline Orchestration
- Coordinate all steps: file extraction → filtering → chunking → metadata → embedding → upsert
- Run steps sequentially (not parallel) to control memory usage
- Enforce maximum memory usage: 2GB during indexing
- If memory exceeds limit, pause and wait for garbage collection

## Non-Functional Requirements

### NFR1: Performance
- Index 1000 lines of code in under 2 seconds (excluding embedding API latency)
- Embedding API latency not counted toward performance benchmark
- Memory usage must not exceed 2GB during indexing

### NFR2: Reliability
- All operations must be idempotent (re-running produces same result)
- Partial failures must not corrupt Qdrant state
- Retry logic must prevent transient failures from failing entire operation

### NFR3: Observability
- All major operations logged at INFO level
- Progress updates visible during long operations
- Errors logged at ERROR level with full context

### NFR4: Type Safety
- All functions fully type-annotated
- All domain types use dataclasses from architecture.md
- mypy strict mode passes with no errors

### NFR5: Test Coverage
- Unit tests for: chunker, file_filter, metadata extractor, commit tracker
- Integration test: index small test repo, verify chunks in Qdrant
- All tests run locally before CI/CD
- Tests must pass in GitHub Actions workflow

## Domain Types

Using types from specs/architecture.md:

```python
@dataclass
class CodeChunk:
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
class IndexStatus:
    repo_path: str
    branch: str
    last_indexed_commit: str
    last_indexed_timestamp: datetime
    total_chunks: int
    total_files: int
    collection_name: str
    is_indexing: bool
```

## Configuration

From specs/tech-stack.md, these environment variables are used:

- REPO_PATH: Absolute path to Git repository
- WATCH_BRANCH: Default branch to index (default: main)
- CHUNK_SIZE: Max characters per chunk (default: 1000)
- CHUNK_OVERLAP: Overlap between chunks (default: 200)
- EMBEDDING_MODEL: voyage-code-2 or text-embedding-3-small
- EMBEDDING_API_KEY: API key for embedding provider
- QDRANT_HOST: Qdrant server hostname
- QDRANT_PORT: Qdrant gRPC port (default: 6333)
- QDRANT_COLLECTION: Collection name (default: git_debug_oracle)

## Acceptance Criteria

- All FR1-FR13 implemented and tested
- All NFR1-NFR5 satisfied
- Exit conditions from roadmap.md met:
  - Calling `index_repo` on real repository completes without errors
  - Qdrant collection contains chunks with all metadata fields present
  - Calling `index_incremental` after new commit indexes only changed files
  - Indexing 1000 lines completes in under 2 seconds (excluding API latency)
  - All unit tests pass
  - Integration test verifies chunk count matches expected value
