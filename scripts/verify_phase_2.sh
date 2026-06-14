#!/bin/bash
# verify_phase_2.sh
# Phase 2: Indexing Pipeline - Verify exit conditions

set -e

echo "=== Phase 2: Indexing Pipeline Exit Conditions Verification ==="
echo ""

# Check 1: Indexer module structure
echo "✓ Check 1: Indexer module structure..."
required_files=(
    "src/git_debug_oracle/indexer/chunker.py"
    "src/git_debug_oracle/indexer/file_filter.py"
    "src/git_debug_oracle/indexer/metadata.py"
    "src/git_debug_oracle/indexer/pipeline.py"
)
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo "  ✗ $file not found"
        exit 1
    fi
done
echo "  ✓ All indexer files present"

# Check 2: Git watcher module
echo "✓ Check 2: Git watcher module..."
if [ ! -f "src/git_debug_oracle/git_watcher/repo_reader.py" ]; then
    echo "  ✗ repo_reader.py not found"
    exit 1
fi
echo "  ✓ repo_reader.py exists"

# Check 3: Embedder module
echo "✓ Check 3: Embedder module..."
if [ ! -f "src/git_debug_oracle/embedder/batch_processor.py" ]; then
    echo "  ✗ batch_processor.py not found"
    exit 1
fi
echo "  ✓ batch_processor.py exists"

# Check 4: MCP tool: index_repo
echo "✓ Check 4: MCP tool index_repo..."
if [ ! -f "src/git_debug_oracle/mcp_tools/index_repo.py" ]; then
    echo "  ✗ index_repo.py not found"
    exit 1
fi
echo "  ✓ index_repo.py exists"

# Check 5: Unit tests for indexing
echo "✓ Check 5: Unit tests..."
required_tests=(
    "tests/unit/test_chunker.py"
    "tests/unit/test_file_filter.py"
    "tests/unit/test_metadata.py"
)
for test in "${required_tests[@]}"; do
    if [ ! -f "$test" ]; then
        echo "  ✗ $test not found"
        exit 1
    fi
done
echo "  ✓ All unit tests present"

# Check 6: Integration tests
echo "✓ Check 6: Integration tests..."
if [ ! -f "tests/integration/test_indexing_pipeline.py" ]; then
    echo "  ✗ test_indexing_pipeline.py not found"
    exit 1
fi
echo "  ✓ test_indexing_pipeline.py exists"

# Check 7: Run tests
echo "✓ Check 7: Running tests..."
if ! python -m pytest tests/unit/test_chunker.py -v --tb=short &> /dev/null; then
    echo "  ✗ Chunker tests failed"
    exit 1
fi
echo "  ✓ Tests passed"

echo ""
echo "=== Phase 2 Exit Conditions: ALL PASSED ✓ ==="
echo ""
echo "Next: Proceed to Phase 3 (Retrieval and Error Ingestion)"
