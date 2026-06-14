# Phase 6: Docker Removal - Validation Checklist

## File System Validation

- [ ] `Dockerfile` deleted
- [ ] `docker-compose.yml` deleted
- [ ] `docker/` directory deleted
- [ ] `get-docker.sh` deleted (if existed)
- [ ] `.dockerignore` deleted (if existed)
- [ ] `find . -name "*docker*" -o -name "*Docker*"` returns no results

## Configuration Validation

- [ ] `pyproject.toml` valid TOML
- [ ] `pyproject.toml` builds successfully: `uv build`
- [ ] `.env.example` has Qdrant config documented
- [ ] No Docker environment variables in `.env.example`

## README Validation

- [ ] Prerequisites section mentions Python 3.11+, uv, local Qdrant
- [ ] Quick Start quickstart section does NOT mention Docker
- [ ] Quick Start section shows: `uv install` → `uv run python -m git_debug_oracle.server`
- [ ] Quick Start section < 5 minutes to execute
- [ ] "Qdrant Setup" section exists with user options
- [ ] All commands in README tested to work
- [ ] No "docker" or "Docker" strings in README (except in Qdrant setup as user option)

## Documentation Validation

- [ ] `specs/architecture.md` has no Docker references
- [ ] `specs/architecture.md` Deployment section describes pip-only
- [ ] `specs/tech-stack.md` has no Docker in Packaging section
- [ ] `specs/tech-stack.md` Qdrant section notes user responsibility
- [ ] All doc links are valid

## Code Validation

- [ ] No Docker references in source code
- [ ] `grep -r "docker" src/ tests/` returns no results (case-insensitive)
- [ ] `grep -r "compose" src/ tests/` returns no results

## Functional Testing

- [ ] `uv install` succeeds
- [ ] `uv pip install -e .` succeeds
- [ ] `uv run python -m git_debug_oracle.server` starts (requires Qdrant running)
- [ ] Server validates config and shows errors if ANTHROPIC_API_KEY missing
- [ ] No crashes on startup

## Git Validation

- [ ] Docker files deleted from git: `git status` shows deletions
- [ ] Commit created with conventional message
- [ ] Commit message follows: `chore: remove docker and docker-compose, migrate to pip-only`
- [ ] No accidental files in commit
- [ ] `git log --oneline` shows new commit

## Code Review Validation

- [ ] Code review passed with no blocking issues
- [ ] All changes align with project constitution
- [ ] No regressions in existing functionality

## Final Sign-Off

- [ ] All checklist items completed
- [ ] Phase 6 ready for merge
- [ ] Commit URL reported
