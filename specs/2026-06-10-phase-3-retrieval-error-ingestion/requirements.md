# Phase 3 Retrieval and Error Ingestion - Requirements

## Functional Requirements

### FR1: Webhook Endpoint
- **Endpoint:** POST `/webhook/error`
- **Port:** Configurable via `WEBHOOK_PORT` environment variable (default: 8000)
- **Protocol:** HTTP/HTTPS
- **Request Content-Type:** `application/json`
- **Response Content-Type:** `application/json`
- **Success Response:** HTTP 200 with RetrievalResultList JSON
- **Validation Failure:** HTTP 400 with error message
- **Authentication Failure:** HTTP 401 with error message
- **Server Error:** HTTP 500 with error message

### FR2: Webhook Authentication
- **Method:** HMAC-SHA256 signature validation
- **Header:** `X-Webhook-Signature` (required if WEBHOOK_SECRET is set)
- **Signature Format:** `sha256=<hex_digest>`
- **Secret Source:** `WEBHOOK_SECRET` environment variable
- **If WEBHOOK_SECRET not set:** Skip validation (dev mode)
- **Validation:** Compare computed signature to provided signature using constant-time comparison
- **On failure:** Return 401 Unauthorized with message "Invalid signature"

### FR3: Error Payload Parser
- **Input:** JSON object with fields:
  - `file_path` (required): string, relative or absolute path
  - `line_number` (required): integer > 0
  - `function_name` (optional): string
  - `error_type` (optional): string (e.g., "TypeError", "ValueError")
  - `error_message` (optional): string
  - `stacktrace` (optional): string or list of strings
  - `language` (optional): string (python, javascript, java, go)
- **Validation:**
  - file_path must not be empty
  - line_number must be > 0
  - stacktrace if present must be string or list
- **Output:** `ErrorContext` dataclass with normalized fields
- **On validation failure:** Raise ValueError with specific field name
- **Stacktrace normalization:** Convert list to newline-joined string if needed

### FR4: Python Stacktrace Parser
- **Input:** Python stacktrace string or lines
- **Format recognition:** Detect traceback format by "Traceback" header
- **Extract:** file_path, function_name, line_number for each frame
- **Handle:**
  - Multi-line frames with context (code lines shown)
  - Exception type and message on last line
  - Frames with missing line numbers (skip those frames)
- **Output:** List of `StackFrame(file_path, function_name, line_number)`
- **On parse error:** Return empty list (graceful degradation)
- **Example format:**
  ```
  Traceback (most recent call last):
    File "src/app.py", line 42, in process_data
      result = calculate(x, y)
    File "src/math.py", line 15, in calculate
      return a / b
  ZeroDivisionError: division by zero
  ```

### FR5: JavaScript Stacktrace Parser
- **Input:** JavaScript stacktrace string
- **Format recognition:** Detect by "Error:" prefix or "at " lines
- **Extract:** file_path, function_name, line_number:column_number for each frame
- **Handle:**
  - Node.js format: `at function (file.js:line:col)`
  - Browser format: `functionName@file.js:line:col`
  - Anonymous functions: show as `<anonymous>`
- **Output:** List of `StackFrame` (use line_number, ignore column)
- **On parse error:** Return empty list
- **Example formats:**
  ```
  Error: Cannot read property 'x' of undefined
    at processData (app.js:42:10)
    at Object.<anonymous> (app.js:1:1)
  ```

### FR6: Java Stacktrace Parser
- **Input:** Java stacktrace string
- **Format recognition:** Detect by "Exception:" or "at " lines
- **Extract:** class_name, method_name, file_path, line_number for each frame
- **Handle:**
  - Format: `at package.ClassName.methodName(FileName.java:123)`
  - Native methods: `(Native Method)`
  - Unknown source: `(Unknown Source)`
- **Output:** List of `StackFrame(file_path, function_name, line_number)`
- **On parse error:** Return empty list
- **Example format:**
  ```
  java.lang.NullPointerException
    at com.example.Calculator.divide(Calculator.java:45)
    at com.example.Main.main(Main.java:12)
  ```

### FR7: Go Stacktrace Parser
- **Input:** Go stacktrace string
- **Format recognition:** Detect by "panic:" or goroutine format
- **Extract:** file_path, function_name, line_number for each frame
- **Handle:**
  - Format: `file.go:line +0xoffset`
  - Function names with package prefix
  - Multiple goroutines (use main goroutine only)
