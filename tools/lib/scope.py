"""File scope operations for drift checking."""

from typing import List, Tuple

try:
    import pathspec
except ImportError:
    raise ImportError(
        "pathspec is required for scope resolution. "
        "Install with: pip install pathspec"
    )


def matches_pattern(path: str, patterns: List[str]) -> bool:
    """
    Check if path matches any glob pattern using pathspec.
    """
    spec = pathspec.PathSpec.from_lines('gitwildmatch', patterns)
    return spec.match_file(path)


def classify_files(
    changed_files: List[str],
    include_patterns: List[str],
    exclude_patterns: List[str] = None
) -> Tuple[List[str], List[str]]:
    """
    Return (in_scope, out_of_scope) based on include/exclude patterns.

    Uses .gitignore-style pattern matching (supports ** for recursive matching).
    """
    exclude_patterns = exclude_patterns or []
    in_scope = []
    out_of_scope = []

    # Use pathspec for accurate matching
    include_spec = pathspec.PathSpec.from_lines('gitwildmatch', include_patterns)
    exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', exclude_patterns) if exclude_patterns else None

    for file_path in changed_files:
        included = include_spec.match_file(file_path)
        excluded = exclude_spec.match_file(file_path) if exclude_spec else False

        if included and not excluded:
            in_scope.append(file_path)
        else:
            out_of_scope.append(file_path)

    return in_scope, out_of_scope


def resolve_scope(scope_config: dict, changed_files: List[str]) -> List[str]:
    """Unified scope resolution for all gate types."""
    if scope_config.get("lint_scope") == "scope":
        return filter_changed_files(changed_files, scope_config)
    return changed_files


def filter_changed_files(changed_files: List[str], scope_config: dict) -> List[str]:
    """Filter changed files against scope patterns."""
    include_patterns = scope_config.get("scope", {}).get("include", [])
    if not include_patterns:
        return changed_files
    
    # Use pathspec for consistent pattern matching (same as classify_files)
    include_spec = pathspec.PathSpec.from_lines('gitwildmatch', include_patterns)
    return [f for f in changed_files if include_spec.match_file(f)]


def check_forbidden_files(
    changed_files: List[str],
    forbid_patterns: List[str]
) -> List[str]:
    """Return files matching forbidden patterns."""
    if not forbid_patterns:
        return []
    return [f for f in changed_files if matches_pattern(f, forbid_patterns)]
