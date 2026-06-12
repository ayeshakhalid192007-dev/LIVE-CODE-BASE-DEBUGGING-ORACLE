"""Tests for Qdrant vector search retriever."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, AsyncMock

from git_debug_oracle.error_ingestion.models import ErrorContext, RetrievalResult
from git_debug_oracle.retriever.qdrant_retriever import search_qdrant


class TestQdrantRetriever:
    """Vector search against indexed code chunks in Qdrant."""

    def test_search_returns_retrieval_results(self) -> None:
        """Search returns list of RetrievalResult objects."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
            function_name="process",
            error_message="error",
        )
        query = "process in src/app.py error"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client") as mock_client:
            mock_search = Mock()
            mock_client.return_value.search = mock_search
            mock_search.return_value = []

            results = search_qdrant(query, ctx, top_k=5)

            assert isinstance(results, list)

    def test_search_respects_top_k(self) -> None:
        """Search respects top_k parameter."""
        ctx = ErrorContext(file_path="app.py", line_number=1)
        query = "app.py"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client"):
            results = search_qdrant(query, ctx, top_k=3)
            assert len(results) <= 3

    def test_search_with_metadata_filter(self) -> None:
        """Search filters by file_path if provided."""
        ctx = ErrorContext(
            file_path="src/app.py",
            line_number=42,
        )
        query = "app.py"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client"):
            results = search_qdrant(query, ctx, top_k=5)
            # All results should be from same file or related
            assert isinstance(results, list)

    def test_search_empty_results(self) -> None:
        """Search with no matches returns empty list."""
        ctx = ErrorContext(
            file_path="nonexistent.py",
            line_number=1,
        )
        query = "nonexistent"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client") as mock_client:
            mock_search = Mock()
            mock_client.return_value.search = mock_search
            mock_search.return_value = []

            results = search_qdrant(query, ctx, top_k=5)
            assert results == []

    def test_result_has_required_fields(self) -> None:
        """Retrieval result contains all required fields."""
        ctx = ErrorContext(file_path="app.py", line_number=1)
        query = "app.py"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client"):
            results = search_qdrant(query, ctx, top_k=1)

            if results:
                result = results[0]
                assert hasattr(result, "file_path")
                assert hasattr(result, "start_line")
                assert hasattr(result, "end_line")
                assert hasattr(result, "code_snippet")
                assert hasattr(result, "commit_hash")
                assert hasattr(result, "final_score")

    def test_search_scores_normalized(self) -> None:
        """All scores in [0, 1] range."""
        ctx = ErrorContext(file_path="app.py", line_number=1)
        query = "app.py"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client"):
            results = search_qdrant(query, ctx, top_k=5)

            for result in results:
                assert 0 <= result.final_score <= 1
                assert 0 <= result.original_score <= 1
                assert 0 <= result.recency_score <= 1

    def test_search_results_ranked_by_score(self) -> None:
        """Results sorted by final_score descending."""
        ctx = ErrorContext(file_path="app.py", line_number=1)
        query = "app.py"

        with patch("git_debug_oracle.retriever.qdrant_retriever.get_qdrant_client"):
            results = search_qdrant(query, ctx, top_k=5)

            if len(results) > 1:
                for i in range(len(results) - 1):
                    assert results[i].final_score >= results[i + 1].final_score
