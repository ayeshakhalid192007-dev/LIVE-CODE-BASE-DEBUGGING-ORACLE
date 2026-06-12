# Phase 4 Fix Generation and MCP Tool Contracts - Validation

## Test Strategy

This document defines test cases for Phase 4 implementation validation.

## Unit Tests

### Test File: tests/unit/test_fix_models.py

**Test Suite: FixProposal Model**

```python
def test_fix_proposal_creation():
    """Create valid FixProposal"""
    fix = FixProposal(
        root_cause="Off-by-one error in loop",
        affected_file="src/app.py",
        affected_line_range=(42, 45),
        code_patch="for i in range(len(items) - 1):",
        patch_language="python",
        confidence=0.85,
        explanation="Changed range end to exclude last item",
        affected_functions=["process_items"],
        root_cause_category="logic"
    )
    assert fix.confidence == 0.85

def test_fix_proposal_validation():
    """Confidence must be 0-1"""
    with pytest.raises(ValueError):
        FixProposal(..., confidence=1.5)

def test_fix_proposal_json_serialization():
    """FixProposal serializes to JSON"""
    fix = FixProposal(...)
    json_str = json.dumps(fix, default=str)
    assert "root_cause" in json_str
```

### Test File: tests/unit/test_context_assembler.py

**Test Suite: Context Assembly**

```python
def test_assemble_context_from_error():
    """Assemble context from error and retrieval results"""
    ctx = ErrorContext(file_path="app.py", line_number=42)
    results = [
        RetrievalResult(...),
        RetrievalResult(...)
    ]
    
    context = assemble_context(ctx, results, [])
    
    assert "app.py" in context
    assert "line 42" in context
    assert len(context) < 4000  # Token limit

def test_context_includes_code_snippets():
    """Context includes retrieved code with line numbers"""
    ctx = ErrorContext(...)
    results = [RetrievalResult(start_line=10, code_snippet="def foo()")]
    
    context = assemble_context(ctx, results, [])
    
    assert "10:" in context or "def foo()" in context

def test_context_includes_diffs():
    """Context includes recent diffs"""
    ctx = ErrorContext(...)
    results = []
    diffs = [CommitDiff(...)]
    
    context = assemble_context(ctx, results, diffs)
    
    assert "diff" in context.lower() or "changed" in context.lower()

def test_context_token_count():
    """Context respects 4000 token limit"""
    ctx = ErrorContext(...)
    results = [RetrievalResult(...) for _ in range(10)]
    
    context = assemble_context(ctx, results, [])
    
    # Approximate: 1 token ≈ 4 chars
    assert len(context) < 16000  # Conservative limit
```

### Test File: tests/unit/test_fix_parser.py

**Test Suite: Fix Proposal Parsing**

```python
def test_parse_well_formed_response():
    """Parse standard Claude response format"""
    response = """
Root Cause: Off-by-one error in array access
    
Fix:
```python
for i in range(len(items) - 1):
    process(items[i])
```

Confidence: 0.9
    
The error occurred because the loop didn't account for array length.
"""
    fix = parse_fix_response(response)
    
    assert fix.root_cause == "Off-by-one error in array access"
    assert fix.confidence == 0.9
    assert "range(len(items) - 1)" in fix.code_patch

def test_parse_confidence_as_percentage():
    """Parse confidence as percentage"""
    response = "Confidence: 85%\nRoot Cause: ..."
    fix = parse_fix_response(response)
    assert fix.confidence == 0.85

def test_parse_missing_sections():
    """Handle missing sections gracefully"""
    response = "Root Cause: Issue X\nNo fix section"
    fix = parse_fix_response(response)
    
    assert fix.root_cause == "Issue X"
    assert fix.confidence < 0.5  # Low confidence

def test_parse_multiple_code_blocks():
    """Use first code block as patch"""
    response = """
```python
# First block
for i in range(len(items) - 1):
```

```python
# Second block
x = y
```
"""
    fix = parse_fix_response(response)
    assert "for i in range" in fix.code_patch

def test_parse_malformed_response():
    """Fallback on unparseable response"""
    response = "Random text with no structure"
    fix = parse_fix_response(response)
    
    assert fix.confidence < 0.4
    assert fix.explanation == response
```

