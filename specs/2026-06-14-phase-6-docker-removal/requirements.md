# Phase 6: Docker Removal - Requirements

## Functional Requirements

### FR1: File System Cleanup
**Description:** Remove all Docker-related files and directories.

**Requirements:**
- Delete `Dockerfile`
- Delete `docker-compose.yml`
- Delete `docker/` directory and contents
- Delete any Docker-related scripts (e.g., `get-docker.sh`)
- Delete any `.dockerignore` if present

**Acceptance Criteria:**
- No Docker files exist in repo
- `find . -name "*docker*" -o -name "*Docker*"` returns nothing
- `find . -name "Dockerfile"` returns nothing

### FR2: Configuration File Updates
**Description:** Update configuration files to reflect pip-only deployment.

**Requirements:**
- `pyproject.toml`: Remove any Docker build configurations
- `.env.example`: Verify no Docker-specific environment variables; keep Qdrant config
- Remove any docker-compose-specific env files

**Acceptance Criteria:**
- `pyproject.toml` is valid TOML
- `.env.example` has clear comments for local Qdrant setup
- No references to Docker in config files

### FR3: README Update
**Description:** Rewrite README to remove Docker, emphasize pip/uv.

**Requirements:**
- Quick Start section:
  - Prerequisites: Python 3.11+, uv, local Qdrant instance
  - Remove Docker/Docker Compose from prerequisites
  - Add step: "Set up Qdrant locally (see Qdrant Setup section)"
  - Show only: `uv install` → `uv run python -m git_debug_oracle.server`
- Installation section:
  - Remove Docker installation method
  - Keep: pip/uv from source, pip from GitHub
- Add new section: "Qdrant Setup" explaining user options:
  - Local Docker: `docker run -p 6333:6333 qdrant/qdrant:latest`
  - Cloud: Qdrant Cloud account
  - Local Python: `pip install qdrant-client` with local mode
- Remove any references to `docker-compose up`

**Acceptance Criteria:**
- Quickstart takes < 5 minutes without Docker
- All commands tested
- Qdrant setup clearly explained as user responsibility
- No Docker references remain

### FR4: Architecture Documentation Update
**Description:** Update architecture docs to remove Docker references.

**Requirements:**
- `specs/architecture.md`: Remove "Docker image via docker-compose" section
- Remove "MCP config registration via Docker" if present
- Update "Deployment" section to describe pip-only
- Add note on Qdrant setup: "Qdrant runs independently; users configure QDRANT_HOST and QDRANT_PORT"

**Acceptance Criteria:**
- No Docker references in architecture.md
- Deployment section accurate for pip-only
- Qdrant configuration clearly described

### FR5: Tech Stack Documentation Update
**Description:** Update tech stack to remove Docker.

**Requirements:**
- `specs/tech-stack.md`: Remove "Docker image via docker-compose" from Packaging section
- Add note under "Environment Variables" Qdrant section:
  - "Qdrant must be deployed separately. Users can run: docker run -p 6333:6333 qdrant/qdrant:latest or use Qdrant Cloud."
- Update any Docker-related configuration items

**Acceptance Criteria:**
- Tech stack valid and complete
- No Docker requirements listed
- Qdrant setup guidance present

### FR6: Git Cleanup
**Description:** Remove Docker files from git index and commit.

**Requirements:**
- Stage deletions: `git add -A` or specific file deletions
- Commit with message: `chore: remove docker and docker-compose, migrate to pip-only`
- Verify deletion in git log

**Acceptance Criteria:**
- Files deleted from repo
- Commit message follows conventional commits
- No accidental files deleted

## Non-Functional Requirements

### NFR1: Completeness
- All Docker references removed from code, config, docs, and git
- No dangling Docker commands in examples

### NFR2: Backward Compatibility
- No breaking changes to core functionality
- Existing code continues to work via pip

### NFR3: Documentation Clarity
- New users can set up Qdrant and project without Docker knowledge
- Error messages clear if Qdrant is not available

## Acceptance Criteria (Overall)

Phase 6 complete when:
1. ✅ All Docker files deleted
2. ✅ No Docker references in code/docs
3. ✅ README quickstart works with pip/uv only
4. ✅ Qdrant setup documented as user responsibility
5. ✅ All documentation updated
6. ✅ Git history cleaned
7. ✅ Tests pass
8. ✅ Code review passed
