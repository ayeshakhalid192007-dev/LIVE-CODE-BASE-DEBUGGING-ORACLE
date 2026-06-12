"""FastAPI webhook endpoint for error ingestion."""

import hashlib
import hmac
import json
import time
from typing import Any

from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from git_debug_oracle.config import settings
from git_debug_oracle.error_ingestion.parsers import parse_error_payload
from git_debug_oracle.retriever.query_constructor import construct_query
from git_debug_oracle.retriever.qdrant_retriever import search_qdrant
from git_debug_oracle.retriever.git_diff_retriever import get_commit_diffs
from git_debug_oracle.retriever.result_formatter import format_results


class ErrorPayloadRequest(BaseModel):
    """Error payload from monitoring system."""

    file_path: str
    line_number: int
    function_name: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    stacktrace: str | list[str] | None = None
    language: str | None = None


app = FastAPI(title="Git Debug Oracle", version="0.1.0")


def validate_webhook_signature(payload: bytes, signature: str | None) -> bool:
    """Validate HMAC-SHA256 webhook signature.

    Args:
        payload: Raw request body bytes
        signature: X-Webhook-Signature header value (sha256=hex)

    Returns:
        True if signature valid or WEBHOOK_SECRET not set (dev mode)
    """
    # If no secret configured, skip validation (dev mode)
    if not settings.webhook_secret:
        return True

    # If signature not provided but secret is set, reject
    if not signature:
        return False

    try:
        # Parse signature format: "sha256=hexdigest"
        if not signature.startswith("sha256="):
            return False

        provided_digest = signature[7:]  # Remove "sha256=" prefix

        # Compute expected signature
        expected_digest = hmac.new(
            settings.webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()

        # Constant-time comparison to prevent timing attacks
        return hmac.compare_digest(expected_digest, provided_digest)

    except Exception:
        return False


@app.post("/webhook/error")
async def webhook_error(request: Request) -> dict[str, Any]:
    """Accept error payload and return retrieval results.

    Endpoint: POST /webhook/error
    Content-Type: application/json

    Args:
        request: FastAPI Request object

    Returns:
        JSON object with error_context, retrieval_results, related_diffs, metadata

    Raises:
        HTTPException 400: Invalid payload
        HTTPException 401: Invalid signature
        HTTPException 500: Server error
    """
    try:
        # Get raw body for signature validation
        body = await request.body()

        # Validate signature
        signature = request.headers.get("X-Webhook-Signature")
        if not validate_webhook_signature(body, signature):
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Parse JSON payload
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")

        # Parse and validate error payload
        try:
            error_context = parse_error_payload(payload)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Construct query
        query = construct_query(error_context)

        # Search Qdrant
        start_time = time.time()
        retrieval_results = search_qdrant(
            query,
            error_context,
            top_k=settings.top_k,
        )
        search_duration_ms = (time.time() - start_time) * 1000

        # Fetch related diffs
        commit_hashes = [r.commit_hash for r in retrieval_results]
        related_diffs = get_commit_diffs(
            commit_hashes,
            settings.repo_path,
        )

        # Format response
        response = format_results(
            retrieval_results,
            related_diffs,
            error_context,
            search_duration_ms=search_duration_ms,
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.webhook_port,
    )
