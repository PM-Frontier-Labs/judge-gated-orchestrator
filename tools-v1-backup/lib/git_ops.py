"""Git operations for judge system."""

import subprocess
from pathlib import Path
from typing import List, Tuple


def get_changed_files(
    repo_root: Path,
    include_committed: bool = True,
    base_branch: str = "main",
    baseline_sha: str = None
) -> Tuple[List[str], List[str]]:
    """
    Get changed files with deterministic ordering and error transparency.

    Args:
        repo_root: Repository root path
        include_committed: Include committed changes (default True)
        base_branch: Base branch for merge-base fallback (default "main")
        baseline_sha: Fixed baseline commit SHA for consistent diffs (preferred)

    Returns:
        Tuple of (sorted_file_list, warnings_list)
    """
    warnings = []
    
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
                    # Check if base_branch exists first
                    subprocess.run(
                        ["git", "rev-parse", "--verify", f"origin/{base_branch}"],
                        cwd=repo_root,
                        capture_output=True,
                        check=True
                    )
                    
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
                except subprocess.CalledProcessError as e:
                    warning_msg = f"Cannot access base branch {base_branch}: {e}"
                    warnings.append(warning_msg)
                    print(f"⚠️  Warning: {warning_msg}")
                    # Continue with just uncommitted changes

        # Remove duplicates and empty strings, then sort for determinism
        unique_changes = list(set(all_changes))
        filtered_changes = [f for f in unique_changes if f]
        sorted_changes = sorted(filtered_changes)  # Deterministic ordering
        
        return sorted_changes, warnings

    except subprocess.CalledProcessError as e:
        error_msg = f"Git operation failed: {e}"
        warnings.append(error_msg)
        print(f"⚠️  Warning: {error_msg}")
        return [], warnings