- **Output:** List of `StackFrame`
- **On parse error:** Return empty list
- **Example format:**
  ```
  panic: runtime error: index out of range [10] with length 5
  
  goroutine 1 [running]:
  main.process()
      /path/to/file.go:42 +0x1c4
  main.main()
      /path/to/file.go:15 +0x44
  ```

### FR8: Query Constructor
- **Input:** `ErrorContext` with file_path, function_name, error_message, error_type
- **Strategy:** Build query prioritizing most specific to least specific
  1. If function_name present: `"function_name in file_path error_message error_type"`
  2. Else if file_path present: `"file_path error_message error_type"`
  3. Else: `"error_message error_type"`
- **Query length:** Max 500 characters (truncate if needed, preserve word boundaries)
- **Normalization:**
  - Remove leading/trailing whitespace
  - Replace multiple spaces with single space
  - Convert to lowercase for consistency (optional, depends on embedding model)
- **Output:** Single query string optimized for vector embedding
- **Examples:**
  - Input: `ErrorContext(file_path="src/app.py", function_name="process_data", error_message="division by zero")`
  - Output: `"process_data in src/app.py division by zero"`

### FR9: Qdrant Vector Search
- **Operation:** Search Qdrant collection for similar code chunks
- **Inputs:**
  - Query string (from FR8)
  - top_k from config (default: 5)
  - Metadata filters (optional: file_path, recent commits)
- **Process:**
  1. Embed query string using same embedding model as indexing
  2. Search Qdrant with vector and optional metadata filter
  3. Apply recency weighting to results
  4. Return top_k results sorted by final score
- **Metadata filtering:** Support filtering by:
  - `file_path`: Match exact file or similar paths
  - `commit_timestamp`: Restrict to commits within RECENT_COMMIT_WINDOW days
- **Output:** List of `RetrievalResult` with top_k items max
- **De-duplication:** If multiple chunks from same file/function appear, keep highest-scoring

### FR10: Recency Weighting Algorithm
- **Goal:** Boost scores for chunks from recent commits
- **Inputs:**
  - Original retrieval score (0-1 from vector similarity)
  - Commit timestamp of chunk
  - RECENT_COMMIT_WINDOW days (config, default: 30)
  - Current time
- **Algorithm:**
  ```
  days_old = (now - commit_timestamp).days
  if days_old <= RECENT_COMMIT_WINDOW:
    recency_boost = 1.0 - (days_old / RECENT_COMMIT_WINDOW) * 0.3
  else:
    recency_boost = 0.7
  final_score = original_score * recency_boost
  ```
- **Effect:** Recent commits get up to 30% boost, old commits penalized by 30%
- **Explanation:** A chunk from today gets 1.0x boost, from 30 days ago gets 0.7x
- **Output:** Updated score for each result

### FR11: Git Diff Retriever
- **Input:** List of commit hashes (from retrieval results)
- **Operation:** Fetch git diffs for each commit
- **Diff scope:**
  - For first N results: fetch full diff
  - For remaining results: fetch diff stats only (file list)
  - Limit: Fetch diffs for max 5 commits (to avoid performance issues)
- **Process:**
  1. For each commit, use GitPython to show diff
  2. Parse diff to extract changed file list
  3. For top 3 commits, include full diff
  4. For others, include only file list
