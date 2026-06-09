"""Unit tests for git_watcher/repo_reader.py."""

import tempfile
from pathlib import Path

import pytest
from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from git_debug_oracle.git_watcher.repo_reader import (
    extract_files_from_commit,
    get_branch_head,
    get_changed_files,
    get_commit_metadata,
    get_commits_in_range,
    validate_repo,
)


@pytest.fixture
def temp_git_repo(tmp_path: Path) -> str:
    """Create a temporary Git repository for testing.

    Args:
        tmp_path: Pytest temporary directory fixture

    Returns:
        Absolute path to temporary repository
    """
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    repo = Repo.init(repo_path)

    repo.config_writer().set_value("user", "name", "Test User").release()
    repo.config_writer().set_value("user", "email", "test@example.com").release()

    file1 = repo_path / "file1.py"
    file1.write_text("def hello():\n    return 'world'\n")
    repo.index.add(["file1.py"])
    commit1 = repo.index.commit("Initial commit")

    file2 = repo_path / "file2.py"
    file2.write_text("def goodbye():\n    return 'farewell'\n")
    repo.index.add(["file2.py"])
    commit2 = repo.index.commit("Add file2")

    file1.write_text("def hello():\n    return 'universe'\n")
    repo.index.add(["file1.py"])
    commit3 = repo.index.commit("Modify file1")

    return str(repo_path)


def test_validate_repo_with_valid_repo(temp_git_repo: str) -> None:
    """Test validate_repo returns True for valid repository."""
    result = validate_repo(temp_git_repo)
    assert result is True


def test_validate_repo_with_nonexistent_path() -> None:
    """Test validate_repo returns False for nonexistent path."""
    result = validate_repo("/nonexistent/path")
    assert result is False


def test_validate_repo_with_non_git_directory(tmp_path: Path) -> None:
    """Test validate_repo returns False for non-Git directory."""
    non_git_dir = tmp_path / "not_a_repo"
    non_git_dir.mkdir()
    result = validate_repo(str(non_git_dir))
    assert result is False


def test_validate_repo_with_file_path(tmp_path: Path) -> None:
    """Test validate_repo returns False for file path."""
    file_path = tmp_path / "test.txt"
    file_path.write_text("test")
    result = validate_repo(str(file_path))
    assert result is False


def test_extract_files_from_commit(temp_git_repo: str) -> None:
    """Test extract_files_from_commit returns all files from commit."""
    files = extract_files_from_commit(temp_git_repo, "HEAD")

    assert len(files) == 2
    file_paths = [f[0] for f in files]
    assert "file1.py" in file_paths
    assert "file2.py" in file_paths

    file1_content = next(f[1] for f in files if f[0] == "file1.py")
    assert "universe" in file1_content


def test_extract_files_from_commit_with_specific_hash(temp_git_repo: str) -> None:
    """Test extract_files_from_commit with specific commit hash."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())
    first_commit_hash = commits[-1].hexsha

    files = extract_files_from_commit(temp_git_repo, first_commit_hash)

    assert len(files) == 1
    assert files[0][0] == "file1.py"
    assert "world" in files[0][1]


def test_extract_files_from_commit_with_invalid_hash(temp_git_repo: str) -> None:
    """Test extract_files_from_commit raises error for invalid hash."""
    with pytest.raises(GitCommandError):
        extract_files_from_commit(temp_git_repo, "invalid_hash_12345")


def test_extract_files_from_commit_with_invalid_repo() -> None:
    """Test extract_files_from_commit raises error for invalid repo."""
    with pytest.raises(InvalidGitRepositoryError):
        extract_files_from_commit("/nonexistent/path", "HEAD")


def test_get_commit_metadata(temp_git_repo: str) -> None:
    """Test get_commit_metadata returns correct metadata."""
    metadata = get_commit_metadata(temp_git_repo, "HEAD")

    assert "hash" in metadata
    assert "author" in metadata
    assert "timestamp" in metadata
    assert "message" in metadata

    assert metadata["author"] == "Test User"
    assert "Modify file1" in metadata["message"]
    assert len(metadata["hash"]) == 40


def test_get_commit_metadata_with_specific_hash(temp_git_repo: str) -> None:
    """Test get_commit_metadata with specific commit hash."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())
    first_commit_hash = commits[-1].hexsha

    metadata = get_commit_metadata(temp_git_repo, first_commit_hash)

    assert metadata["hash"] == first_commit_hash
    assert "Initial commit" in metadata["message"]


