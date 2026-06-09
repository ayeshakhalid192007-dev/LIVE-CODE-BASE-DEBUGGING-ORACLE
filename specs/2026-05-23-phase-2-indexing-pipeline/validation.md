# Phase 2 Indexing Pipeline - Validation Checklist

## Test Cases

### TC1: Git Repository Reader
```bash
uv run pytest tests/unit/test_repo_reader.py -v
```
**Expected:** All tests pass, repo validation works, file extraction works, commit metadata extracted

### TC2: Commit Tracker
```bash
uv run pytest tests/unit/test_commit_tracker.py -v
```
**Expected:** Multi-branch tracking works, last commit stored/retrieved per branch

### TC3: File Filter
```bash
uv run pytest tests/unit/test_file_filter.py -v
```
**Expected:** Only .py files accepted, large files rejected, binary files rejected, gitignore respected

### TC4: AST Chunker
```bash
uv run pytest tests/unit/test_chunker.py -v
```
**Expected:** Functions chunked correctly, large functions kept whole, overlap applied, parsing errors handled

### TC5: Metadata Extraction
```bash
uv run pytest tests/unit/test_metadata.py -v
```
**Expected:** All CodeChunk fields populated, chunk_id deterministic, function names extracted

### TC6: Embedding Clients
```bash
uv run pytest tests/unit/test_voyage_client.py tests/unit/test_openai_client.py -v
```
**Expected:** Batch embedding works (mocked), retry logic works, API errors handled

### TC7: Batch Processor
```bash
uv run pytest tests/unit/test_batch_processor.py -v
```
**Expected:** Chunks batched into groups of 100, embeddings attached, progress logged

### TC8: Qdrant Collection Management
```bash
uv run pytest tests/unit/test_qdrant_collection.py -v
```
**Expected:** Collection created automatically, chunks upserted, retry logic works

### TC9: Indexing Pipeline Integration
```bash
uv run pytest tests/integration/test_indexing_pipeline.py -v
```
**Expected:** 
- Test repo indexed successfully
- Chunks in Qdrant with all metadata fields
- Chunk count matches expected value
- Progress logging visible
- Memory usage < 2GB

### TC10: MCP Tools
```bash
uv run pytest tests/unit/test_mcp_index_repo.py tests/unit/test_mcp_get_index_status.py -v
```
**Expected:** Tools callable, input validation works, output structured correctly

### TC11: Type Checking
```bash
uv run mypy src/git_debug_oracle/
```
**Expected:** No type errors, strict mode passes

### TC12: Full Test Suite
```bash
uv run pytest
```
**Expected:** All tests pass, coverage > 80%

### TC13: Pre-commit Hooks
```bash
pre-commit run --all-files
```
**Expected:** Ruff and mypy pass, no formatting issues

### TC14: Real Repository Indexing
```bash
# Start Qdrant
docker compose up -d

# Set environment variables
export QDRANT_HOST=localhost
export EMBEDDING_API_KEY=your_key
export ANTHROPIC_API_KEY=your_key
export REPO_PATH=/path/to/this/repo

# Run MCP server and call index_repo tool
uv run python -m git_debug_oracle.server
```
**Expected:**
- Server starts without errors
- index_repo tool callable
- Repository indexed successfully
- Chunks visible in Qdrant

### TC15: Incremental Indexing
```bash
# Make a commit in test repo
cd /path/to/test/repo
echo "# New function" >> test.py
git add test.py
git commit -m "Add new function"

# Call index_incremental tool
# Verify only test.py re-indexed
```
**Expected:**
- Only changed file re-indexed
- Old chunks for test.py deleted
- New chunks inserted
- Other files untouched

### TC16: Performance Benchmark
```bash
# Create test file with 1000 lines
python -c "
for i in range(100):
    print(f'def func_{i}():')
    print(f'    return {i}')
    print()
" > test_1000_lines.py

# Measure indexing time (excluding embedding API)
time uv run python -c "
from git_debug_oracle.indexer.chunker import chunk_file
from git_debug_oracle.indexer.metadata import extract_chunk_metadata
with open('test_1000_lines.py') as f:
    content = f.read()
chunks = chunk_file('test_1000_lines.py', content, 1000, 200)
"
```
**Expected:** Completes in < 2 seconds