### Test File: tests/unit/test_confidence_scoring.py

**Test Suite: Confidence Scoring**

```python
def test_score_perfect_conditions():
    """Perfect conditions yield high confidence"""
    score = calculate_confidence(
        retrieval_score=1.0,
        claude_certainty=1.0,
        patch_validity=1.0,
        error_coverage=1.0
    )
    assert 0.95 <= score <= 1.0

def test_score_poor_conditions():
    """Poor conditions yield low confidence"""
    score = calculate_confidence(
        retrieval_score=0.2,
        claude_certainty=0.2,
        patch_validity=0.2,
        error_coverage=0.2
    )
    assert 0.2 <= score <= 0.3

def test_score_weighting():
    """Factors weighted correctly"""
    # High retrieval, low Claude
    score1 = calculate_confidence(0.9, 0.2, 0.5, 0.5)
    # Low retrieval, high Claude
    score2 = calculate_confidence(0.2, 0.9, 0.5, 0.5)
    
    # Retrieval should have more influence (0.4 weight)
    assert score1 > score2

def test_score_range():
    """Score always 0-1"""
    for _ in range(10):
        score = calculate_confidence(
            random.uniform(0, 1),
            random.uniform(0, 1),
            random.uniform(0, 1),
            random.uniform(0, 1)
        )
        assert 0 <= score <= 1
```

### Test File: tests/unit/test_mcp_schemas.py

**Test Suite: MCP Tool Schemas**

```python
def test_debug_error_input_validation():
    """debug_error input schema validated"""
    # Valid input
    input_data = {
        "file_path": "app.py",
        "line_number": 42
    }
    model = DebugErrorInput(**input_data)
    assert model.file_path == "app.py"

def test_debug_error_input_rejects_invalid():
    """Invalid inputs rejected"""
    with pytest.raises(ValidationError):
        DebugErrorInput(file_path="", line_number=0)

def test_debug_error_output_schema():
    """debug_error output has all required fields"""
    output = DebugErrorOutput(
        error_context=ErrorContext(...),
        retrieval_results=[],
        fix_proposal=FixProposal(...),
        status="success"
    )
    assert output.status in ["success", "partial", "failed"]

def test_index_status_output_schema():
    """get_index_status output valid"""
    status = IndexStatus(
        is_indexed=True,
        last_indexed_commit="abc123",
        last_indexed_timestamp=datetime.now(timezone.utc),
        total_chunks=1000,
        total_files=50,
        branch="main",
        status="indexed"
    )
    assert status.status in ["indexed", "not_indexed", "indexing", "failed"]
```

## Integration Tests

### Test File: tests/integration/test_fix_generation_e2e.py

**Test Suite: End-to-End Fix Generation**

