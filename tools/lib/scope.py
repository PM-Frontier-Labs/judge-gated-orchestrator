"""File scope operations for drift checking."""

import fnmatch
from typing import List, Tuple


def matches_pattern(path: str, patterns: List[str]) -> bool:
    """Check if path matches any glob pattern."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def classify_files(
    changed_files: List[str],
    include_patterns: List[str],
    exclude_patterns: List[str] = None
) -> Tuple[List[str], List[str]]:
    """Return (in_scope, out_of_scope) based on include/exclude patterns."""
    exclude_patterns = exclude_patterns or []
    in_scope = []
    out_of_scope = []

    for file_path in changed_files:
        included = matches_pattern(file_path, include_patterns)
        excluded = matches_pattern(file_path, exclude_patterns)

        if included and not excluded:
            in_scope.append(file_path)
        else:
            out_of_scope.append(file_path)

    return in_scope, out_of_scope


def check_forbidden_files(
    changed_files: List[str],
    forbid_patterns: List[str]
) -> List[str]:
    """Return files matching forbidden patterns."""
    if not forbid_patterns:
        return []
    return [f for f in changed_files if matches_pattern(f, forbid_patterns)]
