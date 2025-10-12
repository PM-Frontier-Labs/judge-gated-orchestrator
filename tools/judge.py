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
    """Check that required artifacts exist."""
    issues = []
    artifacts = phase.get("artifacts", {}).get("must_exist", [])

    for artifact in artifacts:
        path = REPO_ROOT / artifact
        if not path.exists():
            issues.append(f"Missing required artifact: {artifact}")

    return issues




def check_docs(phase: Dict[str, Any]) -> List[str]:
    """Check that documentation was updated."""
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

    # Check if docs exist and are not empty
    for doc in must_update:
        # Handle section anchors like "docs/mvp.md#feature"
        doc_path = doc.split("#")[0]
        path = REPO_ROOT / doc_path

        if not path.exists():
            issues.append(f"Documentation not found: {doc_path}")
        elif path.stat().st_size == 0:
            issues.append(f"Documentation is empty: {doc_path}")

    return issues




def check_drift(phase: Dict[str, Any], plan: Dict[str, Any]) -> List[str]:
    """Check for changes outside phase scope (plan drift)."""
    issues = []

    # Check if drift gate is enabled
    drift_gate = phase.get("gates", {}).get("drift")
    if not drift_gate:
        return []  # Drift checking not enabled for this phase

    # Get base branch
    base_branch = plan.get("plan", {}).get("base_branch", "main")

    # Get changed files
    changed_files = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch
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
        issues.append(f"Fix: git checkout HEAD {' '.join(forbidden_files)}")
        issues.append("")

    # Check out-of-scope changes
    allowed_drift = drift_gate.get("allowed_out_of_scope_changes", 0)

    if len(out_of_scope) > allowed_drift:
        issues.append(f"Out-of-scope changes detected ({len(out_of_scope)} files, {allowed_drift} allowed):")
        for f in out_of_scope:
            issues.append(f"  - {f}")
        issues.append("")
        issues.append("Options to fix:")
        issues.append(f"1. Revert: git checkout HEAD {' '.join(out_of_scope)}")
        issues.append(f"2. Update phase scope in .repo/briefs/{phase['id']}.md")
        issues.append("3. Split into separate phase for out-of-scope work")

    return issues


def write_critique(phase_id: str, issues: List[str]):
    """Write a critique file."""
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    critique_file.write_text(f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

## Resolution

Please address the issues above and re-run:
```
./tools/phasectl.py review {phase_id}
```
""")
    print(f"📝 Critique written to {critique_file.relative_to(REPO_ROOT)}")


def write_approval(phase_id: str):
    """Write an approval marker."""
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    ok_file.write_text(f"Phase {phase_id} approved at {time.time()}\n")
    print(f"✅ Approval written to {ok_file.relative_to(REPO_ROOT)}")


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

    # Run all checks - Phase → Gates → Verdict
    all_issues = []

    print("  🔍 Checking artifacts...")
    all_issues.extend(check_artifacts(phase))

    print("  🔍 Checking tests...")
    all_issues.extend(check_gate_trace("tests", TRACES_DIR, "Tests"))

    # Lint check (optional)
    lint_gate = phase.get("gates", {}).get("lint", {})
    if lint_gate.get("must_pass", False):
        print("  🔍 Checking linting...")
        all_issues.extend(check_gate_trace("lint", TRACES_DIR, "Linting"))

    print("  🔍 Checking documentation...")
    all_issues.extend(check_docs(phase))

    print("  🔍 Checking for plan drift...")
    all_issues.extend(check_drift(phase, plan))

    # LLM code review (optional)
    if LLM_JUDGE_AVAILABLE:
        llm_gate = phase.get("gates", {}).get("llm_review", {})
        if llm_gate.get("enabled", False):
            print("  🤖 Running LLM code review...")
            all_issues.extend(llm_code_review(phase, REPO_ROOT))

    # Clean up old critiques/approvals
    for old_file in CRITIQUES_DIR.glob(f"{phase_id}.*"):
        old_file.unlink()

    # Verdict
    if all_issues:
        write_critique(phase_id, all_issues)
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
