# Multi-stage build for git-debug-oracle MCP server
# Stage 1: Builder - Install dependencies and verify with tests
# Stage 2: Runtime - Minimal production image

# ============================================================================
# STAGE 1: BUILDER
# ============================================================================
FROM python:3.11-slim AS builder

LABEL maintainer="git-debug-oracle contributors"
LABEL description="Builder stage for git-debug-oracle"

# Set working directory
WORKDIR /build

# Install system dependencies needed for build
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install uv package manager
RUN pip install --no-cache-dir uv>=0.1.0

# Install all dependencies (including dev for testing)
RUN uv pip install --system -e .[dev] --no-cache-dir

# Run tests to verify build validity
RUN uv run pytest tests/ -q --tb=short --co -q > /dev/null && \
    uv run pytest tests/unit/ -q --tb=line -x

# Create a requirements file for runtime stage
RUN uv pip freeze > /tmp/requirements.txt

# ============================================================================
# STAGE 2: RUNTIME
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="git-debug-oracle contributors"
LABEL description="git-debug-oracle MCP server for live codebase debugging"
LABEL version="0.1.0"

# Set working directory
WORKDIR /app

# Install only runtime system dependencies (git for repo operations)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy application code from builder
COPY --from=builder /build/src/ ./src/
COPY --from=builder /build/pyproject.toml ./

# Copy only runtime dependencies from builder
COPY --from=builder /tmp/requirements.txt /tmp/requirements-all.txt

# Filter to only runtime dependencies (exclude dev/test packages)
RUN grep -v -E "pytest|ruff|mypy|pre-commit|black" /tmp/requirements-all.txt > /tmp/requirements.txt && \
    rm /tmp/requirements-all.txt

# Install runtime dependencies only
RUN pip install --no-cache-dir --upgrade pip setuptools && \
    pip install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# Create non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Default environment variables
ENV LOG_LEVEL=INFO
ENV QDRANT_HOST=qdrant
ENV QDRANT_PORT=6333
ENV WEBHOOK_PORT=8000
ENV PYTHONUNBUFFERED=1

# Entrypoint
ENTRYPOINT ["python", "-m", "git_debug_oracle.server"]

# Default command (can be overridden)
CMD []
