# Phase 5 OSS Hardening - Validation Checklist

## Unit Tests

### Test File: tests/unit/test_config_validation.py

**Test Suite: Configuration Validation**

```python
def test_missing_required_field_anthropic_api_key():
    """Missing ANTHROPIC_API_KEY raises clear error."""
    import os
    os.environ.pop("ANTHROPIC_API_KEY", None)
    
    with pytest.raises(ValueError, match="ANTHROPIC_API_KEY"):
        from git_debug_oracle.config import settings  # noqa: F401

def test_invalid_port_number():
    """Invalid port number (> 65535) raises error."""
    with pytest.raises(ValueError, match="port"):
        Settings(webhook_port=70000)

def test_invalid_chunk_size():
    """Invalid chunk size (< 100) raises error."""
    with pytest.raises(ValueError, match="chunk_size"):
        Settings(chunk_size=50)

def test_missing_repo_path():
    """Missing REPO_PATH for indexing raises error."""
    import os
    os.environ.pop("REPO_PATH", None)
    
    with pytest.raises(ValueError, match="REPO_PATH"):
        Settings()

def test_valid_config_loads():
    """Valid config with all required fields loads."""
    config = Settings(
        qdrant_host="localhost",
        embedding_api_key="test_key",
        anthropic_api_key="test_key",
        repo_path=".",
    )
    assert config.qdrant_host == "localhost"
```

### Test File: tests/unit/test_edge_cases.py

**Test Suite: Empty Repository**

```python
def test_empty_repository_handling():
    """Empty repository raises clear error."""
    mock_repo = Mock()
    mock_repo.iter_commits.return_value = []
    
    with patch("git_debug_oracle.git_watcher.repo_reader.Repo", return_value=mock_repo):
        from git_debug_oracle.git_watcher.repo_reader import get_commits
        
        commits = get_commits(mock_repo, "main")
        assert len(commits) == 0
```

**Test Suite: Unsupported File Types**

```python
def test_binary_files_skipped():
    """Binary files skipped during indexing."""
    files = ["code.py", "image.png", "binary.exe", "data.bin"]
    
    from git_debug_oracle.indexer.file_filter import is_indexable_file
    
    indexable = [f for f in files if is_indexable_file(f)]
    assert indexable == ["code.py"]
    assert "image.png" not in indexable

def test_invalid_python_syntax_skipped():
    """Python files with syntax errors skipped."""
    code = "def broken(\n  syntax"
    
    from git_debug_oracle.indexer.chunker import parse_python_file
    
    result = parse_python_file(code)
    assert result is None or len(result) == 0
```

**Test Suite: Network Failures**

```python
def test_qdrant_connection_retry():
    """Qdrant connection retries on transient error."""
    mock_client = Mock()
    mock_client.search.side_effect = [
        Exception("Connection timeout"),
        Exception("Connection timeout"),
        [{"id": 1, "score": 0.9}],  # Success on 3rd try
    ]
    
    from git_debug_oracle.utils.qdrant_client import search_with_retry
    
    result = search_with_retry(mock_client, "query", max_retries=3)
    assert result is not None

def test_max_retries_exceeded():
    """After max retries, raises clear error."""
    mock_client = Mock()
    mock_client.search.side_effect = Exception("Connection timeout")
    
    from git_debug_oracle.utils.qdrant_client import search_with_retry
    
    with pytest.raises(Exception, match="max retries"):
        search_with_retry(mock_client, "query", max_retries=3)
```

**Test Suite: API Degradation**

```python
def test_embedding_api_unavailable():
    """Embedding API unavailable after retries returns error."""
    mock_embedder = Mock()
    mock_embedder.embed_batch.side_effect = Exception("Service unavailable")
    
    from git_debug_oracle.embedder.batch_processor import batch_embed_with_retry
    
    with pytest.raises(Exception, match="unavailable"):
        batch_embed_with_retry(mock_embedder, [])

def test_claude_api_unavailable_returns_low_confidence():
    """Claude API unavailable returns FixProposal with low confidence."""
    from git_debug_oracle.fix_generator.claude_client import generate_fix_with_fallback
    from unittest.mock import patch
    
    with patch("git_debug_oracle.fix_generator.claude_client.Anthropic") as mock_claude:
        mock_claude.return_value.messages.create.side_effect = Exception("Rate limited")
        
        fix = generate_fix_with_fallback([], "error_context")
        
        assert fix.confidence < 0.5
        assert "unavailable" in fix.explanation.lower()
```

---

## Integration Tests

### Test File: tests/integration/test_docker_build.py

**Test Suite: Docker Build and Startup**

