# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-06-13

### Added

#### Phase 1: Foundation
- MCP server skeleton with configuration loading via pydantic-settings
- Qdrant client initialization with health check on startup
- structlog configuration for development and production logging modes
- Docker Compose file for Qdrant vector database management
- Pre-commit hooks configured for ruff linting and mypy type checking
- Configuration validation with fail-fast error messages for missing required fields
- Basic MCP server registration with health check tool
- README with installation instructions and environment setup

#### Phase 2: Indexing Pipeline
- Full repository indexing pipeline: Git reader → Code chunker → Embedder → Qdrant storage
- Function-level code chunking with configurable overlap (default 1000 chars, 200 char overlap)
- File type filtering to skip binary files, images, and non-code files
- Chunk metadata extraction: commit hash, author, timestamp, file path, line range, function name
- Embedding generation with support for Voyage AI (voyage-code-2) and OpenAI (text-embedding-3-small)
- Batch embedding processing for efficient API usage
- Qdrant collection upserter with automatic collection creation
- Incremental indexing that only processes changed files since last indexed commit
- MCP tools: `index_repo` (full), `index_incremental` (changed files only)
- Progress logging with chunk count and duration metrics
- Unit tests for chunker, file filter, metadata extraction (97% coverage on chunker)
- Integration tests verifying chunk storage and retrieval from Qdrant

#### Phase 3: Retrieval & Error Ingestion
- FastAPI webhook endpoint at POST /webhook/error for error payload ingestion
- Webhook authentication via WEBHOOK_SECRET header validation
- Error payload parser extracting: file path, line number, function name, error type, message
- Multi-language stacktrace parser: Python, JavaScript, Java, Go
- Query constructor building vector search queries from error metadata
- Qdrant retriever performing vector search with metadata filtering
- Recency weighting algorithm boosting scores for chunks from recent commits (configurable window, default 30 days)
- Git diff retriever fetching diffs for commits containing top retrieval results
- MCP tools: `debug_error`, `search_codebase`, `get_recent_diffs`
- Retrieval result formatter structuring output with file paths, line ranges, commit info
- Unit tests for error parsing, query construction, recency weighting (89% average)
- Integration tests validating end-to-end error ingestion and retrieval pipeline

#### Phase 4: Fix Generation & MCP Contracts
- Claude API client with prompt caching enabled for reduced latency on repeated queries
- Context assembler combining retrieval results, diffs, and error info into structured Claude prompts
- Fix proposal parser extracting root cause, affected file, code patch, confidence from Claude response
- Enhanced `debug_error` MCP tool returning FixProposal with root cause analysis
- MCP tool `get_index_status` returning indexing state, last indexed commit, chunk count
- Structured output schemas for all MCP tools using Pydantic V2 models
- Error handling for Claude API failures with retry logic and fallback messages
- Confidence scoring based on retrieval result scores and Claude response certainty markers
- Unit tests for context assembly and fix proposal parsing (89% and 58% coverage)
- Integration tests generating fixes for known bugs and verifying fix structure
- Comprehensive MCP tool contracts with input/output examples

#### Phase 5: OSS Hardening
- **Docker Distribution:**
  - Multi-stage Dockerfile with separate build and runtime stages
  - Build stage: installs dependencies, runs full test suite to verify image validity
  - Runtime stage: minimal Python 3.11-slim base image with only runtime dependencies
  - Health checks: TCP port validation every 10 seconds with 5 second timeout, 3 retries
  - Security: runs as non-root user (oracle:1000)
  - Size optimization: <500MB target via multi-stage build and minimal base image
  - Labels: version, description, maintainer
  - Exposes port 8000 for MCP server

- **Docker Compose Orchestration:**
  - Two services: mcp-server and qdrant with proper networking
  - MCP server service with environment variable injection, health checks, auto-restart
  - Qdrant service with volume mounts for persistence, health checks, auto-restart
  - Custom bridge network named git-debug-oracle
  - Environment file support via .env.compose

- **GitHub Actions CI/CD Pipeline:**
  - Workflow triggers on push to main and pull requests to main
  - Four parallel jobs: lint (ruff), type-check (mypy), tests (pytest), docker-build
  - Lint job validates code style, naming conventions, imports with ruff
  - Type check job validates type annotations with mypy strict mode
  - Tests job runs full test suite with coverage reporting and >80% threshold enforcement
  - Docker build job verifies image builds successfully without pushing to registry
  - All jobs must pass before merge to main
  - Automatic failure notifications

