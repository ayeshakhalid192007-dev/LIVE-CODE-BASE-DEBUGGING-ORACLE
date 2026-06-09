"""Unit tests for embedder/openai_client.py."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from git_debug_oracle.embedder.openai_client import OpenAIEmbedder


@pytest.fixture
def mock_openai_client() -> Mock:
    """Create a mock OpenAI client.

    Returns:
        Mock OpenAI client
    """
    return MagicMock()


@pytest.fixture
def openai_embedder(mock_openai_client: Mock) -> OpenAIEmbedder:
    """Create an OpenAIEmbedder with mocked client.

    Args:
        mock_openai_client: Mock OpenAI client

    Returns:
        OpenAIEmbedder instance
    """
    with patch("git_debug_oracle.embedder.openai_client.OpenAI") as mock_client_class:
        mock_client_class.return_value = mock_openai_client
        embedder = OpenAIEmbedder(api_key="test_key")
    return embedder


def test_openai_embedder_initialization(mock_openai_client: Mock) -> None:
    """Test OpenAIEmbedder initializes with correct model."""
    with patch("git_debug_oracle.embedder.openai_client.OpenAI") as mock_client_class:
        mock_client_class.return_value = mock_openai_client
        embedder = OpenAIEmbedder(api_key="test_key")

    assert embedder.model == "text-embedding-3-small"
    mock_client_class.assert_called_once_with(api_key="test_key")


def test_openai_embedder_embed_batch_success(openai_embedder: OpenAIEmbedder) -> None:
    """Test embed_batch successfully embeds texts."""
    texts = ["def hello(): pass", "def goodbye(): pass"]

    mock_embedding_1 = [0.1] * 1536
    mock_embedding_2 = [0.2] * 1536

    mock_response = Mock()
    mock_response.data = [
        Mock(embedding=mock_embedding_1),
        Mock(embedding=mock_embedding_2),
    ]

    openai_embedder.client.embeddings.create.return_value = mock_response

    embeddings = openai_embedder.embed_batch(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == mock_embedding_1
    assert embeddings[1] == mock_embedding_2
    openai_embedder.client.embeddings.create.assert_called_once()


def test_openai_embedder_embed_batch_empty_list(openai_embedder: OpenAIEmbedder) -> None:
    """Test embed_batch handles empty text list."""
    embeddings = openai_embedder.embed_batch([])

    assert embeddings == []
    openai_embedder.client.embeddings.create.assert_not_called()


def test_openai_embedder_embed_batch_retry_on_failure(
    openai_embedder: OpenAIEmbedder,
) -> None:
    """Test embed_batch retries on failure."""
    texts = ["def hello(): pass"]

    mock_embedding = [0.1] * 1536
    mock_response = Mock()
    mock_response.data = [Mock(embedding=mock_embedding)]

    openai_embedder.client.embeddings.create.side_effect = [
        Exception("Network error"),
        Exception("Rate limit exceeded"),
        mock_response,
    ]

    with patch("git_debug_oracle.embedder.openai_client.time.sleep"):
        embeddings = openai_embedder.embed_batch(texts)

    assert len(embeddings) == 1
    assert embeddings[0] == mock_embedding
    assert openai_embedder.client.embeddings.create.call_count == 3


def test_openai_embedder_embed_batch_fails_after_retries(
    openai_embedder: OpenAIEmbedder,
) -> None:
    """Test embed_batch raises exception after all retries fail."""
    texts = ["def hello(): pass"]

    openai_embedder.client.embeddings.create.side_effect = Exception("Persistent error")

    with patch("git_debug_oracle.embedder.openai_client.time.sleep"):
        with pytest.raises(Exception, match="Failed to embed batch after 3 retries"):
            openai_embedder.embed_batch(texts)

    assert openai_embedder.client.embeddings.create.call_count == 3


def test_openai_embedder_get_embedding_dimension(openai_embedder: OpenAIEmbedder) -> None:
    """Test get_embedding_dimension returns correct value."""
    dimension = openai_embedder.get_embedding_dimension()

    assert dimension == 1536


def test_openai_embedder_embed_batch_with_correct_parameters(
    openai_embedder: OpenAIEmbedder,
) -> None:
    """Test embed_batch calls client with correct parameters."""
    texts = ["def hello(): pass", "def goodbye(): pass"]

    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1] * 1536), Mock(embedding=[0.2] * 1536)]
    openai_embedder.client.embeddings.create.return_value = mock_response

    openai_embedder.embed_batch(texts)

    openai_embedder.client.embeddings.create.assert_called_once()
    call_kwargs = openai_embedder.client.embeddings.create.call_args.kwargs
    assert call_kwargs["input"] == texts
    assert call_kwargs["model"] == "text-embedding-3-small"
