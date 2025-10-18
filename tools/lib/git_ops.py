"""Git operations for judge system."""

import subprocess
from pathlib import Path
from typing import List


def get_changed_files(
    repo_root: Path,
    include_committed: bool = True,
    base_branch: str = "main",
    baseline_sha: str = None
) -> List[str]:
    """
    Get changed files.

    Args:
        repo_root: Repository root path
        include_committed: Include committed changes (default True)
        base_branch: Base branch for merge-base fallback (default "main")
        baseline_sha: Fixed baseline commit SHA for consistent diffs (preferred)

    Returns:
        List of changed file paths
    """
    try:
        all_changes: List[str] = []

        # Always get uncommitted changes (staged and unstaged) vs HEAD
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        uncommitted = [f for f in result.stdout.strip().split("\n") if f]
        all_changes.extend(uncommitted)

        # Include untracked files (not yet added to git index)
        try:
            untracked_result = subprocess.run(
                ["git", "ls-files", "--others", "--exclude-standard"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            untracked = [f for f in untracked_result.stdout.strip().split("\n") if f]
            all_changes.extend(untracked)
        except subprocess.CalledProcessError:
            # If listing untracked fails, continue with what we have
            pass

        # Optionally get committed changes
        if include_committed:
            if baseline_sha:
                # Use fixed baseline SHA for consistent diffs (preferred)
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{baseline_sha}...HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                committed = [f for f in result.stdout.strip().split("\n") if f]
                all_changes.extend(committed)
            else:
                # Fallback: use merge-base (can drift as base_branch advances)
                try:
                    result = subprocess.run(
                        ["git", "merge-base", "HEAD", base_branch],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    merge_base = result.stdout.strip()

                    # Get committed changes
                    result = subprocess.run(
                        ["git", "diff", "--name-only", f"{merge_base}...HEAD"],
                        cwd=repo_root,
                        capture_output=True,
                        text=True,
                        check=True,
                    )
                    committed = [f for f in result.stdout.strip().split("\n") if f]
                    all_changes.extend(committed)
                except subprocess.CalledProcessError:
                    # Could not determine merge-base (e.g., base branch missing)
                    # Proceed with uncommitted + untracked results only
                    pass

        # Remove duplicates and empty strings
        unique_changes = list(set(all_changes))
        return [f for f in unique_changes if f]

    except subprocess.CalledProcessError:
        # Not a git repo or base branch doesn't exist
        return []
