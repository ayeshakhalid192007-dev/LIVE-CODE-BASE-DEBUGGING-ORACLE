# Phase 2 Indexing Pipeline - Implementation Plan

## Goal
Implement full repository indexing with Git file reading, function-level chunking using Python AST, embedding generation, and Qdrant upsert with multi-branch support.

## Task Groups

### Task Group 1: Domain Types and Git Repository Reader

**Deliverables:**
1. Create domain types in src/git_debug_oracle/types.py (CodeChunk, IndexStatus, CommitDiff)
2. Implement git_watcher/repo_reader.py with GitPython
3. Implement git_watcher/commit_tracker.py for multi-branch tracking
4. Unit tests for repo_reader and commit_tracker

**Steps:**
1. Create src/git_debug_oracle/types.py with dataclasses from architecture.md
2. Implement repo_reader.py:
   - extract_files_from_commit(repo_path, commit_hash) -> list[tuple[str, str]]
   - get_commit_metadata(repo_path, commit_hash) -> dict
   - get_changed_files(repo_path, start_commit, end_commit) -> list[str]
   - get_commits_in_range(repo_path, start_commit, end_commit) -> list[str]
   - validate_repo(repo_path) -> bool
3. Implement commit_tracker.py:
   - get_last_indexed_commit(branch) -> str | None
   - set_last_indexed_commit(branch, commit_hash, timestamp) -> None
   - get_all_tracked_branches() -> list[str]
   - Uses Qdrant metadata collection for storage
4. Write tests/unit/test_repo_reader.py
5. Write tests/unit/test_commit_tracker.py
6. Run tests locally: uv run pytest tests/unit/test_repo_reader.py tests/unit/test_commit_tracker.py

**Exit Criteria:**
- All functions type-annotated
- Tests pass locally
- mypy passes on git_watcher/

---

### Task Group 2: File Filtering

**Deliverables:**
1. Implement indexer/file_filter.py
2. Unit tests for file_filter

**Steps:**
1. Implement file_filter.py:
   - should_index_file(file_path, file_content) -> bool
   - Check extension is .py
   - Check file size < 1MB
   - Check not binary (no null bytes)
   - get_gitignore_patterns(repo_path) -> list[str]
   - matches_gitignore(file_path, patterns) -> bool
2. Write tests/unit/test_file_filter.py:
   - Test .py files accepted
   - Test non-.py files rejected
   - Test large files rejected
   - Test binary files rejected
   - Test gitignore patterns respected
3. Run tests locally: uv run pytest tests/unit/test_file_filter.py

**Exit Criteria:**
- All functions type-annotated
- Tests pass locally
- mypy passes on indexer/file_filter.py

---

### Task Group 3: AST-Based Chunker

**Deliverables:**
1. Implement indexer/chunker.py using Python ast module
2. Unit tests for chunker

**Steps:**
1. Implement chunker.py:
   - parse_python_file(content) -> ast.Module | None
   - extract_functions(ast_tree) -> list[FunctionDef]
   - chunk_function(func_node, source_lines, chunk_size, overlap) -> list[dict]
   - chunk_file(file_path, content, chunk_size, overlap) -> list[dict]
   - Handle parsing errors: return error dict with file_path and error message
   - If function > chunk_size, keep as single chunk
   - Apply overlap between adjacent chunks
2. Write tests/unit/test_chunker.py:
   - Test simple function chunking
   - Test class method chunking
   - Test large function kept as single chunk
   - Test chunk overlap applied correctly
   - Test parsing error handling
   - Test empty file handling
3. Run tests locally: uv run pytest tests/unit/test_chunker.py

**Exit Criteria:**
- All functions type-annotated
- Tests pass locally
- mypy passes on indexer/chunker.py
- Chunker handles parsing errors gracefully

---

### Task Group 4: Metadata Extraction

**Deliverables:**
1. Implement indexer/metadata.py
2. Unit tests for metadata extractor

**Steps:**
1. Implement metadata.py:
   - extract_chunk_metadata(chunk_dict, file_path, commit_metadata) -> CodeChunk
   - generate_chunk_id(file_path, start_line, end_line, commit_hash) -> str
   - Use hashlib.sha256 for deterministic chunk_id
   - Populate all CodeChunk fields
2. Write tests/unit/test_metadata.py:
   - Test chunk_id generation is deterministic
   - Test all fields populated correctly
   - Test function_name extraction from AST
3. Run tests locally: uv run pytest tests/unit/test_metadata.py

**Exit Criteria:**
- All functions type-annotated
- Tests pass locally
- mypy passes on indexer/metadata.py

---

### Task Group 5: Embedding Generation

**Deliverables:**
1. Implement embedder/voyage_client.py
2. Implement embedder/openai_client.py
3. Implement embedder/batch_processor.py
4. Unit tests for embedding clients (mocked)

**Steps:**
1. Implement voyage_client.py:
   - VoyageEmbedder class
   - embed_batch(texts: list[str]) -> list[list[float]]
   - Use voyageai SDK
   - Handle API errors with retry logic (3 retries, exponential backoff)
