#!/usr/bin/env python3
"""
Judge: Evaluates a phase against plan gates.

Checks:
- Artifacts exist
- Tests pass
- Documentation updated
- LLM code review (if enabled)
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# Import shared utilities
from lib.git_ops import get_changed_files
from lib.scope import classify_files, check_forbidden_files
from lib.traces import check_gate_trace
from lib.protocol_guard import verify_protocol_lock, verify_phase_binding

# Import LLM judge (optional)
try:
    from llm_judge import llm_code_review
    LLM_JUDGE_AVAILABLE = True
except ImportError:
    LLM_JUDGE_AVAILABLE = False

REPO_ROOT = Path(__file__).parent.parent
REPO_DIR = REPO_ROOT / ".repo"
CRITIQUES_DIR = REPO_DIR / "critiques"
TRACES_DIR = REPO_DIR / "traces"


def load_plan() -> Dict[str, Any]:
    """Load plan.yaml and validate."""
    plan_file = REPO_DIR / "plan.yaml"
    if not plan_file.exists():
        print(f"❌ Error: {plan_file} not found")
        sys.exit(1)

    try:
        with plan_file.open() as f:
            return yaml.safe_load(f)
    except yaml.YAMLError as e:
        print(f"❌ Error: Invalid YAML in {plan_file}: {e}")
        sys.exit(1)


def get_phase(plan: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    """Get phase configuration from plan."""
    phases = plan.get("plan", {}).get("phases", [])
    for phase in phases:
        if phase.get("id") == phase_id:
            return phase
    raise ValueError(f"Phase {phase_id} not found in plan")


def check_artifacts(phase: Dict[str, Any]) -> List[str]:
    """Check that required artifacts exist and are non-empty."""
    issues = []
    artifacts = phase.get("artifacts", {}).get("must_exist", [])

    for artifact in artifacts:
        path = REPO_ROOT / artifact
        if not path.exists():
            issues.append(f"Missing required artifact: {artifact}")
        elif path.stat().st_size == 0:
            issues.append(f"Artifact is empty: {artifact}")

    return issues




def check_docs(phase: Dict[str, Any], changed_files: List[str] = None) -> List[str]:
    """Check that documentation was actually updated in this phase."""
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

    if changed_files is None:
        changed_files = []

    # Check each required doc
    for doc in must_update:
        # Handle section anchors like "docs/mvp.md#feature"
        doc_path = doc.split("#")[0]
        anchor = doc.split("#")[1] if "#" in doc else None
        path = REPO_ROOT / doc_path

        # Check existence
        if not path.exists():
            issues.append(f"Documentation not found: {doc_path}")
            continue

        # Check non-empty
        if path.stat().st_size == 0:
            issues.append(f"Documentation is empty: {doc_path}")
            continue

        # CRITICAL: Check if doc was actually changed in this phase
        if doc_path not in changed_files:
            issues.append(
                f"Documentation not updated in this phase: {doc_path}\n"
                f"   This file must be modified as part of {phase['id']}"
            )
            continue

        # If anchor specified, verify heading exists
        if anchor:
            content = path.read_text()
            # Look for markdown heading: # anchor or ## anchor, etc.
            import re
            pattern = rf'^#+\s+{re.escape(anchor)}'
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                issues.append(
                    f"Documentation section not found: {doc}#{anchor}\n"
                    f"   Expected heading '{anchor}' in {doc_path}"
                )

    return issues




def check_drift(phase: Dict[str, Any], plan: Dict[str, Any], baseline_sha: str = None) -> List[str]:
    """Check for changes outside phase scope (plan drift)."""
    issues = []

    # Check if drift gate is enabled
    drift_gate = phase.get("gates", {}).get("drift")
    if not drift_gate:
        return []  # Drift checking not enabled for this phase

    # Get base branch (fallback only)
    base_branch = plan.get("plan", {}).get("base_branch", "main")

    # Get changed files using baseline SHA for consistent diffs
    changed_files = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )

    if not changed_files:
        return []  # No changes or not a git repo

    # Get scope patterns
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    if not include_patterns:
        return []  # No scope defined, can't check drift

    # Classify files using shared utility
    in_scope, out_of_scope = classify_files(
        changed_files,
        include_patterns,
        exclude_patterns
    )

    # Check forbidden patterns using shared utility
    drift_rules = phase.get("drift_rules", {})
    forbid_patterns = drift_rules.get("forbid_changes", [])
    forbidden_files = check_forbidden_files(changed_files, forbid_patterns)

    if forbidden_files:
        issues.append("Forbidden files changed (these require a separate phase):")
        for f in forbidden_files:
            issues.append(f"  - {f}")

        # Get uncommitted changes to provide correct remediation
        import subprocess
        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        uncommitted_set = set(uncommitted_result.stdout.strip().split("\n")) if uncommitted_result.returncode == 0 else set()

        uncommitted_forbidden = [f for f in forbidden_files if f in uncommitted_set]
        committed_forbidden = [f for f in forbidden_files if f not in uncommitted_set]

        if uncommitted_forbidden:
            issues.append(f"Fix uncommitted: git restore --worktree --staged -- {' '.join(uncommitted_forbidden)}")
        if committed_forbidden:
            if baseline_sha:
                issues.append(f"Fix committed: git restore --source={baseline_sha} -- {' '.join(committed_forbidden)}")
            else:
                issues.append(f"Fix committed: git revert <commits> (or restore: git restore --source=<baseline> -- {' '.join(committed_forbidden[:2])})")

        issues.append("")

    # Check out-of-scope changes
    allowed_drift = drift_gate.get("allowed_out_of_scope_changes", 0)

    if len(out_of_scope) > allowed_drift:
        issues.append(f"Out-of-scope changes detected ({len(out_of_scope)} files, {allowed_drift} allowed):")
        for f in out_of_scope:
            issues.append(f"  - {f}")
        issues.append("")

        # Determine which files are committed vs uncommitted for better remediation
        import subprocess

        # Get uncommitted changes
        uncommitted_result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True
        )
        uncommitted_set = set(uncommitted_result.stdout.strip().split("\n")) if uncommitted_result.returncode == 0 else set()

        # Classify out-of-scope files
        uncommitted_out = [f for f in out_of_scope if f in uncommitted_set]
        committed_out = [f for f in out_of_scope if f not in uncommitted_set]

        issues.append("Options to fix:")

        if uncommitted_out:
            issues.append(f"1. Revert uncommitted changes: git restore --worktree --staged -- {' '.join(uncommitted_out[:3])}")
            if len(uncommitted_out) > 3:
                issues.append(f"   (and {len(uncommitted_out) - 3} more)")

        if committed_out:
            if baseline_sha:
                issues.append(f"2. Restore committed files to baseline: git restore --source={baseline_sha} -- {' '.join(committed_out[:3])}")
            else:
                issues.append("2. Revert committed changes: git revert <commit-range> (or restore specific files)")
            if len(committed_out) > 3:
                issues.append(f"   (and {len(committed_out) - 3} more)")

        issues.append(f"3. Update phase scope in .repo/briefs/{phase['id']}.md")
        issues.append("4. Split into separate phase for out-of-scope work")

    return issues


def write_critique(phase_id: str, issues: List[str], gate_results: Dict[str, List[str]] = None):
    """Write critique files atomically (both .md and .json)."""
    import tempfile
    import os
    import json

    # Ensure critiques directory exists
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)

    # Markdown critique
    critique_content = f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

## Resolution

Please address the issues above and re-run:
```
./tools/phasectl.py review {phase_id}
```
"""

    critique_file = CRITIQUES_DIR / f"{phase_id}.md"

    # Write MD to temp file first (atomic operation)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_",
        suffix=".tmp"
    ) as tmp:
        tmp.write(critique_content)
        tmp_path = tmp.name

    # Atomic replace MD
    os.replace(tmp_path, critique_file)

    # JSON critique (machine-readable)
    if gate_results is None:
        gate_results = {}

    critique_json = {
        "phase": phase_id,
        "timestamp": time.time(),
        "passed": False,
        "issues": [
            {
                "gate": gate,
                "messages": msgs
            }
            for gate, msgs in gate_results.items() if msgs
        ],
        "total_issue_count": len(issues)
    }

    json_file = CRITIQUES_DIR / f"{phase_id}.json"

    # Write JSON to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_json_",
        suffix=".tmp"
    ) as tmp:
        json.dump(critique_json, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic replace JSON
    os.replace(tmp_path, json_file)

    # Clean up old approval files AFTER successful write
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    ok_json_file = CRITIQUES_DIR / f"{phase_id}.OK.json"
    if ok_file.exists():
        ok_file.unlink()
    if ok_json_file.exists():
        ok_json_file.unlink()

    print(f"📝 Critique written to {critique_file.relative_to(REPO_ROOT)}")
    print(f"📊 JSON critique: {json_file.relative_to(REPO_ROOT)}")


def write_approval(phase_id: str):
    """Write approval markers atomically (both .OK and .OK.json)."""
    import tempfile
    import os
    import json

    # Ensure critiques directory exists
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)

    approval_timestamp = time.time()
    approval_content = f"Phase {phase_id} approved at {approval_timestamp}\n"
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"

    # Write .OK to temp file first (atomic operation)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_",
        suffix=".tmp"
    ) as tmp:
        tmp.write(approval_content)
        tmp_path = tmp.name

    # Atomic replace .OK
    os.replace(tmp_path, ok_file)

    # JSON approval (machine-readable)
    approval_json = {
        "phase": phase_id,
        "timestamp": approval_timestamp,
        "passed": True,
        "approved_at": approval_timestamp
    }

    ok_json_file = CRITIQUES_DIR / f"{phase_id}.OK.json"

    # Write JSON to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_ok_json_",
        suffix=".tmp"
    ) as tmp:
        json.dump(approval_json, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic replace JSON
    os.replace(tmp_path, ok_json_file)

    # Clean up old critique files AFTER successful write
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    critique_json_file = CRITIQUES_DIR / f"{phase_id}.json"
    if critique_file.exists():
        critique_file.unlink()
    if critique_json_file.exists():
        critique_json_file.unlink()

    print(f"✅ Approval written to {ok_file.relative_to(REPO_ROOT)}")
    print(f"📊 JSON approval: {ok_json_file.relative_to(REPO_ROOT)}")


def judge_phase(phase_id: str):
    """Run all checks and produce verdict."""
    print(f"⚖️  Judging phase {phase_id}...")

    # Load plan
    plan = load_plan()

    try:
        phase = get_phase(plan, phase_id)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return 2

    # Load baseline SHA from CURRENT.json for consistent diffs
    baseline_sha = None
    current_file = REPO_DIR / "briefs/CURRENT.json"
    if current_file.exists():
        try:
            import json
            current = json.loads(current_file.read_text())
            baseline_sha = current.get("baseline_sha")
            if baseline_sha:
                print(f"  📍 Using baseline: {baseline_sha[:8]}...")
        except (json.JSONDecodeError, KeyError):
            pass  # Tolerate missing or malformed CURRENT.json

    # CRITICAL: Verify protocol integrity FIRST
    print("  🔐 Checking protocol integrity...")

    # Check phase binding (plan/manifest unchanged mid-phase)
    current_file = REPO_DIR / "briefs/CURRENT.json"
    if current_file.exists():
        try:
            import json
            current = json.loads(current_file.read_text())
            binding_issues = verify_phase_binding(REPO_ROOT, current)
            if binding_issues:
                write_critique(phase_id, binding_issues)
                return 1
        except (json.JSONDecodeError, KeyError):
            pass  # Tolerate missing or malformed CURRENT.json

    # Check protocol lock (judge/tools haven't been tampered with)
    lock_issues = verify_protocol_lock(REPO_ROOT, plan, phase_id, baseline_sha)
    if lock_issues:
        write_critique(phase_id, lock_issues)
        return 1

    # Run all checks - Phase → Gates → Verdict
    all_issues = []
    gate_results = {}  # Track results per gate for JSON output

    print("  🔍 Checking artifacts...")
    artifacts_issues = check_artifacts(phase)
    gate_results["artifacts"] = artifacts_issues
    all_issues.extend(artifacts_issues)

    print("  🔍 Checking tests...")
    tests_issues = check_gate_trace("tests", TRACES_DIR, "Tests")
    gate_results["tests"] = tests_issues
    all_issues.extend(tests_issues)

    # Lint check (optional)
    lint_gate = phase.get("gates", {}).get("lint", {})
    if lint_gate.get("must_pass", False):
        print("  🔍 Checking linting...")
        lint_issues = check_gate_trace("lint", TRACES_DIR, "Linting")
        gate_results["lint"] = lint_issues
        all_issues.extend(lint_issues)

    # Get changed files for docs and drift gates
    base_branch = plan.get("plan", {}).get("base_branch", "main")
    changed_files = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )

    print("  🔍 Checking documentation...")
    docs_issues = check_docs(phase, changed_files)
    gate_results["docs"] = docs_issues
    all_issues.extend(docs_issues)

    print("  🔍 Checking for plan drift...")
    drift_issues = check_drift(phase, plan, baseline_sha)
    gate_results["drift"] = drift_issues
    all_issues.extend(drift_issues)

    # LLM code review (optional)
    if LLM_JUDGE_AVAILABLE:
        llm_gate = phase.get("gates", {}).get("llm_review", {})
        if llm_gate.get("enabled", False):
            print("  🤖 Running LLM code review...")
            llm_issues = llm_code_review(phase, REPO_ROOT, plan, baseline_sha)
            gate_results["llm_review"] = llm_issues
            all_issues.extend(llm_issues)

    # Verdict (write functions handle cleanup atomically)
    if all_issues:
        write_critique(phase_id, all_issues, gate_results)
        return 1
    else:
        write_approval(phase_id)
        return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: judge.py <PHASE_ID>")
        return 1

    phase_id = sys.argv[1]

    try:
        return judge_phase(phase_id)
    except Exception as e:
        print(f"❌ Judge error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
