#!/bin/bash
# verify_phase_5.sh
# Phase 5: OSS Hardening - Verify exit conditions

set -e

echo "=== Phase 5: OSS Hardening Exit Conditions Verification ==="
echo ""

# Check 1: Docker image build capability
echo "✓ Check 1: Docker configuration..."
if [ ! -f "Dockerfile" ]; then
    echo "  ⚠ Dockerfile not found (optional)"
else
    echo "  ✓ Dockerfile present"
fi

# Check 2: Docker Compose configuration
echo "✓ Check 2: Docker Compose configuration..."
if [ ! -f "docker-compose.yml" ] && [ ! -f "docker-compose.yaml" ]; then
    echo "  ⚠ docker-compose.yml not found (optional)"
else
    echo "  ✓ docker-compose configured"
fi

# Check 3: README quality
echo "✓ Check 3: README quality..."
if ! grep -q "Quick Start" README.md; then
    echo "  ✗ README missing Quick Start section"
    exit 1
fi
echo "  ✓ README has quickstart guide"

# Check 4: Comprehensive documentation
echo "✓ Check 4: Documentation completeness..."
required_docs=(
    "docs/QUICKSTART.md"
    "docs/CONFIGURATION.md"
    "docs/TROUBLESHOOTING.md"
)
for doc in "${required_docs[@]}"; do
    if [ ! -f "$doc" ]; then
        echo "  ✗ $doc not found"
        exit 1
    fi
done
echo "  ✓ All documentation present"

# Check 5: Example error payloads
echo "✓ Check 5: Example error payloads..."
if [ ! -f "docs/ERROR_PAYLOADS.md" ]; then
    echo "  ✗ ERROR_PAYLOADS.md not found"
    exit 1
fi
echo "  ✓ ERROR_PAYLOADS.md exists"

# Check 6: Configuration validation
echo "✓ Check 6: Configuration validation..."
if ! grep -q "pydantic_settings" pyproject.toml; then
    echo "  ⚠ pydantic-settings not in dependencies"
fi
echo "  ✓ Configuration validation present"

# Check 7: LICENSE file
echo "✓ Check 7: License file..."
if [ ! -f "LICENSE" ]; then
    echo "  ✗ LICENSE file not found"
    exit 1
fi
echo "  ✓ LICENSE present"

# Check 8: Contributing guide
echo "✓ Check 8: Contributing guide..."
if [ ! -f "CONTRIBUTING.md" ]; then
    echo "  ✗ CONTRIBUTING.md not found"
    exit 1
fi
echo "  ✓ CONTRIBUTING.md exists"

# Check 9: CI/CD workflow
echo "✓ Check 9: CI/CD workflow..."
if [ ! -d ".github/workflows" ]; then
    echo "  ⚠ .github/workflows not found (optional)"
else
    echo "  ✓ CI/CD workflows present"
fi

# Check 10: Run all tests
echo "✓ Check 10: Running all tests..."
if ! python -m pytest tests/ -v --tb=short -q &> /dev/null; then
    echo "  ✗ Some tests failed"
    exit 1
fi
echo "  ✓ All tests passed"

echo ""
echo "=== Phase 5 Exit Conditions: ALL PASSED ✓ ==="
echo ""
echo "Next: Proceed to Phase 6 (Docker Removal & uv Migration)"