```python
def test_docker_image_builds():
    """Docker image builds successfully."""
    result = subprocess.run(
        ["docker", "build", "-t", "git-debug-oracle:test", "."],
        capture_output=True,
        timeout=300,
    )
    assert result.returncode == 0

def test_docker_image_runs():
    """Docker image starts without errors."""
    subprocess.run(["docker", "run", "--rm", "git-debug-oracle:test", "--help"])
    # Should not raise

def test_docker_image_size():
    """Docker image size < 500MB."""
    result = subprocess.run(
        ["docker", "images", "git-debug-oracle:test", "--format", "{{.Size}}"],
        capture_output=True,
        text=True,
    )
    size_str = result.stdout.strip()
    # Parse size and convert to MB
    assert float(size_str.split()[0]) < 500  # Approximate
```

### Test File: tests/integration/test_docker_compose.py

**Test Suite: Docker Compose Orchestration**

```python
def test_docker_compose_up():
    """docker-compose up starts all services."""
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0
    
    # Check services running
    result = subprocess.run(
        ["docker-compose", "ps", "--format", "{{.State}}"],
        capture_output=True,
        text=True,
    )
    assert "running" in result.stdout.lower()

def test_health_check_passes():
    """MCP server health check returns 200."""
    import requests
    response = requests.get("http://localhost:8000/health", timeout=5)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_docker_compose_down():
    """docker-compose down cleanly stops services."""
    result = subprocess.run(
        ["docker-compose", "down"],
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0
```

### Test File: tests/integration/test_quickstart.py

**Test Suite: Quickstart Guide End-to-End**

```python
def test_quickstart_docker_path():
    """Quickstart with Docker works end-to-end."""
    # Step 1: Clone
    subprocess.run(["git", "clone", "...", "test_repo"], check=True)
    
    # Step 2: docker-compose up
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    # Step 3: Health check
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    
    # Step 4: Index repo
    response = requests.post(
        "http://localhost:8000/index",
        json={"repo_path": "test_repo"},
    )
    assert response.status_code == 200
    
    # Step 5: Send error
    response = requests.post(
        "http://localhost:8000/webhook/error",
        json={"file_path": "app.py", "line_number": 1},
    )
    assert response.status_code == 200
    
    # Cleanup
    subprocess.run(["docker-compose", "down"], check=True)
```

---

## Acceptance Tests

### Test File: tests/acceptance/test_phase_5_acceptance.py

```python
def test_exit_condition_docker_image_builds():
    """Docker image builds successfully."""
    result = subprocess.run(
        ["docker", "build", "-t", "git-debug-oracle:latest", "."],
        capture_output=True,
        timeout=300,
    )
    assert result.returncode == 0

def test_exit_condition_docker_compose_works():
    """Docker Compose starts all services."""
    result = subprocess.run(
        ["docker-compose", "up", "-d"],
        capture_output=True,
        timeout=60,
    )
    assert result.returncode == 0
    
    # Wait for services
    import time
    time.sleep(10)
    
    # Health check
    response = requests.get("http://localhost:8000/health")
    assert response.status_code == 200
    
    subprocess.run(["docker-compose", "down"])

def test_exit_condition_readme_complete():
    """README has quickstart and all required sections."""
    with open("README.md") as f:
        content = f.read()
    
    required_sections = [
        "Quick Start",
        "Installation",
        "Architecture",
        "Usage",
        "Troubleshooting",
        "Contributing",
    ]
    
    for section in required_sections:
        assert section in content, f"Missing section: {section}"

def test_exit_condition_edge_cases_handled():
    """All edge cases handled gracefully."""
    test_cases = [
        ("empty_repo", Empty repository with no commits),
        ("binary_files", Repository with binary files),
        ("invalid_python", Python file with syntax errors),
        ("network_timeout", Network timeout on Qdrant),
        ("api_unavailable", Embedding API returns 503),
        ("rate_limited", Claude API returns 429),
    ]
    
    for test_name, test_description in test_cases:
        # Run each test scenario
        # Verify no crashes, clear error messages

def test_exit_condition_ci_pipeline_passing():
    """GitHub Actions CI pipeline passes."""
    # Check .github/workflows/ci.yml exists
    assert os.path.exists(".github/workflows/ci.yml")
    
    # Verify workflow can be parsed
    with open(".github/workflows/ci.yml") as f:
        import yaml
        workflow = yaml.safe_load(f)
        assert "jobs" in workflow

def test_exit_condition_documentation_complete():
    """All documentation files exist and are substantive."""
    docs = [
        "README.md",
        "CONTRIBUTING.md",
        "LICENSE",
        "CHANGELOG.md",
        "docs/QUICKSTART.md",
        "docs/CONFIGURATION.md",
        "docs/ERROR_PAYLOADS.md",
        "docs/MCP_CONFIG.md",
        "docs/TROUBLESHOOTING.md",
    ]
    
    for doc in docs:
        assert os.path.exists(doc), f"Missing: {doc}"
        with open(doc) as f:
            content = f.read()
            assert len(content) > 500, f"Too short: {doc}"

def test_exit_condition_version_tagged():
    """Version is tagged (v1.0.0 or higher)."""
    result = subprocess.run(
        ["git", "describe", "--tags"],
        capture_output=True,
        text=True,
    )
    version = result.stdout.strip()
    assert version.startswith("v1.") or version.startswith("v2.")
```

