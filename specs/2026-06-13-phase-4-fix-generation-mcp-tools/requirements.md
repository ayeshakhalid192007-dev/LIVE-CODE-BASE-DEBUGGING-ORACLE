# Phase 4 Fix Generation and MCP Tool Contracts - Requirements

## Functional Requirements

### FR1: Context Assembler
- **Input:** ErrorContext, RetrievalResult list, CommitDiff list
- **Process:**
  1. Format error metadata as readable text
  2. Include top 3 code chunks with line numbers
  3. Add relevant recent changes/diffs
  4. Fetch git blame for changed lines (authors, dates)
  5. Construct prompt with all context
- **Output:** Prompt context string (< 4000 tokens)
- **Error handling:** Gracefully handle missing diffs or git data

### FR2: Claude API Client
- **Configuration:**
  - Model: claude-opus-4-1
  - Temperature: 0.2 (low randomness for determinism)
  - Max tokens: 2048
  - System prompt: "You are a debugging expert..."
- **Prompt Caching:**
  - Cache system prompt and retrieval context
  - TTL: 5 minutes (within API limit)
  - Reduces latency on repeated queries for same error
- **Retry Logic:**
  - Max 3 retries on RateLimitError, APIConnectionError
  - Exponential backoff: 1s, 2s, 4s
  - Circuit breaker: After 5 consecutive failures, use fallback
- **Timeout:** 30 seconds max per request
- **Error handling:** Catch API errors, log, return fallback

### FR3: Fix Proposal Data Model
- **FixProposal dataclass fields:**
  ```python
  root_cause: str                          # Why the error occurred
  affected_file: str                       # File path containing bug
  affected_line_range: tuple[int, int]     # Start and end lines
  code_patch: str                          # Code fix (as snippet)
  patch_language: str                      # python, javascript, java, go
  confidence: float                        # 0-1 confidence score
  explanation: string                      # Human-readable explanation
  affected_functions: list[str]            # Function names affected
  root_cause_category: str                 # Category: logic, resource, boundary, type, etc.
  alternative_fixes: list[FixProposal]     # Optional alternatives
  ```
- **Validation:**
  - confidence between 0-1
  - code_patch is valid code snippet
  - affected_file matches error context
  - root_cause is non-empty string