def test_get_commit_metadata_with_invalid_hash(temp_git_repo: str) -> None:
    """Test get_commit_metadata raises error for invalid hash."""
    with pytest.raises(GitCommandError):
        get_commit_metadata(temp_git_repo, "invalid_hash_12345")


def test_get_changed_files(temp_git_repo: str) -> None:
    """Test get_changed_files returns files changed between commits."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())

    second_commit_hash = commits[1].hexsha
    first_commit_hash = commits[2].hexsha

    changed_files = get_changed_files(temp_git_repo, first_commit_hash, second_commit_hash)

    assert len(changed_files) == 1
    assert "file2.py" in changed_files


def test_get_changed_files_with_modification(temp_git_repo: str) -> None:
    """Test get_changed_files detects file modifications."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())

    latest_commit_hash = commits[0].hexsha
    second_commit_hash = commits[1].hexsha

    changed_files = get_changed_files(temp_git_repo, second_commit_hash, latest_commit_hash)

    assert len(changed_files) == 1
    assert "file1.py" in changed_files


def test_get_changed_files_with_same_commit(temp_git_repo: str) -> None:
    """Test get_changed_files returns empty list for same commit."""
    changed_files = get_changed_files(temp_git_repo, "HEAD", "HEAD")
    assert len(changed_files) == 0


def test_get_commits_in_range(temp_git_repo: str) -> None:
    """Test get_commits_in_range returns commits between two commits."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())

    latest_commit_hash = commits[0].hexsha
    first_commit_hash = commits[2].hexsha

    commit_hashes = get_commits_in_range(temp_git_repo, first_commit_hash, latest_commit_hash)

    assert len(commit_hashes) == 2
    assert commits[1].hexsha in commit_hashes
    assert commits[0].hexsha in commit_hashes


def test_get_commits_in_range_chronological_order(temp_git_repo: str) -> None:
    """Test get_commits_in_range returns commits in chronological order."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())

    latest_commit_hash = commits[0].hexsha
    first_commit_hash = commits[2].hexsha

    commit_hashes = get_commits_in_range(temp_git_repo, first_commit_hash, latest_commit_hash)

    assert commit_hashes[0] == commits[1].hexsha
    assert commit_hashes[1] == commits[0].hexsha


def test_get_commits_in_range_with_adjacent_commits(temp_git_repo: str) -> None:
    """Test get_commits_in_range with adjacent commits."""
    repo = Repo(temp_git_repo)
    commits = list(repo.iter_commits())

    second_commit_hash = commits[1].hexsha
    first_commit_hash = commits[2].hexsha

    commit_hashes = get_commits_in_range(temp_git_repo, first_commit_hash, second_commit_hash)

    assert len(commit_hashes) == 1
    assert commit_hashes[0] == second_commit_hash


def test_get_branch_head(temp_git_repo: str) -> None:
    """Test get_branch_head returns HEAD commit for branch."""
    repo = Repo(temp_git_repo)
    expected_hash = repo.head.commit.hexsha

    commit_hash = get_branch_head(temp_git_repo, "master")

    assert commit_hash == expected_hash


def test_get_branch_head_with_nonexistent_branch(temp_git_repo: str) -> None:
    """Test get_branch_head returns None for nonexistent branch."""
    commit_hash = get_branch_head(temp_git_repo, "nonexistent_branch")
    assert commit_hash is None


def test_get_branch_head_with_new_branch(temp_git_repo: str) -> None:
    """Test get_branch_head works with newly created branch."""
    repo = Repo(temp_git_repo)
    new_branch = repo.create_head("feature_branch")
    expected_hash = new_branch.commit.hexsha

    commit_hash = get_branch_head(temp_git_repo, "feature_branch")

    assert commit_hash == expected_hash
