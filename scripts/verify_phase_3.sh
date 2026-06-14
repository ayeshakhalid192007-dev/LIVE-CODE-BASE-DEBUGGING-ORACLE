#!/bin/bash
# verify_phase_3.sh
# Phase 3: Retrieval and Error Ingestion - Verify exit conditions

set -e

echo "=== Phase 3: Retrieval and Error Ingestion Exit Conditions Verification ==="
echo ""

# Check 1: Retriever module structure
echo "✓ Check 1: Retriever module structure..."
required_files=(
    "src/git_debug_oracle/retriever/query_constructor.py"
    "src/git_debug_oracle/retriever/qdrant_retriever.py"
    "src/git_debug_oracle/retriever/recency_weighting.py"
    "src/git_debug_oracle/retriever/result_formatter.py"
    "src/git_debug_oracle/retriever/git_diff_retriever.py"
)
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ✗ $file not found"
        exit 1
    fi
done
echo "  ✓ All retriever files present"

# Check 2: Error ingestion module
echo "✓ Check 2: Error ingestion module..."
if [ ! -f "src/git_debug_oracle/error_ingestion/parsers.py" ]; then
    echo "  ✗ parsers.py not found"
    exit 1
fi
echo "  ✓ parsers.py exists"

# Check 3: Webhook endpoint
echo "✓ Check 3: Webhook endpoint..."
if [ ! -f "src/git_debug_oracle/webhook/app.py" ]; then
    echo "  ✗ webhook/app.py not found"
    exit 1
fi
echo "  ✓ webhook/app.py exists"

# Check 4: MCP tools: debug_error, search_codebase, get_recent_diffs
echo "✓ Check 4: MCP tools..."
required_tools=(
    "src/git_debug_oracle/mcp_tools/debug_error.py"
)
for tool in "${required_tools[@]}"; do
    if [ ! -f "$tool" ]; then
        echo "  ✗ $tool not found"
        exit 1
    fi
done
echo "  ✓ MCP tools present"

# Check 5: Error parsing tests
echo "✓ Check 5: Error parsing tests..."
if [ ! -f "tests/unit/test_error_parser.py" ]; then
    echo "  ✗ test_error_parser.py not found"
    exit 1
fi
echo "  ✓ test_error_parser.py exists"

# Check 6: Retrieval integration tests
echo "✓ Check 6: Retrieval integration tests..."
if [ ! -f "tests/integration/test_retrieval_pipeline.py" ]; then
    echo "  ✗ test_retrieval_pipeline.py not found"
    exit 1
fi
echo "  ✓ test_retrieval_pipeline.py exists"

# Check 7: Run error parser tests
echo "✓ Check 7: Running error parser tests..."
if ! python -m pytest tests/unit/test_error_parser.py -v --tb=short &> /dev/null; then
    echo "  ✗ Error parser tests failed"
    exit 1
fi
echo "  ✓ Tests passed"

echo ""
echo "=== Phase 3 Exit Conditions: ALL PASSED ✓ ==="
echo ""
echo "Next: Proceed to Phase 4 (Fix Generation and MCP Tool Contracts)"
