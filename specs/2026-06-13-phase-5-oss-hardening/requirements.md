# Phase 5 OSS Hardening - Requirements

## Functional Requirements

### FR1: Docker Image Build

**Description:** Create a Docker image for the MCP server that is production-ready and minimal in size.

**Requirements:**
- Multi-stage Dockerfile with separate build and runtime stages
- Build stage: Install all dependencies, run tests to verify image validity
- Runtime stage: Only runtime dependencies, remove build artifacts
- Python 3.11+ base image (python:3.11-slim recommended)
- Image size: < 500MB
- Entrypoint: Starts MCP server on configurable port (default 8000)
- Labels: Include version, description, maintainer
- Build argument: PYTHON_VERSION for flexibility

**Acceptance Criteria:**
- `docker build -t git-debug-oracle:latest .` succeeds
- Image starts without errors: `docker run -p 8000:8000 git-debug-oracle:latest`
- Image size reported by `docker images` is < 500MB
- Container responds to health check on `/health` endpoint

---

### FR2: Docker Compose Orchestration

**Description:** Provide docker-compose.yml that starts MCP server and Qdrant together.

**Requirements:**
- Two services: `mcp-server` and `qdrant`
- MCP server service:
  - Image: git-debug-oracle:latest
  - Port: 8000 (configurable via .env)
  - Environment variables: QDRANT_HOST, EMBEDDING_API_KEY, ANTHROPIC_API_KEY
  - Health check: GET /health every 10s, 3 retries
  - Restart policy: unless-stopped
- Qdrant service:
  - Image: qdrant/qdrant:latest
  - Port: 6333 (configurable)
  - Volume: qdrant_storage for persistence
  - Health check: TCP port 6333
  - Restart policy: unless-stopped
- Network: Custom bridge network named `git-debug-oracle`
- Environment file: .env.compose for configuration
- Volumes: Named volume for Qdrant persistence

**Acceptance Criteria:**
- `docker-compose up` starts both services without errors
- Both services report healthy after 30 seconds
- `docker-compose logs` shows no ERROR level messages
- MCP server can communicate with Qdrant
- `docker-compose down` cleanly stops services

---

### FR3: README with Quickstart Guide

**Description:** Comprehensive README that enables new users to set up and use the project in < 5 minutes.

**Requirements:**
- Header: Project name, description, key features (1-2 paragraphs)
- Table of Contents: Sections numbered for navigation
- Quick Start (< 5 min):
  - Prerequisites: Docker, Docker Compose (or Python 3.11+)
  - Clone: `git clone ...`
  - Docker path: `docker-compose up`
  - Python path: `uv install && uv run python -m git_debug_oracle.server`
  - Verify: Call health check endpoint
  - First index: Example repo path
  - First error: Example error payload
- Installation: Multiple methods (Docker, pip, source)
- Architecture: High-level system diagram (ASCII or image)
- Features: List with brief descriptions
- Usage: Examples for each MCP tool
- Troubleshooting: Common issues and solutions
- Contributing: Link to CONTRIBUTING.md
- License: License type and link

**Acceptance Criteria:**
- README > 2000 words, < 6000 words (concise but complete)
- Quickstart section takes < 5 minutes to execute
- All commands in README are tested and work
- Table of Contents links work in GitHub
- Code examples are syntax-highlighted

---

### FR4: Configuration Validation with Error Messages

**Description:** Enhance configuration system with specific, actionable error messages for each missing or invalid field.

**Requirements:**
- Validation at startup (fail fast):
  - Check required environment variables presence
  - Check types (int, string, enum)
  - Check value ranges (e.g., port 1-65535)
  - Check file paths (if REPO_PATH provided)
- Error messages must include:
  - What is missing/invalid
  - Why it matters (one sentence)
  - How to fix it (exact env var name, example value)
- Example error for missing ANTHROPIC_API_KEY:
  ```
  Configuration Error: ANTHROPIC_API_KEY not set.
  This is required to generate fix proposals using Claude.
  Set it: export ANTHROPIC_API_KEY="sk-..."
  Get it: https://console.anthropic.com/account/keys
  ```
- Log level: ERROR for missing required fields
- Exit code: 1 on validation failure

**Acceptance Criteria:**
- Server refuses to start with missing ANTHROPIC_API_KEY
- Error message is actionable (user can immediately fix)
- Error mentions where to get the value (URL or instruction)
- All required fields validated at startup
- Optional fields with defaults validated for type/range

