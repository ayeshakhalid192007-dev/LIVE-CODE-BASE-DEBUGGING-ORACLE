# Roadmap

## Phase 1 — Foundation

**Goal:** Establish runnable project skeleton with configuration loading, Qdrant connection, and basic MCP server registration.

**Entry Condition:** Empty repository or project directory exists.

**Deliverables:**
- Project directory structure created with src/, tests/, docker/, docs/ folders
- pyproject.toml with all runtime and dev dependencies pinned
- pydantic-settings based configuration loader that reads .env file
- Configuration validation that fails fast with clear error messages for missing required fields
- Qdrant client initialization with connection test on startup
- Basic MCP server that registers with MCP SDK and responds to a health check tool
- structlog configuration for development and production modes
- Docker Compose file that starts Qdrant container with correct ports and volumes
- .env.example file documenting all environment variables
- Pre-commit hooks configured for ruff and mypy
- README with installation instructions and environment setup

**Exit Condition:**
- Running `docker-compose up` starts Qdrant successfully
- Running `python -m git_debug_oracle.server` starts MCP server without errors
- MCP server appears in Claude Code tool list when registered in config
- Calling health check tool returns success response
- All configuration validation tests pass
- mypy reports no type errors

**Estimated Complexity:** Low

---

## Phase 2 — Indexing Pipeline

**Goal:** Implement full repository indexing with Git file reading, function-level chunking, embedding generation, and Qdrant upsert.

**Entry Condition:** Phase 1 complete, MCP server runs and connects to Qdrant.

**Deliverables:**
- Git repository reader that extracts files from a specific commit
- File type filter that skips binary files, images, and non-code files
- Function-level code chunker that splits files into logical units with overlap
- Chunk metadata extractor that captures commit hash, author, timestamp, file path, line range
- Embedding generator that batches chunks and calls embedding API (Voyage or OpenAI)
- Qdrant upserter that creates collection if missing and inserts chunks with metadata
- MCP tool `index_repo` that triggers full repository indexing for a given commit
- Incremental indexing logic that compares current HEAD to last indexed commit
- MCP tool `index_incremental` that indexes only changed files since last index
- Progress logging for indexing operations with chunk count and duration
- Unit tests for chunker, metadata extractor, and file filter
- Integration test that indexes a small test repository and verifies chunks in Qdrant

**Exit Condition:**
- Calling `index_repo` on a real repository completes without errors
- Qdrant collection contains chunks with correct metadata fields
- Calling `index_incremental` after a new commit indexes only changed files
- Indexing 1000 lines of code completes in under 2 seconds
- All unit tests pass
- Integration test verifies chunk count matches expected value

**Estimated Complexity:** High

---

## Phase 3 — Retrieval and Error Ingestion

**Goal:** Accept error payloads via webhook, parse stacktraces, construct retrieval queries, and return relevant code chunks with commit context.

**Entry Condition:** Phase 2 complete, repository is indexed in Qdrant.

**Deliverables:**
- FastAPI webhook endpoint at POST /webhook/error that accepts JSON error payloads
- Webhook authentication using WEBHOOK_SECRET header validation
- Error payload parser that extracts file path, line number, function name, error type, and message
- Stacktrace parser that handles Python, JavaScript, Java, and Go stacktrace formats
- Query constructor that builds vector search query from error metadata
- Qdrant retriever that performs vector search with metadata filtering
- Recency weighting algorithm that boosts scores for chunks from recent commits
- Git diff retriever that fetches diffs for commits containing top results
- MCP tool `debug_error` that accepts error payload and returns retrieval results
- MCP tool `search_codebase` that performs arbitrary vector search over indexed code
- MCP tool `get_recent_diffs` that returns diffs from last N commits
- Retrieval result formatter that structures output with file paths, line ranges, and commit info
- Unit tests for error parser, query constructor, and recency weighting
- Integration test that sends error payload and verifies correct chunks are retrieved

**Exit Condition:**
- Webhook endpoint accepts error payloads and returns 200 status
- Calling `debug_error` with a known error returns correct file in top 3 results
- Retrieval completes in under 500ms from query to results
- Recency weighting correctly ranks recent commits higher than old ones
- All stacktrace format parsers handle valid input without errors
- Integration test achieves 90%+ top-3 hit rate on test error set

**Estimated Complexity:** High

---

## Phase 4 — Fix Generation and MCP Tool Contracts

**Goal:** Integrate Claude API to generate fix proposals with root cause analysis, finalize all MCP tool contracts, and stabilize tool schemas.

**Entry Condition:** Phase 3 complete, retrieval returns relevant code chunks for errors.

**Deliverables:**
- Context assembler that combines retrieval results, diffs, and error info into Claude prompt
- Claude API client that sends fix generation request with prompt caching enabled
- Fix proposal parser that extracts root cause, affected file, code patch, and confidence from Claude response
- MCP tool `debug_error` enhanced to return FixProposal instead of raw retrieval results
- MCP tool `get_index_status` that returns indexing state, last indexed commit, and chunk count
- Structured output schemas for all MCP tools using Pydantic models
- Error handling for Claude API failures with retry logic and fallback messages
- Confidence scoring based on retrieval result scores and Claude response certainty markers
- Unit tests for context assembler and fix proposal parser
- Integration test that generates fix for known bug and verifies fix structure
- Documentation for all MCP tool contracts with input/output examples

**Exit Condition:**
- Calling `debug_error` returns FixProposal with all required fields populated
- Fix proposals include root cause analysis in at least 80% of test cases
- Claude API calls use prompt caching to reduce latency on repeated queries
- All MCP tools have stable schemas that will not change in v1
- Error-to-fix workflow completes in under 30 seconds end-to-end
- Integration test verifies fix proposal quality on 10 known bugs

**Estimated Complexity:** Medium

---

## Phase 5 — OSS Hardening

**Goal:** Prepare project for public release with Docker distribution, comprehensive documentation, robust error handling, and edge case coverage.

**Entry Condition:** Phase 4 complete, all core functionality works in happy path scenarios.

**Deliverables:**
- Docker image build for MCP server with multi-stage build for minimal size
- Docker Compose configuration that bundles MCP server and Qdrant with health checks
- README with quickstart guide, architecture diagram, and troubleshooting section
- Configuration validation with specific error messages for each missing or invalid field
- Edge case handling for empty repositories, repositories with no commits, and unsupported file types
- Qdrant connection retry logic with exponential backoff
- Graceful degradation when embedding API is unavailable
- Graceful degradation when Claude API is unavailable
- Log level adjustment documentation for debugging issues
- Example error payloads for common monitoring systems (Sentry, Datadog, CloudWatch)
- MCP config examples for Claude Desktop and Claude Code
- Contributing guide with development setup instructions
- License file (MIT or Apache 2.0)
- GitHub Actions CI workflow that runs tests, linting, and type checking
- Release preparation: version tagging, changelog, and Docker image publishing

**Exit Condition:**
- Following README quickstart, a new user can index a repo in under 5 minutes
- Docker Compose setup works on macOS, Linux, and Windows
- All edge cases are handled without crashes or unclear error messages
- CI pipeline passes on main branch
- Project is ready for public GitHub release
- At least 3 external users successfully install and run the project

**Estimated Complexity:** Medium
