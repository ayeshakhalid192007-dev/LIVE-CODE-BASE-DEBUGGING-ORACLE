# Multi-stage build for git-debug-oracle MCP server
# Build stage: install dependencies, run tests
# Runtime stage: minimal Python image with only runtime dependencies

# ============================================================================
# Build Stage
# ============================================================================
FROM python:3.11-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY tests/ ./tests/

# Install uv and dependencies
RUN pip install uv && uv pip install -e ".[dev]"

# Run tests to verify build validity
RUN uv run pytest tests/ -v --cov=git_debug_oracle --cov-report=term-missing

# ============================================================================
# Runtime Stage
# ============================================================================
FROM python:3.11-slim

LABEL maintainer="git-debug-oracle contributors"
LABEL description="Live codebase debugging with vector search and Claude"
LABEL version="1.0.0"

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy only runtime dependencies and source from builder
COPY --from=builder /build/src/ ./src/
COPY --from=builder /build/pyproject.toml ./
COPY --from=builder /build/uv.lock ./

# Install uv and runtime dependencies only (no dev)
RUN pip install uv && uv pip install -e .

# Create non-root user for security
RUN useradd -m -u 1000 oracle && chown -R oracle:oracle /app
USER oracle

# Health check
HEALTHCHECK --interval=10s --timeout=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=2)" || exit 1

# Expose MCP server port
EXPOSE 8000

# Run MCP server
ENTRYPOINT ["python", "-m", "git_debug_oracle.server"]
