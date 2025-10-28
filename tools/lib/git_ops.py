#!/usr/bin/env python3
"""
Git operations for judge v2.

Simple, focused git utilities with clear error handling.
"""

import subprocess
from pathlib import Path
from typing import List, Tuple, Optional


def get_changed_files(
    repo_root: Path,
    baseline_sha: Optional[str] = None,
    include_uncommitted: bool = True
) -> Tuple[List[str], List[str]]:
    """
    Get list of changed files.
    
    Args:
        repo_root: Repository root path
        baseline_sha: Baseline commit SHA (if None, uses merge-base)
        include_uncommitted: Include unstaged/staged changes
        
    Returns:
        Tuple of (sorted_files, warnings)
    """
    warnings = []
    all_changes = []
    
    try:
        # Get uncommitted changes (staged + unstaged)
        if include_uncommitted:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True
            )
            uncommitted = [f for f in result.stdout.strip().split("\n") if f]
            all_changes.extend(uncommitted)
        
        # Get committed changes from baseline
        if baseline_sha and baseline_sha != "unknown":
            try:
                result = subprocess.run(
                    ["git", "diff", "--name-only", f"{baseline_sha}...HEAD"],
                    cwd=repo_root,
                    capture_output=True,
                    text=True,
                    check=True
                )
                committed = [f for f in result.stdout.strip().split("\n") if f]
                all_changes.extend(committed)
            except subprocess.CalledProcessError as e:
                warnings.append(f"Could not get changes from baseline {baseline_sha}: {e}")
        
        # Remove duplicates and sort
        unique_files = sorted(set(f for f in all_changes if f))
        
        return unique_files, warnings
        
    except subprocess.CalledProcessError as e:
        warnings.append(f"Git operation failed: {e}")
        return [], warnings


def get_current_sha(repo_root: Path) -> Optional[str]:
    """Get current git HEAD SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