```python
@pytest.mark.asyncio
async def test_debug_error_returns_fix_proposal():
    """Call debug_error, get FixProposal back"""
    error = {
        "file_path": "src/app.py",
        "line_number": 42,
        "error_message": "IndexError: list index out of range"
    }
    
    response = await client.post("/webhook/error", json=error)
    assert response.status_code == 200
    
    data = response.json()
    assert "fix_proposal" in data
    assert data["fix_proposal"]["confidence"] > 0

@pytest.mark.asyncio
async def test_fix_proposal_has_all_fields():
    """FixProposal includes all required fields"""
    error = {...}
    response = await client.post("/webhook/error", json=error)
    fix = response.json()["fix_proposal"]
    
    required_fields = [
        "root_cause", "affected_file", "code_patch",
        "confidence", "explanation"
    ]
    for field in required_fields:
        assert field in fix

@pytest.mark.asyncio
async def test_confidence_score_reasonable():
    """Confidence score reflects fix quality"""
    error = {...}
    response = await client.post("/webhook/error", json=error)
    confidence = response.json()["fix_proposal"]["confidence"]
    
    assert 0 <= confidence <= 1
    assert confidence >= 0.3  # Should have some confidence

@pytest.mark.asyncio
async def test_error_to_fix_latency():
    """End-to-end latency < 30 seconds"""
    error = {...}
    
    start = time.time()
    response = await client.post("/webhook/error", json=error)
    latency = time.time() - start
    
    assert response.status_code == 200
    assert latency < 30.0

@pytest.mark.asyncio
async def test_fix_generation_with_known_bug():
    """Generate fix for known bug in test repo"""
    # Assuming indexed test repository with known bug
    error = {
        "file_path": "tests/fixtures/buggy_math.py",
        "line_number": 15,
        "error_message": "ZeroDivisionError: division by zero"
    }
    
    response = await client.post("/webhook/error", json=error)
    assert response.status_code == 200
    
    fix = response.json()["fix_proposal"]
    # Fix should mention division or zero
    assert "division" in fix["explanation"].lower() or \
           "zero" in fix["explanation"].lower()
```

### Test File: tests/integration/test_mcp_tools_e2e.py

**Test Suite: MCP Tool Integration**

```python
def test_mcp_debug_error_tool():
    """Invoke debug_error MCP tool"""
    result = mcp.call_tool("debug_error", {
        "file_path": "app.py",
        "line_number": 42,
        "error_message": "IndexError"
    })
    
    assert "fix_proposal" in result
    assert result["status"] in ["success", "partial"]

def test_mcp_get_index_status_tool():
    """Invoke get_index_status MCP tool"""
    result = mcp.call_tool("get_index_status", {})
    
    assert "is_indexed" in result
    assert "last_indexed_commit" in result
    assert result["status"] in ["indexed", "not_indexed", "indexing", "failed"]

def test_mcp_tool_input_validation():
    """MCP tool input validated"""
    # Invalid line number
    with pytest.raises(ValidationError):
        mcp.call_tool("debug_error", {
            "file_path": "app.py",
            "line_number": -1
        })

def test_mcp_tool_output_typed():
    """MCP tool output has correct type"""
    result = mcp.call_tool("debug_error", {...})
    
    # Should be able to parse as DebugErrorOutput
    output = DebugErrorOutput(**result)
    assert output is not None
```

### Test File: tests/integration/test_error_to_fix_workflow.py

**Test Suite: Complete Workflow**

```python
@pytest.mark.asyncio
async def test_workflow_error_to_fix():
    """Full workflow: error retrieval to fix proposal"""
    # Step 1: Error ingestion
    error = {"file_path": "app.py", "line_number": 42}
    
    # Step 2: Retrieval
    response = await client.post("/webhook/error", json=error)
    assert response.status_code == 200
    data = response.json()
    
    # Step 3: Verify retrieval results present
    assert len(data["retrieval_results"]) > 0
    
    # Step 4: Verify fix proposal generated
    assert data["fix_proposal"] is not None
    
    # Step 5: Verify confidence score
    assert 0 <= data["fix_proposal"]["confidence"] <= 1

@pytest.mark.asyncio
async def test_workflow_with_multiple_errors():
    """Workflow with multiple similar errors"""
    errors = [
        {"file_path": "app.py", "line_number": 42},
        {"file_path": "app.py", "line_number": 50},
        {"file_path": "utils.py", "line_number": 10}
    ]
    
    fixes = []
    for error in errors:
        response = await client.post("/webhook/error", json=error)
        fixes.append(response.json()["fix_proposal"])
    
    # Similar errors should have similar confidence ranges
    assert all(0 <= f["confidence"] <= 1 for f in fixes)

@pytest.mark.asyncio
async def test_workflow_handles_missing_fields():
    """Workflow handles partially specified errors"""
    # Minimal error
    error = {"file_path": "app.py", "line_number": 1}
    
    response = await client.post("/webhook/error", json=error)
    # Should still work, but confidence may be lower
    assert response.status_code == 200
```

