# Phase 3 Retrieval and Error Ingestion - Implementation Plan

## Overview

Phase 3 implements error ingestion via webhook, stacktrace parsing, vector-based code retrieval, and result formatting. This phase bridges the gap between error detection systems and the indexed codebase, enabling developers to retrieve contextual code for debugging.

## Architecture

### 1. Error Ingestion Pipeline

```
Error Payload (via webhook)
    ↓
[FastAPI webhook endpoint]
    ↓
[Webhook authentication]
    ↓
[Error payload validation]
    ↓
[Stacktrace parsing]
    ↓
[Query construction]
    ↓
[Vector search]
    ↓
[Result formatting]
    ↓
Response with code chunks
```

### 2. Component Breakdown

#### 2.1 Webhook Server (FastAPI)
- **Responsibility:** Accept HTTP POST requests with error payloads
- **Endpoint:** `/webhook/error`
- **Port:** Configurable via `WEBHOOK_PORT` (default: 8000)
- **Authentication:** HMAC-SHA256 validation using `WEBHOOK_SECRET`
- **Request validation:** Pydantic-based schema validation

#### 2.2 Error Parser
- **Responsibility:** Extract structured data from error payloads
- **Input:** Raw JSON error object
- **Output:** Normalized `ErrorContext` dataclass
- **Supported fields:** file_path, line_number, function_name, error_type, message, stacktrace

#### 2.3 Stacktrace Parsers
- **Responsibility:** Parse different stacktrace formats
- **Supported languages:** Python, JavaScript, Java, Go
- **Output:** List of `StackFrame` objects with file, function, and line number
- **Error handling:** Graceful fallback if parse fails

#### 2.4 Query Constructor
- **Responsibility:** Build vector search query from error metadata
- **Inputs:** ErrorContext, stacktrace frames
- **Outputs:** Search query string optimized for embedding
- **Strategy:** Prioritize function name > error message > file name

#### 2.5 Qdrant Retriever
- **Responsibility:** Perform vector search with metadata filtering
- **Operations:** 
  - Vector similarity search
  - Metadata filtering (file_path, commit recency)
  - Recency weighting algorithm
  - De-duplication of results
- **Output:** Ranked list of `RetrievalResult` objects

#### 2.6 Git Diff Retriever
- **Responsibility:** Fetch git diffs for commits containing top results
- **Inputs:** Commit hashes from retrieval results
- **Outputs:** List of `CommitDiff` objects
- **Strategy:** Use GitPython to fetch diffs efficiently

#### 2.7 Result Formatter
- **Responsibility:** Structure retrieval results for presentation
- **Inputs:** RetrievalResult list, CommitDiff list
- **Outputs:** Formatted JSON response
- **Fields:** file_path, line_range, commit_info, code_context, confidence_score

### 3. Data Flow

```
Error Webhook Request
├─ Validate signature
├─ Parse payload → ErrorContext
├─ Extract stacktrace → [StackFrame]
├─ Build query string
├─ Search Qdrant → [RetrievalResult]
├─ Apply recency weighting
├─ Fetch diffs → [CommitDiff]
└─ Format response → JSON
```

### 4. Integration Points

#### With Phase 1 (Foundation)
- Uses Qdrant client from config
- Uses structlog logging setup
- Uses pydantic settings for configuration

#### With Phase 2 (Indexing)
- Queries collections created by indexing
- Reads metadata stored by indexing
- Uses chunk_id and commit_hash from metadata

## Implementation Steps

### Step 1: Domain Models (errorctx, stacktrace)
- Create `ErrorContext` dataclass
- Create `StackFrame` dataclass
- Create `RetrievalResult` dataclass
- Create `CommitDiff` dataclass
- Add docstrings and type hints

### Step 2: Stacktrace Parsers
- Implement Python stacktrace parser
- Implement JavaScript stacktrace parser
- Implement Java stacktrace parser
- Implement Go stacktrace parser
- Unit tests for each parser format

### Step 3: Error Parser
- Parse error payload JSON
- Validate required fields
- Normalize stacktrace field
- Extract ErrorContext
- Unit tests for validation and extraction

### Step 4: Query Constructor
- Build search query from ErrorContext
- Prioritization logic for query terms
- Handle edge cases (missing fields)
- Unit tests for query construction

### Step 5: Qdrant Retriever
- Vector similarity search
- Metadata filtering logic
- Recency weighting implementation
- Result ranking and de-duplication
- Integration tests with real Qdrant

### Step 6: Git Diff Retriever
- Fetch commit diffs via GitPython
- Handle merge commits
- Cache diffs to avoid re-fetching
- Error handling for missing commits

