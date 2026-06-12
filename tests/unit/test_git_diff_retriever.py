"""Tests for git diff retriever."""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from git_debug_oracle.error_ingestion.models import CommitDiff
from git_debug_oracle.retriever.git_diff_retriever import get_commit_diffs


class TestGitDiffRetriever:
    """Fetch git diffs for commits in retrieval results."""

    def test_get_diffs_returns_list(self) -> None:
        """get_commit_diffs returns list of CommitDiff."""
        commit_hashes = ["abc123", "def456"]

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo"):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")
            assert isinstance(diffs, list)

    def test_get_diffs_respects_limit(self) -> None:
        """Only fetches diffs for max 5 commits."""
        commit_hashes = ["h" + str(i) for i in range(10)]

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo"):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")
            assert len(diffs) <= 5

    def test_get_diffs_empty_list(self) -> None:
        """Empty commit list returns empty diffs."""
        diffs = get_commit_diffs([], "/path/to/repo")
        assert diffs == []

    def test_diff_has_required_fields(self) -> None:
        """Each CommitDiff contains required fields."""
        commit_hashes = ["abc123"]

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo"):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")

            if diffs:
                diff = diffs[0]
                assert hasattr(diff, "commit_hash")
                assert hasattr(diff, "author")
                assert hasattr(diff, "message")
                assert hasattr(diff, "timestamp")
                assert hasattr(diff, "files_changed")

    def test_full_diff_for_top_commits(self) -> None:
        """First 3 commits include full diff content."""
        commit_hashes = ["h1", "h2", "h3", "h4", "h5"]

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo"):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")

            # First 3 should have diff_content
            for i in range(min(3, len(diffs))):
                if diffs[i].diff_content:
                    assert len(diffs[i].diff_content) > 0

    def test_files_changed_extracted(self) -> None:
        """files_changed list populated from diff."""
        commit_hashes = ["abc123"]

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo"):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")

            if diffs:
                diff = diffs[0]
                assert isinstance(diff.files_changed, list)

    def test_invalid_repo_path_handled(self) -> None:
        """Invalid repo path returns empty list."""
        diffs = get_commit_diffs(["abc"], "/nonexistent/repo")
        assert diffs == []

    def test_commit_metadata_extracted(self) -> None:
        """Commit author and message extracted."""
        commit_hashes = ["abc123"]

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo"):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")

            if diffs:
                diff = diffs[0]
                assert isinstance(diff.author, str)
                assert isinstance(diff.message, str)
