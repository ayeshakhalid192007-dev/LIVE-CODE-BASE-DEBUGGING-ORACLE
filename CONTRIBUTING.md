# Contributing Guide

Thank you for interest in contributing to git-debug-oracle! This guide explains how to set up for development and contribute.

## Development Setup

### 1. Clone and install

```bash
git clone https://github.com/ayeshakhalid192007-dev/LIVE-CODE-BASE-DEBUGGING-ORACLE.git
cd LIVE-CODE-BASE-DEBUGGING-ORACLE
```

### 2. Install dependencies

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv pip install -e ".[dev]"
```

### 3. Install pre-commit hooks

```bash
pre-commit install
```

Hooks run automatically before every commit:
- `ruff` — Linting and formatting
- `mypy` — Type checking

### 4. Start Qdrant for testing

```bash
docker-compose up -d qdrant
```

## Development Workflow

### Creating a branch

Use one of three branch types:

```bash
# Feature: New functionality within a phase
git checkout -b phase/5-feature-name

# Fix: Bug fix or correction
git checkout -b fix/bug-description

# Replan: Refactoring or architectural change
git checkout -b replan/refactor-name
```

### Making commits

Follow conventional commit format:

```bash
git commit -m "type: subject

body explaining what and why, not how."
```

**Types:** `feat`, `fix`, `docs`, `test`, `refactor`, `chore`

**Example:**
```bash
git commit -m "feat: implement Qdrant retry logic with exponential backoff

Adds exponential backoff retry strategy for transient Qdrant failures.
Retries on connection timeout, network errors, and 5xx responses.
Max 5 attempts with 1s, 2s, 4s, 8s delays plus jitter.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

### Running tests

```bash
# All tests
uv run pytest tests/ -v

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# With coverage report
uv run pytest tests/ --cov=src/git_debug_oracle --cov-report=html
```

### Type checking

```bash
uv run mypy src/
```

### Linting and formatting

```bash
# Check
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/
```

## Code Standards

All code must follow these rules (see CLAUDE.md for full details):

### Type Annotations

Every function must have complete type annotations:

```python
# ✓ Correct
def process_chunk(chunk: CodeChunk, size: int) -> str:
    pass

# ✗ Wrong (missing return type)
def process_chunk(chunk: CodeChunk, size: int):
    pass
```

### Function Responsibility

Each function does one thing only:

```python
# ✓ Correct - single responsibility
def extract_function_name(tree: ast.AST) -> str:
    pass

# ✗ Wrong - too many responsibilities
def parse_and_chunk_and_embed(code: str) -> list[str]:
    pass
```

### No Magic Values

Named constants for all magic values:

```python
# ✓ Correct
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# ✗ Wrong
if retries < 3:  # What does 3 mean?
    time.sleep(30)
```

### Documentation

Public functions must have docstrings:

```python
def search_codebase(query: str, top_k: int = 5) -> list[RetrievalResult]:
    """Search indexed code chunks for relevant matches.
    
    Args:
        query: Search query text
        top_k: Number of top results to return
        
    Returns:
        List of retrieval results ranked by relevance
    """
```

## Testing Requirements

### Write tests before code

TDD (Test-Driven Development) workflow:

```bash
# 1. Write failing test
uv run pytest tests/unit/test_feature.py::test_new_feature -v

# 2. Implement feature (test passes)
# 3. Run all tests to ensure no regression
uv run pytest tests/ -v
```

### Coverage target

Aim for > 80% code coverage:

```bash
uv run pytest tests/ --cov=src/git_debug_oracle --cov-report=html
open htmlcov/index.html
```

### Test naming

Descriptive test names that explain what is tested:

```python
# ✓ Correct
def test_retry_logic_succeeds_on_third_attempt():
    pass

# ✗ Wrong
def test_retry():
    pass
```

## Code Review Process

### Before pushing

1. Run tests: `uv run pytest tests/ -v`
2. Type check: `uv run mypy src/`
3. Lint: `uv run ruff check src/`
4. Format: `uv run ruff format src/ tests/`
5. Pre-commit hooks should pass automatically

### Creating a pull request

```bash
# Push branch
git push -u origin phase/5-your-feature

# Create PR using gh command or GitHub web interface
gh pr create \
  --title "Short description of change" \
  --body "Explanation of what changed and why"
```

### PR description template

```markdown
## Summary
Brief explanation of the change

## Changes
- Bullet point 1
- Bullet point 2

## Testing
- [ ] Unit tests added
- [ ] Integration tests pass
- [ ] Manual testing done

## Checklist
- [ ] Code follows standards
- [ ] Tests pass
- [ ] Documentation updated
```

## Common Tasks

### Adding a new MCP tool

1. Create implementation in `src/git_debug_oracle/mcp_tools/`
2. Add tests in `tests/unit/test_mcp_*.py`
3. Register in `src/git_debug_oracle/server.py`
4. Document in `docs/MCP_CONFIG.md`

### Adding a new error parser

1. Implement parser in `src/git_debug_oracle/error_ingestion/stacktrace.py`
2. Add tests in `tests/unit/test_stacktrace_*.py`
3. Document in `docs/ERROR_PAYLOADS.md`

### Updating documentation

1. Edit file in `docs/` or `README.md`
2. Test examples work
3. Check for broken links
4. Commit with `docs:` type

## Resources

- **Architecture:** `specs/architecture.md`
- **Roadmap:** `specs/roadmap.md`
- **API Docs:** Generated from docstrings
- **Code style:** Follow Python PEP 8 (enforced by ruff)

## Getting Help

- **Questions?** Open a GitHub issue with label `question`
- **Bug report?** Open issue with label `bug` and include:
  - Error message and logs
  - Steps to reproduce
  - System info (OS, Python version, Docker version)
- **Feature request?** Open issue with label `enhancement` and explain use case

## Recognition

All contributions are tracked in git history. Commits include co-author lines:

```
Co-Authored-By: Your Name <your.email@example.com>
```

Thank you for contributing!
