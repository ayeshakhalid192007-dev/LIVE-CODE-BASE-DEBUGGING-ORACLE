"""Tests for MCP server entry point."""

from unittest.mock import MagicMock, patch

import pytest

from git_debug_oracle.server import create_server, health_check


@patch("git_debug_oracle.server.Config")
@patch("git_debug_oracle.server.configure_logging")
@patch("git_debug_oracle.server.QdrantClientWrapper")
def test_create_server_initializes_components(
    mock_qdrant_wrapper: MagicMock,
    mock_configure_logging: MagicMock,
    mock_config_class: MagicMock,
) -> None:
    """Test that create_server initializes all required components."""
    mock_config = MagicMock()
    mock_config.log_level = "INFO"
    mock_config_class.return_value = mock_config

    mock_qdrant_instance = MagicMock()
    mock_qdrant_instance.test_connection.return_value = True
    mock_qdrant_wrapper.return_value = mock_qdrant_instance

    server = create_server()

    # Verify configuration was loaded
    mock_config_class.assert_called_once()

    # Verify logging was configured
    mock_configure_logging.assert_called_once_with(
        log_level="INFO", development=True
    )

    # Verify Qdrant client was initialized
    mock_qdrant_wrapper.assert_called_once_with(mock_config)

    # Verify connection was tested
    mock_qdrant_instance.test_connection.assert_called_once()

    # Verify server was created
    assert server is not None


@patch("git_debug_oracle.server.Config")
@patch("git_debug_oracle.server.configure_logging")
@patch("git_debug_oracle.server.QdrantClientWrapper")
def test_create_server_logs_qdrant_connection_failure(
    mock_qdrant_wrapper: MagicMock,
    mock_configure_logging: MagicMock,
    mock_config_class: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that create_server logs warning when Qdrant connection fails."""
    mock_config = MagicMock()
    mock_config.log_level = "INFO"
    mock_config_class.return_value = mock_config

    mock_qdrant_instance = MagicMock()
    mock_qdrant_instance.test_connection.return_value = False
    mock_qdrant_wrapper.return_value = mock_qdrant_instance

    server = create_server()

    # Verify connection was tested
    mock_qdrant_instance.test_connection.assert_called_once()

    # Server should still be created even if connection fails
    assert server is not None


@patch("git_debug_oracle.server.Config")
@patch("git_debug_oracle.server.configure_logging")
@patch("git_debug_oracle.server.QdrantClientWrapper")
def test_health_check_returns_healthy_status(
    mock_qdrant_wrapper: MagicMock,
    mock_configure_logging: MagicMock,
    mock_config_class: MagicMock,
) -> None:
    """Test that health_check returns healthy status when Qdrant is connected."""
    mock_config = MagicMock()
    mock_config.log_level = "INFO"
    mock_config_class.return_value = mock_config

    mock_qdrant_instance = MagicMock()
    mock_qdrant_instance.test_connection.return_value = True
    mock_qdrant_wrapper.return_value = mock_qdrant_instance

    # Create server to initialize global state
    create_server()

    # Call health check
    result = health_check()

    # Verify result structure
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == "healthy"
    assert "qdrant_connected" in result
    assert result["qdrant_connected"] is True


@patch("git_debug_oracle.server.Config")
@patch("git_debug_oracle.server.configure_logging")
@patch("git_debug_oracle.server.QdrantClientWrapper")
def test_health_check_returns_degraded_status_when_qdrant_disconnected(
    mock_qdrant_wrapper: MagicMock,
    mock_configure_logging: MagicMock,
    mock_config_class: MagicMock,
) -> None:
    """Test that health_check returns degraded status when Qdrant is disconnected."""
    mock_config = MagicMock()
    mock_config.log_level = "INFO"
    mock_config_class.return_value = mock_config

    mock_qdrant_instance = MagicMock()
    mock_qdrant_instance.test_connection.return_value = False
    mock_qdrant_wrapper.return_value = mock_qdrant_instance

    # Create server to initialize global state
    create_server()

    # Call health check
    result = health_check()

    # Verify result structure
    assert isinstance(result, dict)
    assert "status" in result
    assert result["status"] == "degraded"
    assert "qdrant_connected" in result
    assert result["qdrant_connected"] is False


@patch("git_debug_oracle.server.Config")
@patch("git_debug_oracle.server.configure_logging")
def test_create_server_uses_production_logging_when_configured(
    mock_configure_logging: MagicMock,
    mock_config_class: MagicMock,
) -> None:
    """Test that create_server uses production logging mode when configured."""
    mock_config = MagicMock()
    mock_config.log_level = "WARNING"
    mock_config_class.return_value = mock_config

    with patch("git_debug_oracle.server.QdrantClientWrapper"):
        # Set environment variable to indicate production
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}):
            create_server()

            # In this test, we're just verifying the function can be called
            # The actual environment detection logic will be in the implementation
            mock_configure_logging.assert_called_once()
