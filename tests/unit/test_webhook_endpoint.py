"""Tests for webhook endpoint."""

import json
import hmac
import hashlib
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

from git_debug_oracle.webhook.app import app


client = TestClient(app)


class TestWebhookEndpoint:
    """POST /webhook/error endpoint."""

    def test_webhook_valid_payload(self) -> None:
        """Valid error payload returns 200 with results."""
        payload = {
            "file_path": "src/app.py",
            "line_number": 42,
            "function_name": "process_data",
            "error_type": "ValueError",
            "error_message": "invalid input",
        }

        with patch("git_debug_oracle.webhook.app.search_qdrant", return_value=[]):
            with patch("git_debug_oracle.webhook.app.get_commit_diffs", return_value=[]):
                response = client.post("/webhook/error", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert "retrieval_results" in data
                assert "error_context" in data

    def test_webhook_missing_required_field(self) -> None:
        """Missing required field returns 400."""
        payload = {"line_number": 42}  # missing file_path
        response = client.post("/webhook/error", json=payload)
        assert response.status_code == 400

    def test_webhook_invalid_json(self) -> None:
        """Invalid JSON returns 400."""
        response = client.post(
            "/webhook/error",
            content="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

    def test_webhook_signature_valid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Valid HMAC signature passes validation."""
        payload = {"file_path": "app.py", "line_number": 1}
        json_str = json.dumps(payload)
        json_bytes = json_str.encode()

        # Set webhook secret for this test only
        monkeypatch.setenv("WEBHOOK_SECRET", "test_secret")

        # Restart settings to pick up new env var
        from git_debug_oracle.config import _settings_instance
        import git_debug_oracle.config
        git_debug_oracle.config._settings_instance = None

        signature = "sha256=" + hmac.new(
            b"test_secret",
            json_bytes,
            hashlib.sha256,
        ).hexdigest()

        with patch("git_debug_oracle.webhook.app.search_qdrant", return_value=[]):
            with patch("git_debug_oracle.webhook.app.get_commit_diffs", return_value=[]):
                response = client.post(
                    "/webhook/error",
                    content=json_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "X-Webhook-Signature": signature,
                    },
                )
                assert response.status_code == 200

    def test_webhook_signature_invalid(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Invalid HMAC signature returns 401."""
        payload = {"file_path": "app.py", "line_number": 1}

        # Set webhook secret for this test only
        monkeypatch.setenv("WEBHOOK_SECRET", "test_secret")

        # Restart settings to pick up new env var
        import git_debug_oracle.config
        git_debug_oracle.config._settings_instance = None

        response = client.post(
            "/webhook/error",
            json=payload,
            headers={"X-Webhook-Signature": "sha256=invalid"},
        )
        assert response.status_code == 401

    def test_webhook_response_structure(self) -> None:
        """Response has correct JSON structure."""
        payload = {"file_path": "app.py", "line_number": 1}

        with patch("git_debug_oracle.webhook.app.search_qdrant", return_value=[]):
            with patch("git_debug_oracle.webhook.app.get_commit_diffs", return_value=[]):
                response = client.post("/webhook/error", json=payload)

                data = response.json()
                assert "error_context" in data
                assert "retrieval_results" in data
                assert "related_diffs" in data
                assert "metadata" in data

    def test_health_check(self) -> None:
        """Health check endpoint responds."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
