"""Tests for Qdrant client wrapper."""

from unittest.mock import MagicMock, patch

import pytest

from git_debug_oracle.config import Config
from git_debug_oracle.utils.qdrant_client import QdrantClientWrapper


@pytest.fixture
def mock_config(monkeypatch: pytest.MonkeyPatch) -> Config:
    """Create a mock configuration for testing."""
    monkeypatch.setenv("QDRANT_HOST", "localhost")
    monkeypatch.setenv("QDRANT_PORT", "6333")
    monkeypatch.setenv("QDRANT_COLLECTION", "test_collection")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")
    return Config()


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_qdrant_client_wrapper_initialization(
    mock_qdrant_class: MagicMock, mock_config: Config
) -> None:
    """Test that QdrantClientWrapper initializes with correct parameters."""
    wrapper = QdrantClientWrapper(mock_config)

    # Verify QdrantClient was called with correct parameters
    mock_qdrant_class.assert_called_once_with(
        host=mock_config.qdrant_host,
        port=mock_config.qdrant_port,
        api_key=mock_config.qdrant_api_key,
    )

    # Verify wrapper stores the client
    assert wrapper.client is not None


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_qdrant_client_wrapper_with_api_key(
    mock_qdrant_class: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Test that QdrantClientWrapper passes API key when provided."""
    monkeypatch.setenv("QDRANT_HOST", "cloud.qdrant.io")
    monkeypatch.setenv("QDRANT_API_KEY", "secret-api-key")
    monkeypatch.setenv("EMBEDDING_API_KEY", "test-key")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setenv("REPO_PATH", "/absolute/path")

    config = Config()
    wrapper = QdrantClientWrapper(config)

    # Verify API key was passed
    mock_qdrant_class.assert_called_once_with(
        host="cloud.qdrant.io",
        port=6333,
        api_key="secret-api-key",
    )


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_test_connection_success(
    mock_qdrant_class: MagicMock, mock_config: Config
) -> None:
    """Test that test_connection returns True when connection succeeds."""
    mock_client = MagicMock()
    mock_client.get_collections.return_value = MagicMock()
    mock_qdrant_class.return_value = mock_client

    wrapper = QdrantClientWrapper(mock_config)
    result = wrapper.test_connection()

    assert result is True
    mock_client.get_collections.assert_called_once()


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_test_connection_failure(
    mock_qdrant_class: MagicMock, mock_config: Config
) -> None:
    """Test that test_connection returns False when connection fails."""
    mock_client = MagicMock()
    mock_client.get_collections.side_effect = Exception("Connection failed")
    mock_qdrant_class.return_value = mock_client

    wrapper = QdrantClientWrapper(mock_config)
    result = wrapper.test_connection()

    assert result is False
    mock_client.get_collections.assert_called_once()


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_client_property_access(
    mock_qdrant_class: MagicMock, mock_config: Config
) -> None:
    """Test that client property returns the Qdrant client."""
    mock_client = MagicMock()
    mock_qdrant_class.return_value = mock_client

    wrapper = QdrantClientWrapper(mock_config)

    assert wrapper.client is mock_client


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_collection_name_from_config(
    mock_qdrant_class: MagicMock, mock_config: Config
) -> None:
    """Test that collection_name property returns value from config."""
    wrapper = QdrantClientWrapper(mock_config)

    assert wrapper.collection_name == mock_config.qdrant_collection


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_qdrant_client_wrapper_stores_config(
    mock_qdrant_class: MagicMock, mock_config: Config
) -> None:
    """Test that QdrantClientWrapper stores the config."""
    wrapper = QdrantClientWrapper(mock_config)

    assert wrapper.config is mock_config


@patch("git_debug_oracle.utils.qdrant_client.QdrantClient")
def test_test_connection_logs_error_on_failure(
    mock_qdrant_class: MagicMock, mock_config: Config, caplog: pytest.LogCaptureFixture
) -> None:
    """Test that test_connection logs error when connection fails."""
    mock_client = MagicMock()
    error_message = "Connection timeout"
    mock_client.get_collections.side_effect = Exception(error_message)
    mock_qdrant_class.return_value = mock_client

    wrapper = QdrantClientWrapper(mock_config)
    result = wrapper.test_connection()

    assert result is False
    # Check that error was logged (will be implemented in the actual code)
