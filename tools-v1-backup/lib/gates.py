#!/usr/bin/env python3
"""
Gate Logic: Individual gate implementations extracted from judge.py.

This module contains the actual gate logic implementations, separated
from the main judge.py to enable clean gate interfaces.
"""

from typing import List, Dict, Any
from pathlib import Path


def check_artifacts(phase: Dict[str, Any]) -> List[str]:
    """Check for required artifacts."""
    issues = []
    
    # Check for required artifacts
    artifacts = phase.get("artifacts", [])
    for artifact in artifacts:
        artifact_path = Path(artifact)
        if not artifact_path.exists():
            issues.append(f"Missing required artifact: {artifact}")
    
    return issues


def check_docs(phase: Dict[str, Any], changed_files: List[str]) -> List[str]:
    """Check documentation requirements."""
    issues = []
    
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])
    
    if not must_update:
        return issues
    
    if not changed_files:
        issues.append(
            "Documentation gate failed: No changed files detected\n"
            "This usually means the baseline SHA is incorrect or no changes were made."
        )
        return issues
    
    # Check each required documentation update
    for doc_path in must_update:
        # Use prefix matching for directory requirements
        if not any(f.startswith(doc_path) for f in changed_files):
            issues.append(f"Documentation gate failed: {doc_path} not updated")
    
    return issues


def check_drift(phase: Dict[str, Any], plan: Dict[str, Any], baseline_sha: str = None, repo_root: Path = None) -> List[str]:
    """Check for plan drift."""
    issues = []
    
    # Check if drift gate is enabled
    drift_gate = phase.get("gates", {}).get("drift")
    if not drift_gate:
        return issues  # Drift checking not enabled for this phase
    
    # Get base branch (fallback only)
    base_branch = plan.get("plan", {}).get("base_branch", "main")
    
    # Get changed files using baseline SHA for consistent diffs
    from .git_ops import get_changed_files
    
    # Use provided repo_root or fall back to current directory
    if repo_root is None:
        repo_root = Path.cwd()
    
    changed_files, warnings = get_changed_files(
        repo_root,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )
    
    # Display warnings if any
    for warning in warnings:
        print(f"  ⚠️  {warning}")
    
    if not changed_files:
        return issues  # No changes or not a git repo
    
    # Get scope patterns from plan
    scope_config = phase.get("scope", {})
    include_patterns = scope_config.get("include", [])
    exclude_patterns = scope_config.get("exclude", [])
    
    # Classify files as in-scope or out-of-scope
    from .scope import classify_files
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    # Check drift limits
    allowed_drift = drift_gate.get("allowed_out_of_scope_changes", 0)
    if len(out_of_scope) > allowed_drift:
        issues.append(
            f"Plan drift detected: {len(out_of_scope)} out-of-scope files changed "
            f"(limit: {allowed_drift})\n"
            f"Out-of-scope files: {', '.join(out_of_scope[:10])}"
            + ("..." if len(out_of_scope) > 10 else "")
        )
    
    return issues
