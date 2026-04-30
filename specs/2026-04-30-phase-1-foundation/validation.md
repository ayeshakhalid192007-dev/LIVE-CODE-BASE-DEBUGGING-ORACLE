# Phase 1 Foundation - Validation Checklist

## Test Cases

### TC1: Directory Structure
```bash
ls -R src/ tests/ docker/ docs/
```
**Expected:** All directories and __init__.py files present

### TC2: Package Installation
```bash
uv pip install -e .
```
**Expected:** Installation succeeds, no errors

### TC3: Dependency Pinning
```bash
grep -E "mcp|qdrant-client|GitPython" pyproject.toml
```
**Expected:** All dependencies have version constraints matching tech-stack.md

### TC4: Docker Compose
```bash
docker-compose up -d
docker-compose ps
```
**Expected:** Qdrant container running, healthy

### TC5: Pre-commit Hooks
```bash
pre-commit install
pre-commit run --all-files
```
**Expected:** Hooks installed, no errors

### TC6: Git Ignore
```bash
touch .env
git status
```
**Expected:** .env not shown in untracked files

### TC7: Package Import
```bash
uv run python -c "import git_debug_oracle; print(git_debug_oracle.__version__)"
```
**Expected:** Prints "0.1.0"

### TC8: Type Checking
```bash
uv run mypy src/
```
**Expected:** Success (no type errors)

### TC9: README Readable
```bash
cat README.md
```
**Expected:** All sections present, installation instructions clear

### TC10: Phase Directory Exists
```bash
ls specs/2026-04-30-phase-1-foundation/
```
**Expected:** plan.md, requirements.md, validation.md exist

## Acceptance Criteria

- [ ] All 10 test cases pass
- [ ] No constitutional violations
- [ ] All files created per plan
- [ ] Ready for Task Group 2 (Configuration System)
