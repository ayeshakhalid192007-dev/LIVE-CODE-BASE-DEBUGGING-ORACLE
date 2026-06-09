"""Git repository file reading and commit metadata extraction."""

from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError, NoSuchPathError

from git_debug_oracle.utils.logging import get_logger

logger = get_logger(__name__)


def validate_repo(repo_path: str) -> bool:
    """Validate that the given path is a valid Git repository.

    Args:
        repo_path: Absolute path to repository

    Returns:
        True if valid Git repository, False otherwise
    """
    try:
        path = Path(repo_path)
        if not path.exists():
            logger.error("Repository path does not exist", path=repo_path)
            return False

        if not path.is_dir():
            logger.error("Repository path is not a directory", path=repo_path)
            return False

        Repo(repo_path)
        logger.debug("Repository validation successful", path=repo_path)
        return True

    except InvalidGitRepositoryError:
        logger.error("Path is not a valid Git repository", path=repo_path)
        return False
    except Exception as e:
        logger.error(
            "Repository validation failed",
            path=repo_path,
            error=str(e),
        )
        return False


def extract_files_from_commit(
    repo_path: str, commit_hash: str
) -> list[tuple[str, str]]:
    """Extract all files and their contents from a specific commit.

    Args:
        repo_path: Absolute path to repository
        commit_hash: Commit hash or reference (e.g., 'HEAD', 'main')

    Returns:
        List of tuples (file_path, file_content) for all files in commit

    Raises:
        InvalidGitRepositoryError: If repo_path is not a valid Git repository
        GitCommandError: If commit_hash does not exist
    """
    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, NoSuchPathError) as e:
        logger.error("Invalid repository path", path=repo_path, error=str(e))
        raise InvalidGitRepositoryError(f"Invalid repository: {repo_path}") from e
    
    try:
        commit = repo.commit(commit_hash)
    except Exception as e:
        logger.error(
            "Invalid commit hash",
            commit_hash=commit_hash,
            error=str(e),
        )
        raise GitCommandError("git", str(e)) from e

    files: list[tuple[str, str]] = []

    for item in commit.tree.traverse():
        if item.type == "blob":
            file_path = item.path
            try:
                file_content = item.data_stream.read().decode("utf-8")
                files.append((file_path, file_content))
                logger.debug(
                    "Extracted file from commit",
                    file_path=file_path,
                    commit_hash=commit_hash,
                    size=len(file_content),
                )
            except UnicodeDecodeError:
                logger.warning(
                    "Skipping binary file",
                    file_path=file_path,
                    commit_hash=commit_hash,
                )
                continue

    logger.info(
        "Extracted files from commit",
        commit_hash=commit_hash,
        file_count=len(files),
    )

    return files


def get_commit_metadata(repo_path: str, commit_hash: str) -> dict[str, str]:
    """Get metadata for a specific commit.

    Args:
        repo_path: Absolute path to repository
        commit_hash: Commit hash or reference

    Returns:
        Dictionary with keys: hash, author, timestamp, message

    Raises:
        InvalidGitRepositoryError: If repo_path is not a valid Git repository
        GitCommandError: If commit_hash does not exist
    """
    try:
        repo = Repo(repo_path)
    except InvalidGitRepositoryError:
        logger.error("Path is not a valid Git repository", path=repo_path)
        raise
    
    try:
        commit = repo.commit(commit_hash)
    except Exception as e:
        logger.error(
            "Invalid commit hash",
            commit_hash=commit_hash,
            error=str(e),
        )
        raise GitCommandError("git", str(e)) from e

    metadata = {
        "hash": commit.hexsha,
        "author": commit.author.name,
        "timestamp": commit.committed_datetime.isoformat(),
        "message": commit.message.strip(),
    }

    logger.debug("Retrieved commit metadata", commit_hash=commit_hash)

    return metadata


def get_changed_files(
    repo_path: str, start_commit: str, end_commit: str
) -> list[str]:
    """Get list of files changed between two commits.

    Args:
        repo_path: Absolute path to repository
        start_commit: Starting commit hash or reference
        end_commit: Ending commit hash or reference

    Returns:
        List of file paths that changed between commits

    Raises:
        InvalidGitRepositoryError: If repo_path is not a valid Git repository
        GitCommandError: If commits do not exist
    """
    repo = Repo(repo_path)
    start = repo.commit(start_commit)
    end = repo.commit(end_commit)

    changed_files: list[str] = []

    for diff in start.diff(end):
        if diff.a_path:
            changed_files.append(diff.a_path)
        if diff.b_path and diff.b_path != diff.a_path:
            changed_files.append(diff.b_path)

    unique_files = list(set(changed_files))

    logger.info(
        "Retrieved changed files",
        start_commit=start_commit,
        end_commit=end_commit,
        file_count=len(unique_files),
    )

    return unique_files


def get_commits_in_range(
    repo_path: str, start_commit: str, end_commit: str
) -> list[str]:
    """Get all commit hashes between two commits.

    Args:
        repo_path: Absolute path to repository
        start_commit: Starting commit hash or reference (exclusive)
        end_commit: Ending commit hash or reference (inclusive)

    Returns:
        List of commit hashes in chronological order (oldest first)

    Raises:
        InvalidGitRepositoryError: If repo_path is not a valid Git repository
        GitCommandError: If commits do not exist
    """
    repo = Repo(repo_path)

    commit_range = f"{start_commit}..{end_commit}"
    commits = list(repo.iter_commits(commit_range))

    commit_hashes = [commit.hexsha for commit in reversed(commits)]

    logger.info(
        "Retrieved commits in range",
        start_commit=start_commit,
        end_commit=end_commit,
        commit_count=len(commit_hashes),
    )

    return commit_hashes


def get_branch_head(repo_path: str, branch_name: str) -> Optional[str]:
    """Get the HEAD commit hash for a specific branch.

    Args:
        repo_path: Absolute path to repository
        branch_name: Name of the branch

    Returns:
        Commit hash of branch HEAD, or None if branch does not exist

    Raises:
        InvalidGitRepositoryError: If repo_path is not a valid Git repository
    """
    try:
        repo = Repo(repo_path)
        branch = repo.heads[branch_name]
        commit_hash = branch.commit.hexsha

        logger.debug(
            "Retrieved branch HEAD",
            branch=branch_name,
            commit_hash=commit_hash,
        )

        return commit_hash

    except (IndexError, AttributeError):
        logger.warning("Branch does not exist", branch=branch_name)
        return None
