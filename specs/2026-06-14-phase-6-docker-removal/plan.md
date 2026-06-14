# Phase 6: Docker Removal - Implementation Plan

## Overview
Remove Docker and Docker Compose entirely from the project. Migrate all deployment to pip/uv-only with local Qdrant setup.

## Tasks

### 1. File Deletion
- Delete `Dockerfile`
- Delete `docker-compose.yml`
- Delete `docker/` directory entirely
- Delete `get-docker.sh` (if Docker helper script)

### 2. Configuration Updates
- Update `pyproject.toml`: Remove Docker-related build config if present
- Update `.env.example`: Remove Docker-specific vars (if any), keep Qdrant vars

### 3. README Update
- Remove Docker section entirely
- Update quickstart to show pip/uv only
- Update prerequisites (remove Docker, Docker Compose)
- Add local Qdrant setup instructions (user responsibility)
- Update example commands to use `uv run python -m git_debug_oracle.server`

### 4. Architecture Docs Update
- Update `specs/architecture.md` Deployment section
- Remove Docker references
- Add local Qdrant setup guidance

### 5. Tech Stack Update
- Update `specs/tech-stack.md` to remove Docker references
- Add note: "Qdrant deployment is user responsibility (local Docker, cloud, or local Python instance)"

### 6. Testing
- Verify pip install works: `uv pip install -e .`
- Verify server starts: `uv run python -m git_debug_oracle.server`
- Verify help with ANTHROPIC_API_KEY missing shows proper error

## Success Criteria
- All Docker files deleted
- No Docker references in code or docs
- Pip/uv installation tested and working
- README quickstart works without Docker
- Server runs and validates config properly