### FR4: Fix Response Parser
- **Input:** Raw Claude API response
- **Parsing strategy:**
  1. Look for section headers: "Root Cause:", "Fix:", "Confidence:"
  2. Extract root cause statement
  3. Extract code patch (between ```language markers)
  4. Extract confidence (number 0-1 or percentage)
  5. Extract explanation text
  6. Identify alternative fixes if present
- **Edge cases:**
  - Multiple code blocks: take first one
  - Missing sections: use defaults with low confidence
  - Malformed patch: validate syntax, flag if invalid
- **Output:** FixProposal dataclass
- **Fallback:** If parsing fails, return raw response as explanation with 0.3 confidence

### FR5: Confidence Scoring Algorithm
- **Score factors (sum to 1.0):**
  - Retrieval confidence (0.4): How relevant were retrieved chunks
  - Claude certainty (0.3): "I'm confident", "likely", uncertainty markers
  - Patch validity (0.2): Can patch be parsed, is syntax valid
  - Error coverage (0.1): Does fix address stated root cause
- **Calculation:**
  ```
  confidence = (
    retrieval_score * 0.4 +
    claude_certainty * 0.3 +
    patch_validity * 0.2 +
    error_coverage * 0.1
  )
  ```
- **Range:** 0-1 (0 = no confidence, 1 = high confidence)
- **Threshold:** Only return if confidence >= 0.3 (configurable)

### FR6: MCP Tool - debug_error (Enhanced)
- **Purpose:** Accept error payload, return FixProposal
- **Input schema (Pydantic):**
  ```python
  file_path: str
  line_number: int
  function_name: Optional[str] = None
  error_type: Optional[str] = None
  error_message: Optional[str] = None
  stacktrace: Optional[str] = None
  language: Optional[str] = None
  ```
- **Output schema (Pydantic):**
  ```python
  error_context: ErrorContext
  retrieval_results: list[RetrievalResult]
  fix_proposal: Optional[FixProposal] = None
  status: str  # "success", "partial", "failed"
  ```
- **Behavior:**
  1. Parse error context
  2. Perform vector search
  3. Generate fix proposal via Claude
  4. Return combined result
- **Error handling:** Return error status with message if failures occur

### FR7: MCP Tool - get_index_status
- **Purpose:** Check indexing state without triggering reindex
- **Input schema (Pydantic):**
  ```python
  branch: Optional[str] = None  # Defaults to current branch
  ```
- **Output schema (Pydantic):**
  ```python
  is_indexed: bool
  last_indexed_commit: str
  last_indexed_timestamp: datetime
  total_chunks: int
  total_files: int
  branch: str
  status: str  # "indexed", "not_indexed", "indexing", "failed"
  ```
- **Behavior:**
  1. Check Qdrant collection exists
  2. Get collection stats (chunk count)
  3. Read last index metadata
  4. Return current status
- **Error handling:** Return status "failed" with message if errors occur

### FR8: MCP Tool - search_codebase (Updated)
- **Purpose:** Perform manual code search (existing tool, no changes)
- **Input schema:** Unchanged from Phase 3
- **Output schema:** Unchanged from Phase 3
- **Note:** Stable v1.0 contract

### FR9: MCP Tool - get_recent_diffs (Updated)
- **Purpose:** Get recent changes (existing tool, no changes)
- **Input schema:** Unchanged from Phase 3
- **Output schema:** Unchanged from Phase 3
- **Note:** Stable v1.0 contract

### FR10: MCP Tool Contracts - Stability
- **All tool schemas frozen:** No breaking changes in v1.0
- **Versioning:** Tools v1.0 guaranteed stable
- **Documentation:** Each tool includes:
  - Purpose (1 sentence)
  - Input schema with field descriptions
  - Output schema with field descriptions
  - Example usage
  - Error cases and handling
- **Testing:** Each tool schema validated on invocation

### FR11: Error Handling - Claude API Failures
- **RateLimitError (429):** Retry with backoff
- **APIConnectionError:** Retry with backoff, then fallback
- **Timeout:** Return error response, suggest manual retry
- **Auth error (401):** Return error, check ANTHROPIC_API_KEY
- **Context length exceeded:** Trim context, retry or fallback
- **All errors logged:** Include request ID, error details

### FR12: Fallback Strategy
- **When Claude API unavailable:**
  - Return raw retrieval results
  - No fix proposal generated
  - Mark status as "partial"
  - Log for monitoring
- **When fix parsing fails:**
  - Return full Claude response as explanation
  - Set confidence to 0.3
  - Flag for manual review
  - Log parse failure
- **When context assembly fails:**
  - Return error message
  - Suggest manual debug_error call with fewer parameters
  - Status: "failed"

### FR13: Logging & Monitoring
- **Log events:**
  - debug_error call received (INFO)
  - Retrieval results obtained (DEBUG: count, scores)
  - Claude API call started (INFO: model, prompt_length)
  - Claude API response received (DEBUG: completion_tokens)
  - Fix proposal generated (INFO: confidence, category)
  - Errors encountered (ERROR: full traceback)
- **Structured logging:** Use structlog with context
- **Request tracing:** Include request_id in all logs

### FR14: Performance Requirements
- **Latency breakdown:**
  - Context assembly: < 100ms
  - Claude API call: < 10s (with caching < 5s)
  - Fix parsing: < 50ms
  - Total end-to-end: < 30s
- **Throughput:** Handle concurrent requests
- **Caching:** Prompt cache reduces repeat queries by 50%+

### FR15: System Prompt
- **System prompt content:**
  - Role: "You are a debugging expert"
  - Task: Analyze error, retrieve code, propose fix
  - Output format: Root Cause → Fix → Confidence
  - Constraints: Concise, actionable, confidence rating 0-1
- **Prompt static:** Does not change per request
- **Cached:** Included in prompt caching

### FR16: Configuration Management
- **Environment variables required:**
  - ANTHROPIC_API_KEY: Claude API key
  - CLAUDE_MODEL: Model to use
  - FIX_GENERATION_ENABLED: Feature flag
- **Optional:**
  - CLAUDE_MAX_TOKENS: Max response tokens
  - CLAUDE_TIMEOUT_SECONDS: API timeout
  - FIX_PROPOSAL_CONFIDENCE_THRESHOLD: Min confidence to return
  - CLAUDE_RETRY_MAX: Max retry attempts

### FR17: Documentation
- **MCP tool contracts document:**
  - Schema for each tool (input/output)
  - Examples of valid requests and responses
  - Error cases and handling
- **Fix generation guide:**
  - How fix proposals are generated
  - Understanding confidence scores
  - Interpreting root cause analysis
- **API integration guide:**
  - Setting up Claude API
  - Configuration options
  - Troubleshooting common issues

## Non-Functional Requirements

### NFR1: Type Safety
- All functions fully type-annotated
- FixProposal and schemas as Pydantic models
- MCP tool inputs/outputs typed
- No Any types except where unavoidable
- mypy strict mode passes

### NFR2: Test Coverage
- Fix generation module: 85%+ coverage
- Context assembler: 90%+ coverage
- Parser: 95%+ coverage (many edge cases)
- MCP schemas: 100% coverage
- Integration tests: End-to-end workflow
- Target: 85%+ overall for Phase 4

### NFR3: Reliability
- Claude API failures gracefully degraded
- No unhandled exceptions
- Fallback to retrieval-only results
- Circuit breaker prevents cascade failures
- All errors logged with context

### NFR4: Performance
- Context assembly < 100ms
- Claude API < 10s (< 5s cached)
- Fix parsing < 50ms
- Total latency < 30s
- Prompt caching enabled by default

### NFR5: Maintainability
- Clear separation: assembler, client, parser, scoring
- Each component testable independently
- Schemas in separate file for clarity
- Configuration centralized
- Error paths explicit and logged

### NFR6: Security
- API key never logged
- Sensitive data not stored in context cache
- Input validation on all tool calls
- No code injection vulnerabilities
- Rate limiting respected

### NFR7: Documentation
- MCP tool contracts documented
- Fix generation workflow explained
- API configuration guide
- Troubleshooting guide
- Example fix proposals

## Data Models

```python
@dataclass
class FixProposal:
    root_cause: str
    affected_file: str
    affected_line_range: tuple[int, int]
    code_patch: str
    patch_language: str
    confidence: float
    explanation: str
    affected_functions: list[str]
    root_cause_category: str
    alternative_fixes: list['FixProposal'] = field(default_factory=list)

@dataclass
class IndexStatus:
    is_indexed: bool
    last_indexed_commit: str
    last_indexed_timestamp: datetime
    total_chunks: int
    total_files: int
    branch: str
    status: str
```

## Acceptance Criteria

All functional requirements FR1-FR17 implemented and tested.

Exit conditions:
- Calling `debug_error` returns FixProposal with all required fields
- Root cause analysis included in 80%+ of proposals
- Confidence scores accurately reflect fix quality
- All MCP tool contracts stable and documented
- Prompt caching reduces latency on repeated queries
- Error-to-fix workflow completes in < 30 seconds
- Integration tests verify fix quality on 10 known bugs
- All tests pass (85%+ coverage)

All NFR1-NFR7 requirements met.

## Dependencies

- Phase 1-3: Complete
- anthropic SDK: Claude API integration
- Pydantic: Schema validation
- GitPython: Git operations
- structlog: Structured logging

## Risk Mitigation

**Risk:** Claude API rate limiting
**Mitigation:** Retry logic, prompt caching, circuit breaker

**Risk:** Fix parsing fails on unusual responses
**Mitigation:** Comprehensive test cases, fallback to raw response

**Risk:** Latency exceeds budget
**Mitigation:** Prompt caching, async processing, timeouts

**Risk:** Malformed patches in response
**Mitigation:** Syntax validation, manual review flag

**Risk:** API key exposed
**Mitigation:** Never log key, validate at startup, use env vars only