- **Error handling:** If git diff fails, skip that commit (don't fail entire operation)
- **Caching:** Cache diffs per commit in memory to avoid re-fetching within single request
- **Output:** List of `CommitDiff(commit_hash, author, message, files_changed, diff_content)`

### FR12: Result Formatter
- **Input:**
  - List of `RetrievalResult` from vector search
  - List of `CommitDiff` from git retrieval
  - Original `ErrorContext`
- **Output:** JSON object with structure:
  ```json
  {
    "error_context": {
      "file_path": "string",
      "line_number": "integer",
      "function_name": "string or null",
      "error_type": "string or null",
      "error_message": "string or null"
    },
    "retrieval_results": [
      {
        "rank": 1,
        "file_path": "string",
        "start_line": integer,
        "end_line": integer,
        "code_snippet": "string (first 500 chars)",
        "commit_hash": "string",
        "commit_author": "string",
        "commit_timestamp": "ISO8601 datetime",
        "function_name": "string or null",
        "score": float (0-1),
        "recency_score": float (0-1)
      }
    ],
    "related_diffs": [
      {
        "commit_hash": "string",
        "author": "string",
        "message": "string",
        "timestamp": "ISO8601 datetime",
        "files_changed": ["file1.py", "file2.py"],
        "diff_content": "string or null (full diff for top 3 commits)"
      }
    ],
    "metadata": {
      "query_used": "string",
      "total_chunks_searched": integer,
      "search_duration_ms": float,
      "timestamp": "ISO8601 datetime"
    }
  }
  ```
- **Code snippet:** Truncate to 500 characters, end at line boundary or sentence boundary
- **Timestamp format:** ISO8601 with timezone

### FR13: MCP Tool - debug_error
- **Name:** `debug_error`
- **Description:** "Accept error payload and return relevant code chunks with commit context"
- **Input schema:** Pydantic model with fields:
  ```python
  file_path: str
  line_number: int
  function_name: Optional[str] = None
  error_type: Optional[str] = None
  error_message: Optional[str] = None
  stacktrace: Optional[str] = None
  language: Optional[str] = None
  ```
- **Output schema:** RetrievalResultList JSON (as defined in FR12)
- **Behavior:** Call webhook handler internally, return formatted results
- **Error handling:** Return error message with details if operation fails

### FR14: MCP Tool - search_codebase
- **Name:** `search_codebase`
- **Description:** "Perform arbitrary vector search over indexed code"
- **Input schema:**
  ```python
  query: str  # Search query text
  top_k: Optional[int] = 5  # Number of results (max 20)
  file_filter: Optional[str] = None  # Optional file path filter
  ```
- **Output schema:** Same as FR13 (RetrievalResultList)
- **Behavior:**
  1. Embed query string
  2. Search Qdrant with optional file_filter
  3. Apply recency weighting
  4. Return top_k results
- **Difference from debug_error:** No error parsing, direct query string

### FR15: MCP Tool - get_recent_diffs
- **Name:** `get_recent_diffs`
- **Description:** "Return diffs from last N commits on watched branch"
- **Input schema:**
  ```python
  num_commits: Optional[int] = 5  # Number of recent commits (max 20)
  branch: Optional[str] = None  # Branch name, defaults to WATCH_BRANCH
  ```
- **Output schema:** List of CommitDiff objects
- **Behavior:**
  1. Get last N commits on branch using GitPython
  2. Fetch full diff for each commit
  3. Return list of CommitDiff
- **Error handling:** If branch doesn't exist or repo not accessible, return error

### FR16: Error Handling
- **Invalid JSON payload:** Return 400 with "Invalid JSON"
- **Missing required fields:** Return 400 with field name and reason
- **Invalid line_number:** Return 400 with "line_number must be > 0"
- **Qdrant connection error:** Return 500 with "Qdrant connection failed"
- **Embedding API error:** Return 500 with "Embedding API failed"
- **All errors:** Include error_type and error_message fields in JSON response

### FR17: Logging
- **Webhook request received:** INFO log with IP, payload size, timestamp
- **Stacktrace parsing:** DEBUG log with parser used, frames extracted
- **Query constructed:** DEBUG log with query text length
- **Qdrant search started:** DEBUG log with collection, top_k
- **Retrieval results:** INFO log with num_results, top_score, duration_ms
- **Git diff fetch started:** DEBUG log with num_commits
- **Response sent:** INFO log with status_code, duration_ms
- **All errors:** ERROR log with full exception and context

## Non-Functional Requirements

### NFR1: Performance
- Webhook request → response latency: < 1 second total
- Vector search latency: < 500ms (excluding network to embedding API)
- Git diff fetch: < 300ms for 5 commits
- Query construction: < 50ms
- Result formatting: < 100ms

### NFR2: Reliability
- Webhook endpoint available 99.9% of the time
- Graceful degradation if git diff fails (return results without diffs)
- Graceful degradation if stacktrace parsing fails (use file_path + line_number)
- Retry logic for transient failures (Qdrant, embedding API)
- Max 3 retries with exponential backoff (1s, 2s, 4s)

### NFR3: Security
- HMAC-SHA256 signature validation on all webhook requests (if secret configured)
- Constant-time comparison for signature to prevent timing attacks
- No sensitive data (API keys, secrets) in logs
- No raw error payloads stored
- Input validation to prevent injection attacks

### NFR4: Observability
- All major operations logged at INFO level minimum
- Errors logged at ERROR level with full context
- Debug logging for stacktrace parsing, query construction, search
- Structured JSON logs using structlog
- Request tracing: include request_id in all logs for single request

### NFR5: Type Safety
- All functions fully type-annotated
- All domain types use dataclasses (ErrorContext, StackFrame, RetrievalResult, CommitDiff)
- mypy strict mode passes with no errors
- No Any types except where absolutely necessary

### NFR6: Test Coverage
- Unit tests for all stacktrace parsers (Python, JavaScript, Java, Go)
- Unit tests for error parser validation and extraction
- Unit tests for query constructor with various inputs
- Unit tests for recency weighting calculations
- Unit tests for result formatter JSON structure
- Integration test: Full webhook flow with valid payload
- Integration test: Retrieval accuracy (known error returns correct file in top 3)
- Integration test: Recency weighting (recent commits ranked higher)
- All tests run locally and in CI/CD
- Target: 85%+ code coverage for Phase 3 modules

### NFR7: Maintainability
- Each parser module is independent and testable
- Clear separation between parsing, searching, formatting
- All domain types documented with docstrings
- Error messages are specific and actionable
- Code follows project code standards from CLAUDE.md

## Domain Types

All types are Python dataclasses with full type annotations:

```python
@dataclass
class StackFrame:
    """Represents a single frame in a stacktrace"""
    file_path: str
    function_name: str
    line_number: int

@dataclass
class ErrorContext:
    """Normalized error information from webhook payload"""
    file_path: str
    line_number: int
    function_name: Optional[str]
    error_type: Optional[str]
    error_message: Optional[str]
    stacktrace: Optional[str]
    language: Optional[str]
    parsed_frames: list[StackFrame]  # Parsed stacktrace frames

@dataclass
class RetrievalResult:
    """Single code chunk retrieved from Qdrant"""
    rank: int
    file_path: str
    start_line: int
    end_line: int
    code_snippet: str
    commit_hash: str
    commit_author: str
    commit_timestamp: datetime
    function_name: Optional[str]
    original_score: float
    recency_score: float
    final_score: float

@dataclass
class CommitDiff:
    """Diff information for a single commit"""
    commit_hash: str
    author: str
    message: str
    timestamp: datetime
    files_changed: list[str]
    diff_content: Optional[str]  # Full diff for top commits, None for others

@dataclass
class RetrievalResultList:
    """Complete response to webhook request"""
    error_context: ErrorContext
    retrieval_results: list[RetrievalResult]
    related_diffs: list[CommitDiff]
    metadata: dict[str, Any]  # query_used, total_chunks, duration_ms, timestamp
```

## Configuration

From specs/tech-stack.md, these environment variables are used:

- **QDRANT_HOST:** Qdrant server hostname (required)
- **QDRANT_PORT:** Qdrant gRPC port (default: 6333)
- **QDRANT_COLLECTION:** Collection name (default: git_debug_oracle)
- **EMBEDDING_MODEL:** Model for query embedding (default: voyage-code-2)
- **EMBEDDING_API_KEY:** API key for embedding provider (required)
- **WEBHOOK_SECRET:** HMAC secret for webhook validation (optional, dev mode if not set)
- **WEBHOOK_PORT:** Port for FastAPI server (default: 8000)
- **TOP_K:** Number of retrieval results (default: 5, max: 20)
- **RECENT_COMMIT_WINDOW:** Days for recency weighting (default: 30)
- **REPO_PATH:** Path to Git repository (required for diff retrieval)
- **LOG_LEVEL:** Minimum log level (default: INFO)
- **ANTHROPIC_API_KEY:** Claude API key (not used in Phase 3, but must be present)

## Acceptance Criteria

All functional requirements FR1-FR17 must be implemented and tested.

Exit conditions from roadmap.md:
- Webhook endpoint accepts error payloads and returns 200 status
- Calling `debug_error` with a known error returns correct file in top 3 results
- Retrieval completes in under 500ms from query to results
- Recency weighting correctly ranks recent commits higher than old ones
- All stacktrace format parsers handle valid input without errors
- Integration test achieves 90%+ top-3 hit rate on test error set

All NFR1-NFR7 requirements met.

All domain types fully implemented and documented.

All unit and integration tests pass (85%+ coverage target).

## Dependencies

- Phase 1: Configuration loading, Qdrant client, structlog logging
- Phase 2: Indexed Qdrant collections, chunk metadata with commit info
- External: GitPython for git operations
- External: Embedding API (Voyage or OpenAI)

## Risk Mitigation

**Risk:** Stacktrace parsing fails for edge cases
**Mitigation:** Comprehensive test cases for each language, fallback to file_path + line_number

**Risk:** Vector search returns irrelevant results
**Mitigation:** Recency weighting + metadata filtering, integration tests verify hit rate

**Risk:** Webhook becomes performance bottleneck
**Mitigation:** Keep handler async, optimize embedding batching, cache diffs per request

**Risk:** Git diff fetch times out
**Mitigation:** Limit to 5 commits max, async git operations, timeout after 5 seconds