### Step 7: Result Formatter
- Structure RetrievalResult list
- Add commit metadata
- Include code context
- Calculate confidence scores
- Format as JSON response

### Step 8: FastAPI Webhook Server
- Create FastAPI app instance
- Register POST /webhook/error endpoint
- Implement HMAC signature validation
- Request body validation via Pydantic
- Error handling and response formatting
- Health check endpoint

### Step 9: MCP Tool Integration
- Implement `debug_error` MCP tool
- Implement `search_codebase` MCP tool
- Implement `get_recent_diffs` MCP tool
- Tool input/output schemas
- Tool documentation strings

### Step 10: Integration Tests
- End-to-end error-to-retrieval test
- Multiple stacktrace format tests
- Recency weighting verification
- Error payload validation tests
- Webhook signature validation tests

### Step 11: Documentation
- Webhook payload format examples
- MCP tool usage examples
- Error handling guide
- Configuration guide

## File Structure

```
src/git_debug_oracle/
├── error_ingestion/              # NEW
│   ├── __init__.py
│   ├── models.py                 # ErrorContext, StackFrame, etc.
│   ├── parsers.py                # Error payload parser
│   ├── stacktrace.py             # Stacktrace parsers
│   ├── query.py                  # Query constructor
│   └── formatters.py             # Result formatter
├── retrieval/                    # NEW
│   ├── __init__.py
│   ├── qdrant.py                 # Qdrant retriever
│   ├── recency.py                # Recency weighting
│   └── git.py                    # Git diff retriever
├── webhook/                      # NEW
│   ├── __init__.py
│   ├── server.py                 # FastAPI app
│   └── security.py               # HMAC validation
└── mcp/
    └── tools.py                  # MCP tool definitions (updated)

tests/
├── unit/
│   ├── test_error_parser.py      # NEW
│   ├── test_stacktrace.py        # NEW
│   ├── test_query_constructor.py # NEW
│   ├── test_recency_weighting.py # NEW
│   └── test_result_formatter.py  # NEW
├── integration/
│   ├── test_webhook_flow.py      # NEW
│   ├── test_retrieval_end_to_end.py # NEW
│   └── test_mcp_debug_tool.py    # NEW
└── fixtures/
    ├── error_payloads.py         # NEW
    └── stacktraces.py            # NEW
```

## Testing Strategy

### Unit Tests
- Error parser: validate, normalize, extract fields
- Each stacktrace parser: parse valid/invalid formats
- Query constructor: prioritization logic, edge cases
- Recency weighting: score calculations, time ranges
- Result formatter: JSON structure, field presence

### Integration Tests
- Full webhook flow: request → response
- Retrieval accuracy: known error → correct file in top 3
- Recency weighting: recent commits ranked higher
- Multiple stacktrace formats in single error
- Error handling: invalid payloads, missing fields

### Performance Tests
- Retrieval latency: < 500ms query to results
- Webhook response time: < 1s including retrieval

## Success Criteria

1. **Webhook endpoint operational:** Accept valid error payloads, reject invalid
2. **Stacktrace parsing:** All four formats parse correctly
3. **Retrieval accuracy:** 90%+ top-3 hit rate on test error set
4. **Recency weighting:** Recent commits score higher than old ones
5. **Performance:** Retrieval completes in < 500ms
6. **MCP tools:** debug_error, search_codebase, get_recent_diffs implemented and working
7. **All tests pass:** Unit and integration tests achieve 85%+ coverage
8. **Documentation:** Webhook format, MCP tool contracts documented

## Risk Mitigation

### Risk: Stacktrace parsing fails silently
**Mitigation:** Fallback to file_path + line_number if stacktrace parse fails

### Risk: Vector search returns irrelevant results
**Mitigation:** Recency weighting + metadata filtering improves relevance

### Risk: Webhook becomes bottleneck
**Mitigation:** Keep webhook handler async, push heavy work to background if needed

### Risk: Git diffs expensive to fetch
**Mitigation:** Cache diffs per commit, limit number of diffs fetched

## Dependencies

- Phase 1: Configuration, Qdrant client, structlog setup
- Phase 2: Indexed Qdrant collections, chunk metadata
- External: GitPython for diff retrieval

## Timeline

- Step 1-3: Domain models and error parsing (Day 1)
- Step 4-5: Query and retrieval (Day 2)
- Step 6-7: Diffs and formatting (Day 3)
- Step 8-9: Webhook and MCP tools (Day 4)
- Step 10-11: Tests and documentation (Day 5)

Total: 5 days for full implementation