### TC17: Memory Usage
```bash
# Monitor memory during indexing
uv run python -c "
import tracemalloc
tracemalloc.start()
# Run indexing pipeline
# ...
current, peak = tracemalloc.get_traced_memory()
print(f'Peak memory: {peak / 1024 / 1024:.2f} MB')
tracemalloc.stop()
"
```
**Expected:** Peak memory < 2048 MB

### TC18: Multi-Branch Support
```bash
# Index main branch
# Index feature branch
# Verify both tracked separately in commit_tracker
```
**Expected:** Each branch has separate last_indexed_commit

### TC19: Commit Range Indexing
```bash
# Call index_repo with commit_range parameter
# Verify all commits in range indexed
```
**Expected:** All commits between start and end indexed

### TC20: Error Handling
```bash
# Test with invalid Python file (syntax error)
# Verify indexing stops with clear error message
```
**Expected:** Operation fails, error logged with file path and reason

## Exit Conditions (from roadmap.md)

### EC1: index_repo Completes Successfully
- [ ] Calling `index_repo` on a real repository completes without errors
- [ ] Returns structured output with chunks_indexed, files_processed, duration
- [ ] Logs progress during operation

### EC2: Qdrant Contains Correct Data
- [ ] Qdrant collection created automatically
- [ ] Chunks contain all metadata fields:
  - content (str)
  - file_path (str)
  - start_line (int)
  - end_line (int)
  - commit_hash (str)
  - commit_author (str)
  - commit_timestamp (datetime)
  - function_name (Optional[str])
  - embedding (list[float])
  - chunk_id (str)
- [ ] All fields have correct values (not None/empty)

### EC3: Incremental Indexing Works
- [ ] After new commit, calling index_incremental indexes only changed files
- [ ] Old chunks for modified files deleted
- [ ] New chunks for modified files inserted
- [ ] Unchanged files not re-indexed

### EC4: Performance Target Met
- [ ] Indexing 1000 lines of code completes in under 2 seconds
- [ ] Measurement excludes embedding API latency
- [ ] Measurement includes: file reading, parsing, chunking, metadata extraction

### EC5: All Unit Tests Pass
- [ ] test_repo_reader.py passes
- [ ] test_commit_tracker.py passes
- [ ] test_file_filter.py passes
- [ ] test_chunker.py passes
- [ ] test_metadata.py passes
- [ ] test_voyage_client.py passes
- [ ] test_openai_client.py passes
- [ ] test_batch_processor.py passes
- [ ] test_qdrant_collection.py passes
- [ ] test_mcp_index_repo.py passes
- [ ] test_mcp_get_index_status.py passes

### EC6: Integration Test Passes
- [ ] test_indexing_pipeline.py passes
- [ ] Test repo indexed successfully
- [ ] Chunk count matches expected value (within ±5% tolerance)
- [ ] All metadata fields verified

### EC7: Type Checking Passes
- [ ] mypy reports no errors on src/git_debug_oracle/
- [ ] All new code fully type-annotated
- [ ] Strict mode enabled

### EC8: Memory Usage Within Limits
- [ ] Peak memory usage < 2GB during indexing
- [ ] Memory monitoring implemented in pipeline
- [ ] Garbage collection triggered if approaching limit

## Acceptance Criteria

All test cases (TC1-TC20) must pass.
All exit conditions (EC1-EC8) must be satisfied.
Code review must pass with no blocking issues.
README.md updated with Phase 2 usage instructions.

## Ready for Merge Checklist

- [ ] All tests pass locally
- [ ] All tests pass in CI/CD (GitHub Actions)
- [ ] mypy passes with no errors
- [ ] pre-commit hooks pass
- [ ] Code review completed
- [ ] README.md updated
- [ ] All exit conditions verified
- [ ] Performance benchmarks met
- [ ] Memory limits enforced
- [ ] Multi-branch support verified
- [ ] Commit range indexing verified
- [ ] Error handling verified