---

### FR5: Edge Case Handling

**Description:** Handle edge cases gracefully without crashes or unclear error messages.

**Requirements:**

#### Empty Repository
- Input: Repo with no commits
- Expected: Clear error message: "Repository has no commits. Please make at least one commit."
- Exit gracefully: No crash, exit code 1
- Log: WARN level message with repo path

#### Unsupported File Types
- Input: Binary files, images, .exe files
- Expected: Skip with DEBUG log, continue indexing other files
- Result: Index completes, only code files included
- No crash or error

#### Invalid Python Files
- Input: Python file with syntax errors
- Expected: Skip file with WARN log including filename
- Result: Other Python files indexed normally
- Fix generation still works if retrieval succeeds

#### Network Failures (Qdrant Unavailable)
- Input: Qdrant connection timeout
- Expected: Retry with exponential backoff (1s, 2s, 4s, max 3 retries)
- After max retries: Clear error: "Cannot connect to Qdrant at {host}:{port}. Check QDRANT_HOST and QDRANT_PORT."
- Log: ERROR level with full traceback

#### Embedding API Unavailable
- Input: Embedding API returns 503
- Expected: Graceful degradation, retry up to 3 times with backoff
- After retries: Skip indexing, return error: "Embedding service unavailable. Retried 3 times. Please try again later."
- Log: ERROR with API response code

#### Claude API Unavailable
- Input: Claude API returns rate limit (429)
- Expected: Do not retry automatically
- Return: FixProposal with low confidence (0.3) and explanation: "Claude API currently unavailable. Showing retrieval results only."
- Log: WARNING level (not ERROR)

**Acceptance Criteria:**
- All edge cases tested in test_edge_cases.py
- No crashes (no unhandled exceptions)
- All error messages clear and actionable
- Logging appropriate level (DEBUG, INFO, WARN, ERROR)
- Recovery graceful (service continues if possible)

---

### FR6: Qdrant Connection Retry Logic

**Description:** Implement exponential backoff retry logic for Qdrant connections.

**Requirements:**
- Retry on transient errors:
  - Connection timeout
  - Network unreachable
  - Service unavailable (5xx)
- Don't retry on permanent errors:
  - Invalid API key
  - Collection not found
  - Schema mismatch
- Backoff strategy: exponential
  - Attempt 1: immediate
  - Attempt 2: wait 1s
  - Attempt 3: wait 2s
  - Attempt 4: wait 4s
  - Attempt 5: wait 8s
  - Max 5 attempts, then fail
- Add jitter: ±20% random jitter to prevent thundering herd
- Log each attempt: "Qdrant connection attempt 2/5 after 1.2s wait"
- Final failure message: Actionable (see FR5)

**Acceptance Criteria:**
- Transient error followed by success: Succeeds after retry
- 5 consecutive failures: Clear error message, exit gracefully
- Logging shows all retry attempts
- Jitter prevents synchronized retries

---

### FR7: Graceful Degradation (Embedding API)

**Description:** Handle unavailable embedding API gracefully.

**Requirements:**
- Detection: Embedding API returns error on first request
- Degradation mode:
  - Log: "Embedding API unavailable, retrying..."
  - Retry up to 3 times with exponential backoff
  - After retries, skip indexing: "Cannot embed code chunks. Indexing halted."
- Clear messaging to user:
  - Don't index (maintain consistency)
  - Clear reason why
  - Suggestion: Check EMBEDDING_API_KEY and network connectivity

**Acceptance Criteria:**
- Embedding API error → Max 3 retries → Clear error message
- User knows exactly why indexing failed
- No partial/corrupted index

---

### FR8: Graceful Degradation (Claude API)

**Description:** Handle unavailable Claude API without blocking retrieval.

**Requirements:**
- Detection: Claude API returns error on fix generation request
- Degradation mode:
  - Continue with retrieval results only
  - FixProposal returned with:
    - root_cause: null
    - code_patch: null
    - confidence: 0.3 (low)
    - explanation: "Claude API currently unavailable. Showing retrieval results only."
  - No automatic retries (user decides)
- Clear messaging:
  - Status: "partial" (not "success", not "failed")
  - Retrieval results still provided
  - User can manually invoke fix generation later

