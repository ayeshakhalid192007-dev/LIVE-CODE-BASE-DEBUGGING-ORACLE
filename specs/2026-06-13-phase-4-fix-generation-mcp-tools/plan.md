# Phase 4 Fix Generation and MCP Tool Contracts - Implementation Plan

## Overview

Phase 4 integrates Claude API for fix generation with root cause analysis, finalizes all MCP tool contracts with stable schemas, and establishes a robust error-to-fix workflow. This phase transforms retrieval results into actionable fix proposals.

## Architecture

### 1. Context Assembly Pipeline

```
Error Context + Retrieval Results
    ↓
[Combine into Prompt Context]
    ├─ Error metadata (file, line, stacktrace)
    ├─ Retrieved code chunks (top 3)
    ├─ Recent diffs
    └─ Commit history
    ↓
[Create Claude Prompt]
    ├─ System prompt (fix generation expert)
    ├─ Error context
    ├─ Code samples
    └─ Analysis directives
    ↓
[Send to Claude API with Caching]
```

### 2. Fix Generation Flow

```
Prompt Context
    ↓
[Claude API Call]
    ├─ Model: claude-opus-4.1
    ├─ Prompt caching enabled
    ├─ Max tokens: 2048
    ↓
[Parse Response]
    ├─ Root cause extraction
    ├─ Code patch extraction
    ├─ Confidence scoring
    └─ Explanation text
    ↓
[Format as FixProposal]
    ├─ root_cause: string
    ├─ affected_file: string
    ├─ code_patch: string
    ├─ confidence: float (0-1)
    ├─ explanation: string
    └─ alternative_fixes: list[FixProposal]
```

### 3. MCP Tool Contract System

```
Tool Definition (Input Schema)
    ↓
[Pydantic Model Validation]
    ↓
[Execute Tool Logic]
    ↓
[Generate Output Schema]
    ↓
[Return Structured Output]
    ↓
[Client Receives Typed Result]
```

## Component Breakdown

### 4.1 Context Assembler
- **Responsibility:** Combine retrieval results, error info, and diffs into coherent prompt
- **Inputs:**
  - ErrorContext (file, line, error type, message, stacktrace)
  - RetrievalResult list (top 3 code chunks)
  - CommitDiff list (recent changes)
  - Git history (last N commits)
- **Processing:**
  1. Format error metadata as structured text
  2. Include retrieved code chunks with line numbers
  3. Add relevant diffs for context
  4. Extract git blame info for changed lines
- **Output:** Prompt context string (< 4000 tokens)
- **Caching:** Cache context per error hash to avoid recomputation

### 4.2 Claude API Client
- **Responsibility:** Call Claude API for fix generation
- **Configuration:**
  - Model: claude-opus-4.1
  - Max tokens: 2048
  - Temperature: 0.2 (low randomness)
  - System prompt: Fix generation expert instructions
- **Prompt caching:**
  - Cache system prompt + error context
  - TTL: 5 minutes
  - Reduce latency on repeated queries
- **Retry logic:**
  - Max 3 retries on transient errors
  - Exponential backoff: 1s, 2s, 4s
  - Circuit breaker: 5 consecutive failures → fallback
- **Latency target:** < 10 seconds end-to-end

