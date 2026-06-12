"""Git diff retriever for fetching commit changes.

Retrieves git diffs for commits containing retrieved code chunks,
providing context about what changed in those commits.
"""

from datetime import datetime, timezone
from typing import Optional

from git.repo import Repo
from git.exc import GitCommandError, InvalidGitRepositoryError

from git_debug_oracle.error_ingestion.models import CommitDiff


def get_commit_diffs(
    commit_hashes: list[str],
    repo_path: str,
    max_diffs: int = 5,
) -> list[CommitDiff]:
    """Fetch git diffs for specified commits.

    Retrieves diffs from a git repository for the given commit hashes.
    Limited to max_diffs commits to avoid performance issues. Full diff
    content is included for the first 3 commits; others include only
    file change lists.

    Args:
        commit_hashes: List of git commit SHA hashes
        repo_path: Path to git repository root
        max_diffs: Maximum commits to fetch diffs for (default: 5)

    Returns:
        List of CommitDiff objects with metadata and diff content.
        Empty list if repo is invalid or no commits found.

    Example:
        >>> diffs = get_commit_diffs(["abc123", "def456"], "/path/to/repo")
        >>> len(diffs) <= 5
        True
    """
    if not commit_hashes:
        return []

    try:
        repo = Repo(repo_path)
    except (InvalidGitRepositoryError, Exception):
        # Invalid repo path or not a git repo
        return []

    diffs: list[CommitDiff] = []

    for idx, commit_hash in enumerate(commit_hashes[:max_diffs]):
        try:
            # Get commit object
            commit = repo.commit(commit_hash)

            # Extract metadata
            author = commit.author.name if commit.author else "unknown"
            message = commit.message.strip() if commit.message else ""
            timestamp = datetime.fromtimestamp(commit.committed_date, tz=timezone.utc)

            # Get list of files changed
            files_changed: list[str] = []
            if commit.parents:
                # Compare with parent
                diffs_obj = commit.parents[0].diff(commit)
                files_changed = [d.b_path or d.a_path or "" for d in diffs_obj]
                files_changed = [f for f in files_changed if f]
            else:
                # First commit - all files are "changed"
                files_changed = list(commit.stats.files.keys())

            # Include full diff for first 3 commits only
            diff_content: Optional[str] = None
            if idx < 3:
                try:
                    # Get full diff output
                    if commit.parents:
                        diff_output = repo.git.diff(commit.parents[0].hexsha, commit.hexsha)
                    else:
                        # First commit: show all files
                        diff_output = repo.git.show(commit.hexsha)
                    diff_content = diff_output[:5000]  # Limit to 5000 chars
                except GitCommandError:
                    pass

            diff = CommitDiff(
                commit_hash=commit_hash,
                author=author,
                message=message,
                timestamp=timestamp,
                files_changed=files_changed,
                diff_content=diff_content,
            )
            diffs.append(diff)

        except Exception:
            # Commit not found or other git error - skip
            continue

    return diffs
