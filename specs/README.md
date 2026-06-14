# Specifications

Design documents and phase execution plans for Git Debug Oracle.

---

## Core Specifications

- **[mission.md](mission.md)** — Why this project exists, target audience, core goals, success criteria
- **[roadmap.md](roadmap.md)** — Phase breakdown, entry/exit conditions, deliverables
- **[architecture.md](architecture.md)** — System design, data flow, component organization
- **[tech-stack.md](tech-stack.md)** — Technology choices, rationale, dependency versions

---

## Phase Structure

Project is organized into 6 phases, each with:
- **plan.md** — Implementation steps, file changes, task breakdown
- **requirements.md** — Detailed requirements, acceptance criteria
- **validation.md** — Exit conditions, test cases, verification checklist

### Phase 1: Foundation (2026-04-30)
**Status:** Complete ✓

Establish runnable project skeleton with configuration, Qdrant connection, basic MCP server.

**Exit Conditions Met:**
- Docker Compose starts Qdrant successfully
- MCP server runs and connects to Qdrant
- Health check tool returns success
- All configuration validation tests pass
- mypy reports no type errors

### Phase 2: Indexing Pipeline (2026-05-23)
**Status:** Complete ✓

Implement full repository indexing with Git reading, function-level chunking, embedding generation, Qdrant upsert.

**Exit Conditions Met:**
- `index_repo` completes without errors
- Qdrant collection contains chunks with correct metadata
- `index_incremental` indexes only changed files
- Indexing 1000 lines completes in under 2 seconds
- All unit tests pass
- Integration test verifies chunk count

### Phase 3: Retrieval and Error Ingestion (2026-06-10)
**Status:** Complete ✓

Accept error payloads via webhook, parse stacktraces, construct queries, return relevant code chunks.

**Exit Conditions Met:**
- Webhook endpoint accepts error payloads
- `debug_error` returns correct file in top 3 results
- Retrieval completes in under 500ms
- Recency weighting ranks recent commits higher
- All stacktrace parsers handle valid input
- Integration test achieves 90%+ top-3 hit rate

### Phase 4: Fix Generation & MCP Tool Contracts (2026-06-13)
**Status:** Complete ✓

Integrate Claude API for fix proposals, finalize MCP tool contracts, stabilize schemas.

**Exit Conditions Met:**
- `debug_error` returns FixProposal with all fields
- Fix proposals include root cause analysis in 80%+ of cases
- Claude API calls use prompt caching
- All MCP tools have stable schemas
- Error-to-fix workflow completes in under 30 seconds
- Integration test verifies fix quality on 10 known bugs

### Phase 5: OSS Hardening (2026-06-13)
**Status:** Complete ✓

Prepare for public release: Docker distribution, comprehensive docs, robust error handling, edge cases.

**Exit Conditions Met:**
- README quickstart gets user indexed in under 5 minutes
- Docker Compose works on macOS, Linux, Windows
- All edge cases handled without crashes
- CI pipeline passes on main branch
- Project ready for public release
- 3+ external users successfully install and run

### Phase 6: Docker Removal & Migration to uv (2026-06-14)
**Status:** Complete ✓

Remove Docker dependency, migrate to uv-only setup for simpler deployment.

**Exit Conditions Met:**
- Docker Compose removed from required setup
- All Docker references removed from docs
- Qdrant deployed via uv or Docker Desktop
- Setup simplified for developers
- Tests pass without Docker
- All documentation updated

---

## Reading These Specs

**New to the project?**
- Start with [mission.md](mission.md) to understand the problem
- Read [roadmap.md](roadmap.md) for high-level phases
- Check individual phase directories for current work

**Implementing a phase?**
- Read phase `plan.md` for tasks and file structure
- Check `requirements.md` for acceptance criteria
- Verify `validation.md` exit conditions before marking complete

**Modifying architecture?**
- Read [architecture.md](architecture.md) for system design
- Check [tech-stack.md](tech-stack.md) for technology rationale
- Update relevant docs if architecture changes

---

## Phase Exit Conditions

All phases use the same validation pattern:

**Each phase defines:**
1. Entry conditions (what must be true to start)
2. Deliverables (what will be built)
3. Exit conditions (verification checklist)

**Before merging to main:**
- All exit conditions in phase `validation.md` must be true
- Integration tests must pass
- Code review must pass
- No blocking issues remain

---

## Current Status

```
Phase 1: Foundation           ✓ Complete
Phase 2: Indexing Pipeline   ✓ Complete
Phase 3: Retrieval & Errors  ✓ Complete
Phase 4: Fix Generation      ✓ Complete
Phase 5: OSS Hardening       ✓ Complete
Phase 6: Docker Removal      ✓ Complete

Project Status: MVP Ready for Use ✓
```

All core functionality implemented and tested. Project is ready for production use.

---

## Contributing

See [../CONTRIBUTING.md](../CONTRIBUTING.md) for:
- Development setup
- How to work with phases
- Git workflow
- Code standards

---

## Questions?

- Confused about phase structure? Read [roadmap.md](roadmap.md)
- Want to understand technical design? Read [architecture.md](architecture.md)
- Need to know why we chose specific tech? Read [tech-stack.md](tech-stack.md)