### 4.3 Fix Proposal Parser
- **Responsibility:** Extract structured fix data from Claude response
- **Parsing strategy:**
  1. Split response into sections (Root Cause, Fix, Confidence)
  2. Extract root cause statement
  3. Extract code patch (between ```python/js/java/go markers)
  4. Extract confidence score (0-1 or percentage)
  5. Extract explanation text
  6. Identify alternative fixes if present
- **Error handling:** If parsing fails, return response as explanation with low confidence
- **Output:** FixProposal dataclass
- **Validation:** Ensure patch is valid code snippet

### 4.4 MCP Tool Contract System
- **Responsibility:** Define stable, typed contracts for all MCP tools
- **Tool types:**
  - Input schema: Pydantic model (required, optional fields)
  - Output schema: Pydantic model (structured return)
  - Documentation: Purpose, usage examples, error cases
- **Contract enforcement:**
  - Input validation on tool call
  - Output validation before returning
  - Type checking with mypy
- **Versioning:** v1.0 stable for production use
- **Breaking changes:** None permitted in v1

### 4.5 Confidence Scoring
- **Purpose:** Rate quality of fix proposal
- **Factors:**
  - Retrieval confidence (how relevant were code chunks)
  - Claude response certainty (explicit markers: "I'm confident", "likely", etc.)
  - Patch validity (can be parsed, follows syntax)
  - Error coverage (does fix address root cause)
- **Scoring:**
  ```
  confidence = (retrieval_score * 0.4 + 
                claude_certainty * 0.3 + 
                patch_validity * 0.2 +
                error_coverage * 0.1)
  ```
- **Output:** Float 0-1 (0 = no confidence, 1 = high confidence)

### 4.6 Fallback Strategy
- **When Claude API unavailable:**
  - Return raw retrieval results as fix suggestions
  - Use recency weighting for ranking
  - Mark confidence as 0.5 (medium, no analysis)
- **When fix parsing fails:**
  - Return full Claude response as explanation
  - Set confidence to 0.3
  - Flag for manual review
- **When context assembly fails:**
  - Return error message
  - Suggest manual retrieval query
  - Log for debugging

## Implementation Steps

### Step 1: Domain Models (Day 1)
- Create FixProposal dataclass with all fields
- Create MCP tool input/output schemas
- Create ContextAssembly types
- Add type hints and docstrings
- Unit tests for model validation

### Step 2: Context Assembler (Day 1)
- Implement context_from_retrieval() function
- Add git blame integration
- Implement prompt formatting
- Unit tests for context assembly
- Integration test with real retrieval results

### Step 3: Claude API Client (Day 1-2)
- Create ClaudeClient wrapper
- Implement prompt caching logic
- Add retry/backoff logic
- Circuit breaker for API failures
- Unit tests for API calls (mocked)
- Integration tests with real API

### Step 4: Fix Proposal Parser (Day 2)
- Implement parse_fix_response() function
- Extract root cause, patch, confidence
- Handle edge cases (malformed responses)
- Unit tests for parsing (10+ test cases)
- Integration test end-to-end

### Step 5: MCP Tool Contracts (Day 2)
- Define all tool schemas (input + output)
- Implement validation logic
- Update debug_error tool to use FixProposal
- Add get_index_status tool
- Document all tool contracts
- Unit tests for schema validation

### Step 6: Confidence Scoring (Day 2-3)
- Implement scoring algorithm
- Add factor calculations
- Integrate with fix generation
- Unit tests for scoring logic
- Integration test end-to-end

### Step 7: Error Handling & Fallbacks (Day 3)
- Implement fallback strategies
- Add circuit breaker logic
- Add graceful degradation
- Unit tests for error paths
- Integration tests with failures injected

### Step 8: Documentation & Examples (Day 3)
- MCP tool contract documentation
- Fix generation guide with examples
- API error handling guide
- Configuration guide
- Example fix proposals from real errors

## File Structure

```
src/git_debug_oracle/
├── fix_generation/                  # NEW
│   ├── __init__.py
│   ├── models.py                    # FixProposal, schemas
│   ├── context.py                   # Context assembler
│   ├── claude_client.py             # Claude API integration
│   ├── parser.py                    # Fix proposal parser
│   ├── scoring.py                   # Confidence scoring
│   └── fallback.py                  # Fallback strategies
├── mcp/
│   ├── tools.py                     # UPDATED: Add new tool contracts
│   └── schemas.py                   # NEW: Pydantic schemas for tools
├── webhook/
│   └── server.py                    # UPDATED: Integrate fix generation
└── config.py                        # UPDATED: Add Claude API config

tests/
├── unit/
│   ├── test_fix_models.py           # NEW
│   ├── test_context_assembler.py    # NEW
│   ├── test_claude_client.py        # NEW (mocked API)
│   ├── test_fix_parser.py           # NEW
│   ├── test_confidence_scoring.py   # NEW
│   ├── test_mcp_schemas.py          # NEW
│   └── test_fallback_strategies.py  # NEW
├── integration/
│   ├── test_fix_generation_e2e.py   # NEW
│   ├── test_mcp_tools_e2e.py        # NEW
│   └── test_error_to_fix_workflow.py # NEW
└── fixtures/
    ├── sample_fixes.py              # NEW
    └── claude_responses.py          # NEW
```

## Testing Strategy

### Unit Tests
- Domain models: validation, serialization
- Context assembler: prompt formatting, edge cases
- Fix parser: extraction accuracy, malformed responses
- Confidence scoring: algorithm correctness
- MCP schemas: validation, type safety
- Fallback: degradation paths

### Integration Tests
- Full error-to-fix workflow
- Claude API calls (with real API in CI)
- MCP tool invocations
- Error handling paths
- Performance benchmarks

### Mock Strategy
- Mock Claude API responses in unit tests
- Use real Claude API in integration tests (CI only)
- Fixture set of real Claude responses for repeatability

## Success Criteria

1. **Fix generation operational:** FixProposal returned with all fields
2. **Root cause analysis:** Included in 80%+ of proposals
3. **Confidence scoring:** Accurately reflects fix quality
4. **MCP tools:** All contracts stable and validated
5. **Prompt caching:** Reduces latency on repeated queries
6. **Error-to-fix workflow:** Completes in < 30 seconds
7. **All tests pass:** 85%+ coverage for Phase 4 modules
8. **Documentation:** Complete with examples

## Risk Mitigation

### Risk: Claude API latency
**Mitigation:** Prompt caching, async processing, timeouts

### Risk: Fix parsing fails
**Mitigation:** Fallback to raw response, manual review flag

### Risk: Claude API unavailable
**Mitigation:** Circuit breaker, graceful degradation to retrieval

### Risk: Malformed responses
**Mitigation:** Comprehensive parser tests, error handling

## Dependencies

- Phase 1-3: All foundational phases complete
- Claude API: anthropic SDK
- Pydantic: Schema validation
- GitPython: Git blame/history

## Timeline

- Step 1-3: Models and API (Days 1-2)
- Step 4-6: Parser and scoring (Days 2-3)
- Step 7-8: Error handling and docs (Day 3)

Total: 3 days for full implementation

## Configuration

New environment variables:

- **ANTHROPIC_API_KEY:** Claude API key (required)
- **CLAUDE_MODEL:** Model ID (default: claude-opus-4-1)
- **CLAUDE_MAX_TOKENS:** Max response tokens (default: 2048)
- **FIX_GENERATION_ENABLED:** Boolean (default: true)
- **FIX_PROPOSAL_CONFIDENCE_THRESHOLD:** Min score to return (default: 0.3)
- **CLAUDE_TIMEOUT_SECONDS:** API timeout (default: 30)
- **CLAUDE_RETRY_MAX:** Max retries (default: 3)

## MCP Tool Contracts (v1.0)

### Tool: debug_error
- **Input:** ErrorContext (file_path, line_number, etc.)
- **Output:** FixProposal (root_cause, code_patch, confidence, etc.)
- **Purpose:** Accept error and return fix proposal

### Tool: get_index_status
- **Input:** None (optional: filter by branch)
- **Output:** IndexStatus (last_commit, chunk_count, timestamp)
- **Purpose:** Check indexing state

### Tool: search_codebase
- **Input:** Query string, optional filters
- **Output:** RetrievalResultList
- **Purpose:** Manual code search

### Tool: get_recent_diffs
- **Input:** Num commits, optional branch
- **Output:** List[CommitDiff]
- **Purpose:** Get recent changes
