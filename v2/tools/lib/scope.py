#!/usr/bin/env python3
"""
Scope classification using pathspec.

Simple, clear implementation with no experimental features.
"""

from typing import List, Tuple

try:
    import pathspec
except ImportError:
    raise ImportError(
        "pathspec is required for scope checking. "
        "Install with: pip install pathspec"
    )


def classify_files(
    changed_files: List[str],
    include_patterns: List[str],
    exclude_patterns: List[str] = None
) -> Tuple[List[str], List[str]]:
    """
    Classify files as in-scope or out-of-scope.
    
    Args:
        changed_files: List of file paths
        include_patterns: Glob patterns for in-scope files
        exclude_patterns: Glob patterns to exclude from scope
        
    Returns:
        Tuple of (in_scope_files, out_of_scope_files)
    """
    exclude_patterns = exclude_patterns or []
    
    in_scope = []
    out_of_scope = []
    
    # Build pathspec matchers
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
