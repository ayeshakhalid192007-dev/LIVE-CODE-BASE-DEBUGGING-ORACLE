"""Unit tests for embedder/voyage_client.py."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from git_debug_oracle.embedder.voyage_client import VoyageEmbedder


@pytest.fixture
def mock_voyage_client() -> Mock:
    """Create a mock Voyage AI client.

    Returns:
        Mock Voyage AI client
    """
    return MagicMock()


@pytest.fixture
def voyage_embedder(mock_voyage_client: Mock) -> VoyageEmbedder:
    """Create a VoyageEmbedder with mocked client.

    Args:
        mock_voyage_client: Mock Voyage AI client

    Returns:
        VoyageEmbedder instance
    """
    with patch("git_debug_oracle.embedder.voyage_client.voyageai.Client") as mock_client_class:
        mock_client_class.return_value = mock_voyage_client
        embedder = VoyageEmbedder(api_key="test_key")
    return embedder


def test_voyage_embedder_initialization(mock_voyage_client: Mock) -> None:
    """Test VoyageEmbedder initializes with correct model."""
    with patch("git_debug_oracle.embedder.voyage_client.voyageai.Client") as mock_client_class:
        mock_client_class.return_value = mock_voyage_client
        embedder = VoyageEmbedder(api_key="test_key")

    assert embedder.model == "voyage-code-2"
    mock_client_class.assert_called_once_with(api_key="test_key")


def test_voyage_embedder_embed_batch_success(voyage_embedder: VoyageEmbedder) -> None:
    """Test embed_batch successfully embeds texts."""
    texts = ["def hello(): pass", "def goodbye(): pass"]

    mock_embedding_1 = [0.1] * 1536
    mock_embedding_2 = [0.2] * 1536

    mock_response = Mock()
    mock_response.embeddings = [
        Mock(embedding=mock_embedding_1),
        Mock(embedding=mock_embedding_2),
    ]

    voyage_embedder.client.embed.return_value = mock_response

    embeddings = voyage_embedder.embed_batch(texts)

    assert len(embeddings) == 2
    assert embeddings[0] == mock_embedding_1
    assert embeddings[1] == mock_embedding_2
    voyage_embedder.client.embed.assert_called_once()


def test_voyage_embedder_embed_batch_empty_list(voyage_embedder: VoyageEmbedder) -> None:
    """Test embed_batch handles empty text list."""
    embeddings = voyage_embedder.embed_batch([])

    assert embeddings == []
    voyage_embedder.client.embed.assert_not_called()


def test_voyage_embedder_embed_batch_retry_on_failure(voyage_embedder: VoyageEmbedder) -> None:
    """Test embed_batch retries on failure."""
    texts = ["def hello(): pass"]

    mock_embedding = [0.1] * 1536
    mock_response = Mock()
    mock_response.embeddings = [Mock(embedding=mock_embedding)]

    voyage_embedder.client.embed.side_effect = [
        Exception("Network error"),
        Exception("Timeout"),
        mock_response,
    ]

    with patch("git_debug_oracle.embedder.voyage_client.time.sleep"):
        embeddings = voyage_embedder.embed_batch(texts)

    assert len(embeddings) == 1
    assert embeddings[0] == mock_embedding
    assert voyage_embedder.client.embed.call_count == 3


def test_voyage_embedder_embed_batch_fails_after_retries(
    voyage_embedder: VoyageEmbedder,
) -> None:
    """Test embed_batch raises exception after all retries fail."""
    texts = ["def hello(): pass"]

    voyage_embedder.client.embed.side_effect = Exception("Persistent error")

    with patch("git_debug_oracle.embedder.voyage_client.time.sleep"):
        with pytest.raises(Exception, match="Failed to embed batch after 3 retries"):
            voyage_embedder.embed_batch(texts)

    assert voyage_embedder.client.embed.call_count == 3


def test_voyage_embedder_get_embedding_dimension(voyage_embedder: VoyageEmbedder) -> None:
    """Test get_embedding_dimension returns correct value."""
    dimension = voyage_embedder.get_embedding_dimension()

    assert dimension == 1536


def test_voyage_embedder_embed_batch_with_correct_parameters(
    voyage_embedder: VoyageEmbedder,
) -> None:
    """Test embed_batch calls client with correct parameters."""
    texts = ["def hello(): pass", "def goodbye(): pass"]

    mock_response = Mock()
    mock_response.embeddings = [Mock(embedding=[0.1] * 1536), Mock(embedding=[0.2] * 1536)]
    voyage_embedder.client.embed.return_value = mock_response

    voyage_embedder.embed_batch(texts)

    voyage_embedder.client.embed.assert_called_once()
    call_kwargs = voyage_embedder.client.embed.call_args.kwargs
    assert call_kwargs["texts"] == texts
    assert call_kwargs["model"] == "voyage-code-2"
    assert call_kwargs["input_type"] == "code"
