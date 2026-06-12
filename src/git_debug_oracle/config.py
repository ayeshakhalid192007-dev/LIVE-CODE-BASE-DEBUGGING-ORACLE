"""Configuration loading and validation using pydantic-settings."""

from enum import Enum
from pathlib import Path
from typing import Any, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class EmbeddingModel(str, Enum):
    """Supported embedding models."""

    VOYAGE_CODE_2 = "voyage-code-2"
    TEXT_EMBEDDING_3_SMALL = "text-embedding-3-small"


class LogLevel(str, Enum):
    """Supported log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


class Config(BaseSettings):
    """Application configuration loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Qdrant configuration
    qdrant_host: str = Field(
        ...,
        description="Hostname or IP address of Qdrant server",
    )
    qdrant_port: int = Field(
        default=6333,
        description="Port number for Qdrant gRPC API",
        ge=1,
        le=65535,
    )
    qdrant_collection: str = Field(
        default="git_debug_oracle",
        description="Name of Qdrant collection to store code chunks",
    )
    qdrant_api_key: Optional[str] = Field(
        default=None,
        description="API key for Qdrant Cloud (not needed for local Docker instance)",
    )

    # Embedding configuration
    embedding_model: EmbeddingModel = Field(
        default=EmbeddingModel.VOYAGE_CODE_2,
        description="Which embedding model to use for code chunks",
    )
    embedding_api_key: str = Field(
        ...,
        description="API key for embedding provider (Voyage AI or OpenAI)",
    )

    # Claude API configuration
    anthropic_api_key: str = Field(
        ...,
        description="API key for Claude API to generate fix proposals",
    )
    claude_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Claude model to use for fix generation",
    )

    # Repository configuration
    repo_path: str = Field(
        ...,
        description="Absolute path to Git repository to index",
    )
    watch_branch: str = Field(
        default="main",
        description="Git branch to watch for new commits during incremental indexing",
    )

    # Webhook configuration
    webhook_secret: Optional[str] = Field(
        default=None,
        description="Shared secret for validating webhook requests (if None, no validation)",
    )
    webhook_port: int = Field(
        default=8000,
        description="Port number for FastAPI webhook server",
        ge=1,
        le=65535,
    )

    # Chunking configuration
    chunk_size: int = Field(
        default=1000,
        description="Maximum number of characters per code chunk",
        ge=100,
        le=10000,
    )
    chunk_overlap: int = Field(
        default=200,
        description="Number of overlapping characters between adjacent chunks",
        ge=0,
        le=1000,
    )

    # Retrieval configuration
    top_k: int = Field(
        default=5,
        description="Number of top results to retrieve from Qdrant for each query",
        ge=1,
        le=100,
    )
    recent_commit_window: int = Field(
        default=30,
        description="Number of days to consider a commit 'recent' for recency weighting",
        ge=1,
        le=365,
    )
    max_context_chunks: int = Field(
        default=10,
        description="Maximum number of code chunks to include in fix generation context",
        ge=1,
        le=50,
    )

    # Logging configuration
    log_level: LogLevel = Field(
        default=LogLevel.INFO,
        description="Minimum log level to output",
    )

    @field_validator("repo_path")
    @classmethod
    def validate_repo_path(cls, v: str) -> str:
        """Validate that repo_path is an absolute path."""
        path = Path(v)
        if not path.is_absolute():
            raise ValueError(
                f"REPO_PATH must be an absolute path, got: {v}\n"
                f"Example: /home/user/my-repo or /Users/user/my-repo"
            )
        return v

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v: int, info: Any) -> int:
        """Validate that chunk_overlap is less than chunk_size."""
        chunk_size = info.data.get("chunk_size", 1000)
        if v >= chunk_size:
            raise ValueError(
                f"CHUNK_OVERLAP ({v}) must be less than CHUNK_SIZE ({chunk_size})"
            )
        return v


_settings_instance: Optional[Config] = None


def get_settings() -> Config:
    """Get or create settings instance (lazy loading to avoid validation on import)."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Config()
    return _settings_instance


# For backwards compatibility, provide settings as a module-level object
# that behaves like Config but uses lazy loading
class SettingsProxy:
    """Proxy to settings instance that lazy-loads on first access."""

    def __getattr__(self, name: str) -> Any:
        return getattr(get_settings(), name)


settings = SettingsProxy()  # type: ignore
