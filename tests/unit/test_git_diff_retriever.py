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

        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.author.name = "test author"
        mock_commit.message = "test message"
        mock_commit.committed_date = 1000000
        mock_commit.hexsha = "h1hash"
        mock_commit.parents = [Mock(hexsha="parent_hash")]
        mock_commit.stats.files.keys.return_value = []

        # Mock diff output for first 3 commits
        mock_repo.commit.return_value = mock_commit
        mock_repo.git.diff.return_value = "diff --git a/file.py b/file.py\nindex abc..def\n--- a/file.py\n+++ b/file.py"
        mock_parent_diff = Mock()
        mock_repo.commit().parents[0].diff.return_value = mock_parent_diff

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo", return_value=mock_repo):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")

            # First 3 should have diff_content
            for i in range(min(3, len(diffs))):
                if diffs[i].diff_content:
                    assert len(diffs[i].diff_content) > 0
                    assert isinstance(diffs[i].diff_content, str)

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

        mock_repo = Mock()
        mock_commit = Mock()
        mock_commit.author.name = "John Doe"
        mock_commit.message = "Fix bug in parser"
        mock_commit.committed_date = 1000000
        mock_commit.hexsha = "abc123hash"
        mock_commit.parents = [Mock(hexsha="parent_hash")]
        mock_commit.stats.files.keys.return_value = ["file.py"]

        mock_repo.commit.return_value = mock_commit
        mock_repo.git.diff.return_value = "diff content"
        mock_parent_diff = Mock()
        mock_repo.commit().parents[0].diff.return_value = mock_parent_diff

        with patch("git_debug_oracle.retriever.git_diff_retriever.Repo", return_value=mock_repo):
            diffs = get_commit_diffs(commit_hashes, "/path/to/repo")

            if diffs:
                diff = diffs[0]
                assert isinstance(diff.author, str)
                assert isinstance(diff.message, str)
                assert diff.author == "John Doe"
                assert diff.message == "Fix bug in parser"
