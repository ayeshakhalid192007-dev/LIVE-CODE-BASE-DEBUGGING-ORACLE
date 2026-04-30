"""Tests for configuration loading and validation."""

import os
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from git_debug_oracle.config import Config, EmbeddingModel, LogLevel


def test_config_missing_required_qdrant_host(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing QDRANT_HOST raises ValidationError."""
    monkeypatch.delenv("QDRANT_HOST", raising=False)
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "qdrant_host" in error_msg.lower()
    assert "field required" in error_msg.lower()


def test_config_missing_required_embedding_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing EMBEDDING_API_KEY raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "embedding_api_key" in error_msg.lower()
    assert "field required" in error_msg.lower()


def test_config_missing_required_anthropic_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing ANTHROPIC_API_KEY raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "anthropic_api_key" in error_msg.lower()
    assert "field required" in error_msg.lower()


def test_config_missing_required_repo_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that missing REPO_PATH raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("REPO_PATH", raising=False)

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "repo_path" in error_msg.lower()
    assert "field required" in error_msg.lower()


def test_config_invalid_qdrant_port_type(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that invalid QDRANT_PORT type raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "not-a-number")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "qdrant_port" in error_msg.lower()


def test_config_invalid_qdrant_port_range(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that QDRANT_PORT outside valid range raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "99999")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "qdrant_port" in error_msg.lower()


def test_config_invalid_embedding_model(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that invalid EMBEDDING_MODEL raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("EMBEDDING_MODEL", "invalid-model")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "embedding_model" in error_msg.lower()


def test_config_invalid_log_level(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that invalid LOG_LEVEL raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("LOG_LEVEL", "INVALID")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "log_level" in error_msg.lower()


def test_config_relative_repo_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that relative REPO_PATH raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "relative/path")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "repo_path" in error_msg.lower()
    assert "absolute path" in error_msg.lower()


def test_config_chunk_overlap_greater_than_chunk_size(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that CHUNK_OVERLAP >= CHUNK_SIZE raises ValidationError."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")
    monkeypatch.setenv("CHUNK_SIZE", "500")
    monkeypatch.setenv("CHUNK_OVERLAP", "500")

    with pytest.raises(ValidationError) as exc_info:
        Config()

    error_msg = str(exc_info.value)
    assert "chunk_overlap" in error_msg.lower()
    assert "less than" in error_msg.lower()


def test_config_valid_minimal(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that valid minimal configuration loads successfully."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-embedding-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("REPO_PATH", "/home/user/repo")

    config = Config()

    assert config.qdrant_host == "localhost"
    assert config.qdrant_port == 6333
    assert config.qdrant_collection == "git_debug_oracle"
    assert config.qdrant_api_key is None
    assert config.embedding_model == EmbeddingModel.VOYAGE_CODE_2
    assert config.embedding_api_key == "test-embedding-key"
    assert config.anthropic_api_key == "test-anthropic-key"
    assert config.claude_model == "claude-sonnet-4-20250514"
    assert config.repo_path == "/home/user/repo"
    assert config.watch_branch == "main"
    assert config.webhook_secret is None
    assert config.webhook_port == 8000
    assert config.chunk_size == 1000
    assert config.chunk_overlap == 200
    assert config.top_k == 5
    assert config.recent_commit_window == 30
    assert config.max_context_chunks == 10
    assert config.log_level == LogLevel.INFO


def test_config_valid_all_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that configuration with all fields set loads successfully."""
    monkeypatch.setenv("QDRANT_HOST", "qdrant.example.com")
    monkeypatch.setenv("QDRANT_PORT", "6334")
    monkeypatch.setenv("QDRANT_COLLECTION", "custom_collection")
    monkeypatch.setenv("QDRANT_API_KEY", "qdrant-key")
    monkeypatch.setenv("EMBEDDING_MODEL", "text-embedding-3-small")
    monkeypatch.setenv("EMBEDDING_API_KEY", "openai-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "claude-key")
    monkeypatch.setenv("CLAUDE_MODEL", "claude-opus-4-20250514")
    monkeypatch.setenv("REPO_PATH", "/var/repos/myproject")
    monkeypatch.setenv("WATCH_BRANCH", "develop")
    monkeypatch.setenv("WEBHOOK_SECRET", "secret123")
    monkeypatch.setenv("WEBHOOK_PORT", "9000")
    monkeypatch.setenv("CHUNK_SIZE", "1500")
    monkeypatch.setenv("CHUNK_OVERLAP", "300")
    monkeypatch.setenv("TOP_K", "10")
    monkeypatch.setenv("RECENT_COMMIT_WINDOW", "60")
    monkeypatch.setenv("MAX_CONTEXT_CHUNKS", "20")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")

    config = Config()

    assert config.qdrant_host == "qdrant.example.com"
    assert config.qdrant_port == 6334
    assert config.qdrant_collection == "custom_collection"
    assert config.qdrant_api_key == "qdrant-key"
    assert config.embedding_model == EmbeddingModel.TEXT_EMBEDDING_3_SMALL
    assert config.embedding_api_key == "openai-key"
    assert config.anthropic_api_key == "claude-key"
    assert config.claude_model == "claude-opus-4-20250514"
    assert config.repo_path == "/var/repos/myproject"
    assert config.watch_branch == "develop"
    assert config.webhook_secret == "secret123"
    assert config.webhook_port == 9000
    assert config.chunk_size == 1500
    assert config.chunk_overlap == 300
    assert config.top_k == 10
    assert config.recent_commit_window == 60
    assert config.max_context_chunks == 20
    assert config.log_level == LogLevel.DEBUG


def test_config_loads_from_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that configuration loads from .env file."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
QDRANT_HOST=localhost
EMBEDDING_API_KEY=test-key
ANTHROPIC_API_KEY=test-key
REPO_PATH=/absolute/path
CHUNK_SIZE=2000
"""
    )

    monkeypatch.chdir(tmp_path)

    config = Config()

    assert config.qdrant_host == "localhost"
    assert config.embedding_api_key == "test-key"
    assert config.anthropic_api_key == "test-key"
    assert config.repo_path == "/absolute/path"
    assert config.chunk_size == 2000


def test_config_env_vars_override_env_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that environment variables override .env file values."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        """
QDRANT_HOST=localhost
EMBEDDING_API_KEY=file-key
ANTHROPIC_API_KEY=file-key
REPO_PATH=/file/path
"""
    )

    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("EMBEDDING_API_KEY", "env-key")

    config = Config()

    assert config.qdrant_host == "localhost"
    assert config.embedding_api_key == "env-key"
    assert config.anthropic_api_key == "file-key"
    assert config.repo_path == "/file/path"
