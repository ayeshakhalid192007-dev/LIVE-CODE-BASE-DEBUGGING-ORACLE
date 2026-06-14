#!/bin/bash
# verify_phase_4.sh
# Phase 4: Fix Generation and MCP Tool Contracts - Verify exit conditions

set -e

echo "=== Phase 4: Fix Generation and MCP Tool Contracts Exit Conditions Verification ==="
echo ""

# Check 1: Fix generation module structure
echo "✓ Check 1: Fix generation module structure..."
required_files=(
    "src/git_debug_oracle/fix_generation/context.py"
    "src/git_debug_oracle/fix_generation/claude_client.py"
    "src/git_debug_oracle/fix_generation/parser.py"
    "src/git_debug_oracle/fix_generation/scoring.py"
)
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ✗ $file not found"
        exit 1
    fi
done
echo "  ✓ All fix generation files present"

# Check 2: MCP tools have schemas
echo "✓ Check 2: MCP tool schemas..."
if [ ! -f "src/git_debug_oracle/mcp_tools/schemas.py" ]; then
    echo "  ✗ schemas.py not found"
    exit 1
fi
echo "  ✓ schemas.py exists"

# Check 3: get_index_status MCP tool
echo "✓ Check 3: get_index_status MCP tool..."
if [ ! -f "src/git_debug_oracle/mcp_tools/get_index_status.py" ]; then
    echo "  ✗ get_index_status.py not found"
    exit 1
fi
echo "  ✓ get_index_status.py exists"

# Check 4: Domain types include FixProposal
echo "✓ Check 4: Domain types..."
if ! grep -q "class FixProposal" src/git_debug_oracle/types.py; then
    echo "  ✗ FixProposal not in types.py"
    exit 1
fi
echo "  ✓ FixProposal defined"

# Check 5: Context assembler tests
echo "✓ Check 5: Context assembler tests..."
if [ ! -f "tests/unit/test_context_assembler.py" ]; then
    echo "  ✗ test_context_assembler.py not found"
    exit 1
fi
echo "  ✓ test_context_assembler.py exists"

# Check 6: Fix generation integration tests
echo "✓ Check 6: Fix generation integration tests..."
if [ ! -f "tests/integration/test_fix_generation.py" ]; then
    echo "  ✗ test_fix_generation.py not found"
    exit 1
fi
echo "  ✓ test_fix_generation.py exists"

# Check 7: Documentation for MCP tools
echo "✓ Check 7: MCP tool documentation..."
if [ ! -f "docs/mcp_tools.md" ] && [ ! -f "docs/MCP_TOOLS.md" ]; then
    echo "  ✗ MCP tool documentation not found"
    exit 1
fi
echo "  ✓ MCP documentation exists"

# Check 8: Run context assembler tests
echo "✓ Check 8: Running context assembler tests..."
if ! python -m pytest tests/unit/test_context_assembler.py -v --tb=short &> /dev/null; then
    echo "  ✗ Context assembler tests failed"
    exit 1
fi
echo "  ✓ Tests passed"

echo ""
echo "=== Phase 4 Exit Conditions: ALL PASSED ✓ ==="
echo ""
echo "Next: Proceed to Phase 5 (OSS Hardening)"