- **Configuration Validation Enhancement:**
  - Specific, actionable error messages for each missing or invalid field
  - Validation at server startup (fail-fast principle)
  - Type checking for all configuration values
  - Range validation for numeric fields (e.g., port 1-65535)
  - File path existence checking for REPO_PATH
  - Error messages include: what's missing, why it matters, how to fix, where to get the value

- **Edge Case Handling:**
  - Empty repository: Clear error message with graceful exit (exit code 1)
  - Unsupported file types: Skip with DEBUG log, continue indexing
  - Invalid Python files: Skip with WARN log, indexing continues
  - Qdrant connection failures: Retry with exponential backoff (1s, 2s, 4s, 8s, max 5 attempts)
  - Embedding API unavailable: Retry up to 3 times with backoff, clear error on failure
  - Claude API rate limited (429): Return FixProposal with 0.3 confidence, no automatic retries
  - All edge cases handled without crashes

- **Retry Logic with Exponential Backoff:**
  - Transient error detection (timeout, network unreachable, 5xx errors)
  - Permanent error detection (invalid auth, schema mismatch)
  - Exponential backoff: 1s, 2s, 4s, 8s with ±20% random jitter
  - Maximum 5 retry attempts before failure
  - Detailed logging of each retry attempt with attempt number and wait duration

- **Graceful Degradation:**
  - Embedding API unavailable: Skip indexing with clear error message
  - Claude API unavailable: Continue with retrieval results only, return FixProposal with low confidence (0.3)
  - Retrieval continues even if fix generation fails
  - User always informed of partial/degraded state

- **Comprehensive Documentation:**
  - Enhanced README with quickstart guide (<5 minutes setup), installation methods, architecture overview, features, usage examples, troubleshooting
  - docs/QUICKSTART.md: Step-by-step setup guide with prerequisites and common issues
  - docs/CONFIGURATION.md: All environment variables with type, required/optional, defaults, examples, API key links
  - docs/ERROR_PAYLOADS.md: Example error payloads for Sentry, Datadog, CloudWatch, webhook endpoint specification
  - docs/MCP_CONFIG.md: Claude Desktop and Claude Code configuration with verification steps
  - docs/TROUBLESHOOTING.md: Common issues (connection errors, timeouts, invalid config) with diagnosis and solutions
  - CONTRIBUTING.md: Development setup, running tests, Git workflow, code standards, adding new features
  - LICENSE: MIT license with proper attribution

- **Release Preparation:**
  - Version tagged as v1.0.0 (semantic versioning)
  - CHANGELOG.md documenting all changes per phase
  - GitHub Actions workflow ensures quality on every push/PR
  - All tests passing (337 unit + integration tests)
  - Code coverage > 80%
  - Docker image verified to build and run
  - No breaking changes in v1.0.0 (forward compatible)

### Changed

- Upgraded project for public release: all edge cases handled, error messages actionable, documentation complete
- Docker image now validated in CI/CD pipeline on every commit
- MCP tool schemas now use Pydantic V2 with ConfigDict for forward compatibility
- Logging enhanced with structured context on all major operations

### Fixed

- Pydantic V1 deprecation warnings migrated to V2 style validators and config
- All code review issues from Phase 4 resolved
- Test failures in Phase 4 test suite resolved (3 fixed)
- Type annotation coverage improved to 100% on critical modules

### Removed

- N/A (v1.0.0 is initial release)

---

## [Unreleased]

### Planned for Phase 6
- Advanced monitoring and APM integration (Prometheus, Grafana)
- Multi-language client libraries (Python, JavaScript, Go)
- Helm charts for Kubernetes deployment
- Cloud platform-specific deployment guides (AWS, GCP, Azure)
- Web UI/Dashboard for browsing indexed code and search results
- Mobile client support
- Real-time code analysis and linting integration
- Additional VCS support (Mercurial, SVN, Perforce, Fossil)

---

## Versioning

Starting with v1.0.0, this project uses [Semantic Versioning](https://semver.org/):
- MAJOR version for breaking changes
- MINOR version for new backward-compatible functionality
- PATCH version for backward-compatible bug fixes

## Contributors

- **Phases 1-5 Implementation:** Claude (Anthropic AI)
- **Project Vision & Specifications:** Ayesha Khalid
- **Reference:** Project Constitution (CLAUDE.md) governs all development decisions
