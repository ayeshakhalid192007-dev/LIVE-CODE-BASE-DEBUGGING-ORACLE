"""Pytest configuration and fixtures for all tests."""

import pytest
import os
import shutil
from pathlib import Path


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest) -> None:
    """Provide required environment variables for all tests.

    For config tests, temporarily move .env file to prevent it from being loaded.
    """
    # For config-specific tests, hide the .env file
    if "test_config" in request.node.nodeid:
        # Find .env relative to this conftest.py file
        project_root = Path(__file__).parent.parent
        env_path = project_root / ".env"
        backup_path = project_root / ".env.backup"

        env_existed = env_path.exists()
        try:
            if env_existed:
                shutil.move(str(env_path), str(backup_path))

            def restore_env_file() -> None:
                if backup_path.exists():
                    shutil.move(str(backup_path), str(env_path))

            request.addfinalizer(restore_env_file)
        except Exception:
            # Ensure backup is restored even if setup fails
            if backup_path.exists():
                shutil.move(str(backup_path), str(env_path))
            raise

        return

    # For other tests, provide default env vars
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/tmp/test-repo")


@pytest.fixture(autouse=True)
def reset_config_instance(request: pytest.FixtureRequest) -> None:
    """Reset the global Config instance before each test."""
    if "test_config" in request.node.nodeid:
        import git_debug_oracle.config as config_module

        config_module._settings_instance = None