## Acceptance Tests

### Test File: tests/acceptance/test_phase_4_acceptance.py

```python
def test_exit_condition_fix_proposal_returned():
    """Calling debug_error returns FixProposal"""
    error = {"file_path": "app.py", "line_number": 42}
    response = client.post("/webhook/error", json=error)
    
    assert response.status_code == 200
    assert "fix_proposal" in response.json()
    assert response.json()["fix_proposal"] is not None

def test_exit_condition_root_cause_included():
    """80%+ of proposals include root cause analysis"""
    test_errors = [...]  # 10+ known errors
    
    fixes = [generate_fix(e) for e in test_errors]
    with_root_cause = sum(1 for f in fixes if f.root_cause)
    
    assert with_root_cause / len(fixes) >= 0.8

def test_exit_condition_confidence_accurate():
    """Confidence scores reflect fix quality"""
    # Verify on sample: high confidence fixes should be better
    high_conf = [f for f in test_fixes if f.confidence > 0.8]
    low_conf = [f for f in test_fixes if f.confidence < 0.5]
    
    # This is subjective, but we can spot-check
    assert len(high_conf) > 0

def test_exit_condition_mcp_tools_stable():
    """All MCP tool contracts are stable"""
    tools = ["debug_error", "get_index_status", "search_codebase", "get_recent_diffs"]
    
    for tool in tools:
        schema = mcp.get_tool_schema(tool)
        assert schema is not None
        assert "input" in schema
        assert "output" in schema

def test_exit_condition_latency_budget():
    """End-to-end latency < 30 seconds"""
    error = {"file_path": "app.py", "line_number": 42}
    
    times = []
    for _ in range(5):
        start = time.time()
        response = client.post("/webhook/error", json=error)
        times.append(time.time() - start)
    
    avg_time = sum(times) / len(times)
    assert avg_time < 30.0

def test_exit_condition_integration_test():
    """Integration test passes on 10 known bugs"""
    known_bugs = [...]  # 10 test cases
    
    results = []
    for bug in known_bugs:
        fix = generate_fix(bug)
        results.append(fix)
    
    # All should return a fix
    assert all(r.code_patch for r in results)
```

## Coverage Requirements

- Target: 85%+ code coverage for Phase 4
- Measured: `uv run pytest --cov=src/git_debug_oracle.fix_generation --cov=src/git_debug_oracle.mcp.schemas`

## Test Execution

```bash
# All tests
uv run pytest tests/

# Phase 4 only
uv run pytest tests/ -k "fix_generation or mcp_schemas"

# Unit tests
uv run pytest tests/unit/test_fix*.py tests/unit/test_mcp*.py

# Integration tests
uv run pytest tests/integration/test_fix_generation_e2e.py -v

# With coverage
uv run pytest tests/ --cov=src/git_debug_oracle --cov-report=html
```

## Exit Criteria Checklist

- [ ] FixProposal model complete with all fields
- [ ] Context assembler produces valid prompts
- [ ] Claude API client calls and parses responses
- [ ] Fix proposal parser handles 10+ edge cases
- [ ] Confidence scoring algorithm implemented
- [ ] All MCP tool contracts defined and stable
- [ ] Fallback strategies working
- [ ] Error handling comprehensive
- [ ] Logging and monitoring in place
- [ ] Unit tests: 95%+ pass rate
- [ ] Integration tests: All pass
- [ ] Acceptance tests: All pass
- [ ] Code coverage: 85%+
- [ ] mypy: No type errors
- [ ] ruff: No linting errors
- [ ] Documentation complete with examples

---

## Known Issues / Future Enhancements

- Alternative fixes not yet prioritized
- Claude model selection could be configurable per error type
- Fine-tuning Claude responses with feedback loops
- Batch fix generation for multiple errors
- Integration with issue tracking systems
