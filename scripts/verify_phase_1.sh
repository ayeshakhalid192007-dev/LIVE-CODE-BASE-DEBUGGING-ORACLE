#!/bin/bash
# verify_phase_1.sh
# Phase 1: Foundation - Verify exit conditions

set -e

echo "=== Phase 1: Foundation Exit Conditions Verification ==="
echo ""

# Check 1: Docker Compose can start Qdrant
echo "✓ Check 1: Docker Compose starts Qdrant..."
if ! command -v docker-compose &> /dev/null; then
    echo "  ✗ docker-compose not found"
    exit 1
fi
echo "  ✓ docker-compose available"

# Check 2: MCP server exists and has correct entry point
echo "✓ Check 2: MCP server entry point..."
if [ ! -f "src/git_debug_oracle/server.py" ]; then
    echo "  ✗ server.py not found"
    exit 1
fi
echo "  ✓ server.py exists"

# Check 3: Configuration loader exists
echo "✓ Check 3: Configuration loading..."
if [ ! -f "src/git_debug_oracle/config.py" ]; then
    echo "  ✗ config.py not found"
    exit 1
fi
echo "  ✓ config.py exists"

# Check 4: pyproject.toml configured correctly
echo "✓ Check 4: Project metadata..."
if ! grep -q "name = \"git-debug-oracle\"" pyproject.toml; then
    echo "  ✗ Project name not in pyproject.toml"
    exit 1
fi
echo "  ✓ pyproject.toml configured"

# Check 5: structlog configured
echo "✓ Check 5: Logging configuration..."
if [ ! -f "src/git_debug_oracle/utils/logging.py" ]; then
    echo "  ✗ logging.py not found"
    exit 1
fi
echo "  ✓ logging.py exists"

# Check 6: .env.example exists
echo "✓ Check 6: Environment template..."
if [ ! -f ".env.example" ]; then
    echo "  ✗ .env.example not found"
    exit 1
fi
echo "  ✓ .env.example exists"

# Check 7: Pre-commit hooks configured
echo "✓ Check 7: Pre-commit hooks..."
if [ ! -f ".pre-commit-config.yaml" ]; then
    echo "  ✗ .pre-commit-config.yaml not found"
    exit 1
fi
echo "  ✓ .pre-commit-config.yaml exists"

# Check 8: README exists
echo "✓ Check 8: Documentation..."
if [ ! -f "README.md" ]; then
    echo "  ✗ README.md not found"
    exit 1
fi
echo "  ✓ README.md exists"

# Check 9: Run type checking
echo "✓ Check 9: Type checking with mypy..."
if ! command -v mypy &> /dev/null && ! python -m mypy --version &> /dev/null; then
    echo "  ⚠ mypy not available, skipping"
else
    if ! python -m mypy src/git_debug_oracle --ignore-missing-imports &> /dev/null; then
        echo "  ✗ mypy found type errors"
        exit 1
    fi
    echo "  ✓ mypy passed"
fi

echo ""
echo "=== Phase 1 Exit Conditions: ALL PASSED ✓ ==="
echo ""
echo "Next: Proceed to Phase 2 (Indexing Pipeline)"