**Acceptance Criteria:**
- Claude API unavailable → Fix generation skipped
- Retrieval results returned
- Low confidence indicates incomplete result
- User informed via explanation field

---

### FR9: GitHub Actions CI/CD Workflow

**Description:** Automated testing and validation on every push and PR.

**Requirements:**
- Trigger events:
  - Push to main
  - Push to any branch (optional)
  - Pull requests to main
- Jobs (parallel):
  - Lint (ruff): `ruff check src/ tests/`
  - Type check (mypy): `mypy src/ --strict`
  - Tests (pytest): `pytest tests/ -v --cov`
  - Docker build: `docker build -t git-debug-oracle:test .`
- Success criteria:
  - All jobs pass before merge
  - Coverage > 80%
  - No ruff or mypy errors
  - Docker builds successfully
- Notifications:
  - Failure: Comment on PR with details
  - Success: Green checkmark

**Acceptance Criteria:**
- Workflow file exists: `.github/workflows/ci.yml`
- All jobs run on push to main
- PR status checks show results
- Workflow can be viewed in GitHub Actions tab

---

### FR10: Documentation Files

**Description:** Comprehensive documentation for users and contributors.

**Requirements:**

**docs/QUICKSTART.md:**
- Step-by-step setup (5-10 minutes)
- Screenshots or screen recordings (optional)
- Prerequisites checklist
- Troubleshooting for common setup issues

**docs/CONFIGURATION.md:**
- All environment variables listed
- Type, required/optional, default, description
- Examples for each
- Links to get API keys (Anthropic, Voyage/OpenAI)

**docs/ERROR_PAYLOADS.md:**
- Example payloads for: Sentry, Datadog, CloudWatch
- Format, required fields, optional fields
- Webhook endpoint specification

**docs/MCP_CONFIG.md:**
- Claude Desktop configuration
- Claude Code configuration
- Verification steps after setup

**docs/TROUBLESHOOTING.md:**
- Common issues: Connection errors, timeout, invalid config
- Diagnosis steps for each
- Solution or escalation path

**CONTRIBUTING.md:**
- Development setup: clone, uv install, pre-commit
- Running tests locally
- Git workflow: branch names, commit messages, PR process
- Code standards from CLAUDE.md
- Adding new features: where to start

**LICENSE:**
- MIT or Apache 2.0 (user chooses)
- Full license text

**Acceptance Criteria:**
- All 7 documentation files created
- Each > 500 words except LICENSE
- All code examples tested
- Links are valid (tested after commit)

---

## Non-Functional Requirements

### NFR1: Performance
- Docker image build time: < 5 minutes
- Docker image startup: < 10 seconds
- No performance regression vs. Phase 4

### NFR2: Reliability
- No crashes on edge cases
- Graceful degradation without data loss
- Connection retry logic prevents cascading failures

### NFR3: Observability
- All errors logged with context
- All retries logged with attempt number
- Performance metrics in logs (duration, count)

### NFR4: Usability
- README and quickstart enable new user setup in < 5 minutes
- Error messages actionable (not generic)
- Documentation complete for all features

### NFR5: Maintainability
- CI/CD pipeline prevents regressions
- Code review process via GitHub PR
- Contributing guide documented

### NFR6: Security
- No hardcoded secrets in Docker image
- Secrets passed via environment variables
- License included with proper attribution

---

## Out of Scope (Phase 5)

- Advanced monitoring/APM integration
- Multi-language client libraries
- Helm charts for Kubernetes
- Cloud platform-specific deployment (AWS, GCP, Azure)
- UI/Dashboard
- Mobile client support

---

## Acceptance Criteria (Overall)

Phase 5 is complete when:

1. ✅ Docker image builds and runs successfully
2. ✅ Docker Compose starts all services, health checks pass
3. ✅ README quickstart tested end-to-end in < 5 minutes
4. ✅ All edge cases handled gracefully (no crashes)
5. ✅ Configuration validation with specific error messages working
6. ✅ Retry logic for Qdrant connections implemented
7. ✅ Graceful degradation for embedding API working
8. ✅ Graceful degradation for Claude API working
9. ✅ GitHub Actions CI/CD workflow passing
10. ✅ All documentation files created and reviewed
11. ✅ Version tagged (v1.0.0 or higher)
12. ✅ Changelog updated with Phase 5 changes
13. ✅ License file present and compliant
14. ✅ Code review passed
15. ✅ Ready for public GitHub release
