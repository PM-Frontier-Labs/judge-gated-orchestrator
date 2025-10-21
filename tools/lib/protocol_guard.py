"""Protocol integrity verification."""
import hashlib
import json
import fnmatch
from pathlib import Path
from typing import List, Dict, Any


def sha256(file_path: Path) -> str:
    """Compute SHA256 hash of file."""
    return hashlib.sha256(file_path.read_bytes()).hexdigest()


def verify_protocol_lock(
    repo_root: Path,
    plan: Dict[str, Any],
    phase_id: str,
    baseline_sha: str = None
) -> List[str]:
    """
    Verify protocol files haven't been tampered with.

    Args:
        repo_root: Repository root path
        plan: Full plan configuration
        phase_id: Current phase ID
        baseline_sha: Optional baseline commit SHA for consistent diffs

    Returns list of issues (empty = all good).
    """
    issues = []

    # Load protocol lock config
    lock = plan.get("plan", {}).get("protocol_lock", {})
    if not lock:
        return []  # Protocol lock not configured

    protected_globs = lock.get("protected_globs", [])
    allow_in_phases = set(lock.get("allow_in_phases", []))

    # Load manifest
    manifest_path = repo_root / ".repo/protocol_manifest.json"
    if not manifest_path.exists():
        return ["Protocol manifest missing. Run: ./tools/generate_manifest.py"]

    manifest = json.loads(manifest_path.read_text())
    files = manifest.get("files", {})

    # CRITICAL: Self-check judge integrity FIRST
    judge_rel = "tools/judge.py"
    judge_abs = repo_root / judge_rel
    if judge_rel in files:
        actual_hash = sha256(judge_abs)
        expected_hash = files[judge_rel]
        if actual_hash != expected_hash:
            issues.append(
                f"🚨 JUDGE TAMPER DETECTED: {judge_rel}\n"
                f"   Expected: {expected_hash}\n"
                f"   Actual:   {actual_hash}\n"
                f"   The judge has been modified. This is a critical protocol violation."
            )
            return issues  # Fail immediately on judge tamper

    # If in maintenance phase, allow changes
    if phase_id in allow_in_phases:
        return []

    # Verify all manifest files
    for rel_path, expected_hash in files.items():
        file_path = repo_root / rel_path
        if not file_path.exists():
            issues.append(f"Protocol file missing: {rel_path}")
        else:
            actual_hash = sha256(file_path)
            if actual_hash != expected_hash:
                issues.append(
                    f"Protocol file modified: {rel_path}\n"
                    f"   Expected: {expected_hash}\n"
                    f"   Actual:   {actual_hash}"
                )

    # Check git diff for protected files
    from lib.git_ops import get_changed_files
    base_branch = plan.get("plan", {}).get("base_branch", "main")

    try:
        changed_files, warnings = get_changed_files(
            repo_root,
            include_committed=True,
            base_branch=base_branch,
            baseline_sha=baseline_sha
        )
        
        # Display warnings if any
        for warning in warnings:
            print(f"  ⚠️  {warning}")

        for changed_file in changed_files:
            if any(fnmatch.fnmatch(changed_file, glob) for glob in protected_globs):
                # Skip if already reported in manifest check
                if changed_file not in files:
                    issues.append(f"Protected file changed: {changed_file}")
    except Exception:
        # Git operations may fail in non-git repos or first commit
        pass

    return issues


def verify_phase_binding(
    repo_root: Path,
    current: Dict[str, Any]
) -> List[str]:
    """
    Verify plan and manifest haven't changed mid-phase.

    Returns list of issues (empty = all good).
    """
    issues = []

    plan_path = repo_root / ".repo/plan.yaml"
    manifest_path = repo_root / ".repo/protocol_manifest.json"

    # Check plan binding
    if "plan_sha" in current:
        if not plan_path.exists():
            issues.append("Plan file missing: .repo/plan.yaml")
        else:
            actual_plan_sha = sha256(plan_path)
            expected_plan_sha = current["plan_sha"]
            if actual_plan_sha != expected_plan_sha:
                issues.append(
                    f"Plan changed mid-phase: .repo/plan.yaml\n"
                    f"   Expected: {expected_plan_sha}\n"
                    f"   Actual:   {actual_plan_sha}\n"
                    f"   The plan cannot be modified during phase execution."
                )

    # Check manifest binding
    if "manifest_sha" in current:
        if not manifest_path.exists():
            issues.append("Manifest file missing: .repo/protocol_manifest.json")
        else:
            actual_manifest_sha = sha256(manifest_path)
            expected_manifest_sha = current["manifest_sha"]
            if actual_manifest_sha != expected_manifest_sha:
                issues.append(
                    f"Manifest changed mid-phase: .repo/protocol_manifest.json\n"
                    f"   Expected: {expected_manifest_sha}\n"
                    f"   Actual:   {actual_manifest_sha}\n"
                    f"   The manifest cannot be modified during phase execution."
                )

    return issues