2. Implement openai_client.py:
   - OpenAIEmbedder class
   - embed_batch(texts: list[str]) -> list[list[float]]
   - Use openai SDK
   - Handle API errors with retry logic
3. Implement batch_processor.py:
   - batch_embed(chunks: list[CodeChunk], embedder) -> list[CodeChunk]
   - Split chunks into batches of 100
   - Call embedder.embed_batch() for each batch
   - Attach embeddings to CodeChunk objects
   - Log progress every batch
4. Write tests/unit/test_voyage_client.py (mock API calls)
5. Write tests/unit/test_openai_client.py (mock API calls)
6. Write tests/unit/test_batch_processor.py
7. Run tests locally

**Exit Criteria:**
- All functions type-annotated
- Tests pass locally with mocked API calls
- mypy passes on embedder/

---

### Task Group 6: Qdrant Collection Management

**Deliverables:**
1. Extend utils/qdrant_client.py with collection management
2. Unit tests for collection operations (mocked)

**Steps:**
1. Extend qdrant_client.py:
   - create_collection_if_missing(collection_name, vector_dim=1536) -> None
   - Use HNSW index with m=16, ef_construct=100
   - delete_chunks_by_file(file_path, commit_hash) -> None
   - upsert_chunks(chunks: list[CodeChunk]) -> None
   - Retry logic for upsert failures (3 retries, exponential backoff)
   - get_collection_info(collection_name) -> dict
2. Write tests/unit/test_qdrant_collection.py
3. Run tests locally

**Exit Criteria:**
- All functions type-annotated
- Tests pass locally
- mypy passes on utils/qdrant_client.py

---

### Task Group 7: Indexing Pipeline Orchestration

**Deliverables:**
1. Implement indexer/pipeline.py
2. Integration test for full pipeline

**Steps:**
1. Implement pipeline.py:
   - IndexingPipeline class
   - index_commit(repo_path, commit_hash, branch, force_full) -> IndexStatus
   - index_commit_range(repo_path, start_commit, end_commit, branch) -> IndexStatus
   - Steps: validate repo → get files → filter → chunk → metadata → embed → upsert
   - Progress logging every 10 files and 100 chunks
   - Estimate time remaining based on average time per file
   - Memory monitoring: check memory usage, pause if > 2GB
   - Error handling: stop on first file parsing error
2. Write tests/integration/test_indexing_pipeline.py:
   - Create small test repo with 5 Python files
   - Index repo
   - Verify chunks in Qdrant
   - Verify all metadata fields present
   - Verify chunk count matches expected
3. Run tests locally: uv run pytest tests/integration/test_indexing_pipeline.py

**Exit Criteria:**
- Pipeline orchestrates all steps correctly
- Progress logging works
- Memory monitoring works
- Integration test passes locally

---

### Task Group 8: MCP Tools

**Deliverables:**
1. Implement mcp_tools/index_repo.py
2. Implement mcp_tools/get_index_status.py
3. Register tools in server.py
4. Unit tests for MCP tools

**Steps:**
1. Implement index_repo.py:
   - Tool name: "index_repo"
   - Input schema: repo_path, commit_hash, branch, force_full, commit_range
   - Call IndexingPipeline.index_commit() or index_commit_range()
   - Return structured output with status, chunks_indexed, files_processed, duration
   - Handle errors and return error_message
2. Implement get_index_status.py:
   - Tool name: "get_index_status"
   - Input schema: repo_path, branch
   - Query commit_tracker for last indexed commit
   - Query Qdrant for total chunks and files
   - Return IndexStatus
3. Update server.py:
   - Import and register index_repo tool
   - Import and register get_index_status tool
   - Add to list_tools() and call_tool()
4. Write tests/unit/test_mcp_index_repo.py
5. Write tests/unit/test_mcp_get_index_status.py
6. Run tests locally

**Exit Criteria:**
- Tools registered in MCP server
- Tools callable via MCP protocol
- Tests pass locally
- mypy passes on mcp_tools/

---

### Task Group 9: End-to-End Validation

**Deliverables:**
1. Run all tests locally
2. Verify exit conditions from roadmap.md
3. Update README.md with Phase 2 usage instructions

**Steps:**
1. Run full test suite: uv run pytest
2. Run mypy: uv run mypy src/
3. Verify exit conditions:
   - Index a real repository (this repo)
   - Verify chunks in Qdrant with all fields
   - Make a commit, run index_incremental, verify only new files indexed
   - Measure indexing speed: 1000 lines in <2 seconds (excluding API)
4. Update README.md:
   - Add Quickstart section with index_repo example
   - Document MCP tools
5. Run pre-commit hooks: pre-commit run --all-files

**Exit Criteria:**
- All tests pass locally
- All exit conditions met
- README updated
- Ready for code review and merge

## Implementation Order

Execute task groups sequentially: 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9

Each task group must be complete and tested before moving to next.
