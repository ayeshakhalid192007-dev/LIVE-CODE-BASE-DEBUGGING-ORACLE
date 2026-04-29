# Mission Specification

## Why This Exists

Runtime errors in evolving codebases force developers into a manual investigation loop: copy stacktrace, grep for file paths, open multiple files, scan recent commits, cross-reference diffs, reconstruct what changed, hypothesize root cause, propose fix. This loop burns 15-45 minutes per error. When errors arrive in production or during rapid development, this delay compounds.

git-debug-oracle eliminates this loop. It indexes your repository incrementally as you commit, embeds code at function granularity, stores it with commit metadata in a vector database, and when an error arrives, retrieves the exact diffs and code context that caused it, then generates a fix with full reasoning trace using Claude. Investigation time drops from minutes to seconds.

## Target Audience

**Solo developers with fast-moving repositories**
Developers working alone on projects with frequent commits who need instant error diagnosis without context-switching to manual git archaeology.

**Backend engineers debugging production errors**
Engineers receiving stacktraces from production logs or monitoring systems who need to map runtime failures back to recent code changes immediately.

**OSS maintainers reviewing contributor-introduced regressions**
Maintainers who merge external PRs and need to quickly diagnose whether a new error originated from a recent contribution and which specific change caused it.

**Teams using Claude Code as their primary development agent**
Development teams who have Claude Code in their workflow and want it to have instant access to error context without manual file gathering or explanation.

**Developers working in monorepos with high commit velocity**
Engineers in large codebases where tracking which recent change broke what is difficult due to volume and parallel work streams.

## Core Goals

**Index only changed files on each commit, never the full repo**
After initial indexing, only files modified in new commits are re-embedded and upserted. Unchanged code is never re-processed. This keeps indexing fast and resource-efficient even in large repositories.

**Retrieve relevant code context within top-3 results for any error with a valid stacktrace**
Vector search must surface the function or file that caused the error in the top 3 retrieved chunks at least 90% of the time when the error includes file and line information.

**Propose a fix with a traceable reasoning chain, not just a code suggestion**
Every fix must include: root cause analysis, which commit introduced the issue, what the code was trying to do, why it failed, and what the fix changes. No "try this" suggestions without explanation.

**Support webhook-based error ingestion from any monitoring or logging system**
Accept error payloads via HTTP POST from any source: application logs, Sentry, Datadog, CloudWatch, custom monitoring. Parse stacktrace and metadata regardless of format.

**Maintain commit recency weighting so recent changes rank higher than old code**
When two chunks match a query equally, the one from a more recent commit ranks higher. Errors are more likely caused by recent changes than code written months ago.

**Expose all functionality via MCP tools so Claude Code can use it directly**
Every operation — indexing, error debugging, code search, diff retrieval, status checks — is an MCP tool. No CLI-only features. Claude Code is the primary interface.

**Run entirely locally with no external dependencies except embedding and LLM APIs**
The server, vector database, and Git watcher run on the developer's machine or in their infrastructure. No data leaves their environment except API calls to embedding and Claude APIs, which can be self-hosted if needed.

## Non-Goals

**This project will NOT be a general-purpose code search tool**
It is optimized for error-driven retrieval, not arbitrary code exploration. Use grep, ripgrep, or a dedicated code search tool for that.

**This project will NOT replace a test suite**
It diagnoses errors after they occur. It does not prevent them. Write tests. This tool helps you fix what breaks despite tests.

**This project will NOT support non-Git version control systems in v1**
Git only. No Mercurial, SVN, Perforce, or Fossil support. Git is the target. Other VCS support is a future consideration, not a v1 requirement.

**This project will NOT provide a web UI for browsing indexed code**
It is an MCP server, not a web application. All interaction happens through MCP tools called by Claude Code or other MCP clients. No dashboard, no frontend.

**This project will NOT attempt to fix errors automatically without human review**
It proposes fixes. It does not apply them. The developer reviews the proposal and decides whether to accept, modify, or reject it. No auto-commit, no auto-deploy.

**This project will NOT index non-code files like images, binaries, or large data files**
Only text files that contain code are indexed. Binary files, media assets, and data files are ignored. This keeps the index clean and retrieval relevant.

**This project will NOT support real-time code analysis or linting**
It indexes committed code, not unsaved buffers or dirty working trees. Linting and real-time analysis are the job of LSP servers and editor plugins.

## Design Principles

**Incremental over full — never re-index what has not changed**
Every indexing operation checks what changed since the last indexed commit. Only modified, added, or deleted files are processed. Full re-indexing is a manual operation, not a default behavior.

**Retrieval must be fast enough to feel instant — under 500ms from query to results**
Vector search, metadata filtering, and result ranking must complete in under half a second. Developers will not wait. If retrieval is slow, they will grep instead.

**Commit metadata is first-class — every chunk knows its origin**
Every embedded chunk stores: commit hash, author, timestamp, file path, function name, line range. Retrieval results include this metadata so the developer knows exactly where the code came from.

**Errors are structured data, not free text — parse them, do not guess**
Stacktraces have structure: file paths, line numbers, function names, error types. Extract this structure and use it to construct precise retrieval queries. Do not rely on fuzzy text matching alone.

**Configuration must fail fast with clear errors — no silent defaults for required values**
If a required environment variable is missing, the server refuses to start and prints exactly what is missing and where to set it. No "falling back to default" for critical config like API keys or repo paths.

**Every operation must be observable — log what you do, when, and how long it took**
Indexing, retrieval, embedding generation, fix generation, and errors are all logged with timestamps and durations. Developers need to see what the system is doing, especially when it is slow or failing.

**Dependencies must be pinned and minimal — no framework sprawl**
Every dependency must justify its inclusion. Prefer standard library over third-party when possible. Pin major versions. Avoid frameworks that pull in 50 transitive dependencies.

## Success Criteria

**Technical Benchmarks**

**Retrieval accuracy: 90%+ top-3 hit rate for errors with stacktraces**
Given 100 real errors from a test repository with known root causes, retrieval must return the correct file and function in the top 3 results for at least 90 of them.

**Indexing speed: under 2 seconds per 1000 lines of changed code**
Incremental indexing of a commit that modifies 1000 lines of code (additions + deletions) must complete embedding generation and Qdrant upsert in under 2 seconds on a standard development machine.

**Retrieval latency: under 500ms from error payload to retrieval results**
From the moment an error payload is received to the moment retrieval results are returned, no more than 500ms may elapse, excluding fix generation time.

**Fix generation quality: root cause identified in 80%+ of cases**
When a fix is generated, it must correctly identify the root cause (the specific code change that introduced the error) in at least 80% of test cases, as judged by a human reviewer.

**Adoption Benchmarks**

**Time to first indexed repo: under 5 minutes from clone to indexed**
A developer clones the project, follows the README quickstart, and has their first repository fully indexed in under 5 minutes, including Docker setup and initial indexing.

**MCP tool registration: works on first try in Claude Code and Claude Desktop**
Following the README instructions to add the MCP server to `claude_desktop_config.json` or Claude Code config results in the tools appearing and being callable without debugging or troubleshooting.

**Error-to-fix workflow: under 30 seconds from error to proposed fix**
A developer pastes an error into Claude Code, Claude calls the `debug_error` tool, and a fix proposal with reasoning is returned in under 30 seconds, including retrieval and Claude API call time.

**Documentation completeness: a new user can run the full workflow without asking questions**
The README and inline documentation are sufficient for a developer unfamiliar with the project to install it, index a repo, send an error, and receive a fix without needing to ask for help or read source code.
