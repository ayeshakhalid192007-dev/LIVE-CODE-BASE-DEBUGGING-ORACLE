# Phase 1 Foundation - Requirements

## Functional Requirements

### FR1: Directory Structure
- src/git_debug_oracle/ package with 8 subpackages
- tests/ with unit/, integration/, fixtures/
- docker/ with qdrant/ subdirectory
- docs/ for documentation

### FR2: Python Packaging
- pyproject.toml with project metadata
- All dependencies pinned per specs/tech-stack.md
- Package installable via uv pip install -e .
- Entry point: git_debug_oracle.server:main

### FR3: Configuration
- .env.example documenting all 18 environment variables
- Each variable documented with type, required/optional, default, description

### FR4: Development Tooling
- .gitignore excluding Python artifacts and secrets
- .pre-commit-config.yaml with ruff and mypy hooks
- Hooks enforceable via pre-commit install

### FR5: Docker Setup
- docker-compose.yml with Qdrant service
- Ports: 6333 (gRPC), 6334 (HTTP)
- Volume mount for persistence
- Health check configured

### FR6: Documentation
- README.md with installation instructions
- Development setup instructions
- MCP registration placeholder

## Non-Functional Requirements

### NFR1: Version Pinning
All dependencies must match versions in specs/tech-stack.md exactly.

### NFR2: Constitutional Compliance
- Phase directory created before implementation
- uv as sole package manager
- No direct pip commands

### NFR3: Immutability
Phase directory files (plan.md, requirements.md, validation.md) are immutable during implementation.