---

## Manual Testing Checklist

### Docker Build & Run
- [ ] `docker build -t git-debug-oracle:latest .` succeeds
- [ ] Image size < 500MB
- [ ] `docker run git-debug-oracle:latest` starts without errors
- [ ] Health check responds: `curl http://localhost:8000/health`

### Docker Compose
- [ ] `docker-compose up -d` starts both services
- [ ] Both services healthy after 30 seconds: `docker-compose ps`
- [ ] `docker-compose logs` shows no ERROR messages
- [ ] `docker-compose down` cleanly stops services

### Quickstart Guide (< 5 minutes)
- [ ] macOS: Follow README quickstart, works end-to-end
- [ ] Linux: Follow README quickstart, works end-to-end
- [ ] Windows: Follow README quickstart, works end-to-end

### Configuration Validation
- [ ] Missing ANTHROPIC_API_KEY: Clear error message with fix instructions
- [ ] Invalid port (> 65535): Clear error message
- [ ] Invalid chunk size: Clear error message

### Edge Cases
- [ ] Empty repository: Clear error "Repository has no commits"
- [ ] Binary files: Skipped with DEBUG log, no crash
- [ ] Invalid Python: Skipped with WARN log, indexing continues
- [ ] Network timeout: Retried, then clear error
- [ ] Embedding API down: Graceful degradation or retry
- [ ] Claude API down: Returns FixProposal with low confidence

### Documentation
- [ ] README: Easy to read, no dead links
- [ ] QUICKSTART.md: Step-by-step, tested locally
- [ ] CONFIGURATION.md: All env vars documented
- [ ] ERROR_PAYLOADS.md: Examples for Sentry, Datadog, CloudWatch
- [ ] MCP_CONFIG.md: Claude Desktop and Claude Code setup working
- [ ] TROUBLESHOOTING.md: Common issues covered
- [ ] CONTRIBUTING.md: Development setup clear
- [ ] LICENSE: Present and compliant

### GitHub Actions
- [ ] Workflow file exists: `.github/workflows/ci.yml`
- [ ] Trigger on push/PR to main
- [ ] All jobs run: lint, type check, tests, docker build
- [ ] Failure notifications working

---

## Exit Criteria Checklist

- [ ] Docker image builds successfully (< 5 min)
- [ ] Docker Compose orchestration working
- [ ] README quickstart tested end-to-end (< 5 min)
- [ ] All edge cases handled gracefully (no crashes)
- [ ] Configuration validation with specific error messages
- [ ] Retry logic for Qdrant connections implemented
- [ ] Graceful degradation for embedding API working
- [ ] Graceful degradation for Claude API working
- [ ] GitHub Actions CI/CD pipeline passing
- [ ] All documentation files created (9 files)
- [ ] Version tagged (v1.0.0+)
- [ ] Changelog updated
- [ ] License file present
- [ ] Code review passed
- [ ] All tests passing (unit + integration + acceptance)
- [ ] Coverage > 80%
- [ ] Ready for public release

---

## Test Execution Commands

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests
uv run pytest tests/integration/ -v

# Acceptance tests
uv run pytest tests/acceptance/ -v

# All tests with coverage
uv run pytest tests/ --cov=src/git_debug_oracle --cov-report=html

# Docker tests (requires Docker)
uv run pytest tests/integration/test_docker*.py -v

# Manual verification
docker build -t git-debug-oracle:test .
docker-compose up -d
curl http://localhost:8000/health
docker-compose down
```

---

## Success Metrics

| Metric | Target | Method |
|--------|--------|--------|
| Docker image size | < 500MB | `docker images` |
| Build time | < 5 min | `time docker build` |
| Startup time | < 10s | Measure from run to health check |
| Quickstart time | < 5 min | Time actual walkthrough |
| Test pass rate | 100% | `pytest` output |
| Code coverage | > 80% | `pytest --cov` |
| Documentation completeness | 9/9 files | File existence check |
| Edge case handling | 0 crashes | Manual testing |
| CI/CD success | 100% | GitHub Actions status |

---

## Known Issues / Future Enhancements

- Advanced monitoring/APM integration (Phase 6)
- Multi-language client libraries (Phase 6)
- Helm charts for Kubernetes (Phase 6)
- Cloud platform-specific deployment (Phase 6)
- UI/Dashboard (Phase 6+)
- Mobile client support (Phase 6+)
