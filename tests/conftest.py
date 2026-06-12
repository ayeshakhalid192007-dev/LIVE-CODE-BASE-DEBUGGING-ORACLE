"""Pytest configuration and fixtures for all tests."""

import pytest
import os


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Provide required environment variables for all tests.

    Skips for config tests that need to test env var loading behavior.
    """
    # Skip for config-specific tests
    if "test_config" in request.node.nodeid:
        return

    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/tmp/test-repo")
    # Don't set WEBHOOK_SECRET for tests - allows dev mode (no signature validation)


