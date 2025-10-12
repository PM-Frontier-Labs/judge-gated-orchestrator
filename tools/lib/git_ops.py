"""Git operations for judge system."""

import subprocess
from pathlib import Path
from typing import List


def get_changed_files(
    repo_root: Path,
    include_committed: bool = True,
    base_branch: str = "main"
) -> List[str]:
    """Get changed files. If include_committed=False, only uncommitted changes."""
    try:
        all_changes = []

        # Always get uncommitted changes (staged and unstaged)
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        uncommitted = [f for f in result.stdout.strip().split("\n") if f]
        all_changes.extend(uncommitted)

        # Optionally get committed changes from base branch
        if include_committed:
            # Get merge base
            result = subprocess.run(
                ["git", "merge-base", "HEAD", base_branch],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            merge_base = result.stdout.strip()

            # Get committed changes
            result = subprocess.run(
                ["git", "diff", "--name-only", f"{merge_base}...HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            committed = [f for f in result.stdout.strip().split("\n") if f]
            all_changes.extend(committed)

        # Remove duplicates and empty strings
        unique_changes = list(set(all_changes))
        return [f for f in unique_changes if f]

    except subprocess.CalledProcessError:
        # Not a git repo or base branch doesn't exist
        return []
