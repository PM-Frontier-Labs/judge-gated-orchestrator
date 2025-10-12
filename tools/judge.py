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
import subprocess
import fnmatch
from pathlib import Path
from typing import Dict, List, Any

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

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


def check_tests() -> List[str]:
    """Check that tests passed (read from trace file)."""
    issues = []
    trace_file = TRACES_DIR / "last_test.txt"

    if not trace_file.exists():
        issues.append("No test results found. Tests may not have run.")
        return issues

    # Read trace file
    trace_content = trace_file.read_text()
    lines = trace_content.split("\n")

    # Parse exit code
    exit_code = None
    for line in lines:
        if line.startswith("Exit code:"):
            try:
                exit_code = int(line.split(":")[1].strip())
                break
            except (ValueError, IndexError):
                pass

    if exit_code is None:
        issues.append("Could not parse test exit code from trace")
    elif exit_code != 0:
        issues.append(f"Tests failed with exit code {exit_code}. See .repo/traces/last_test.txt for details.")

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


def get_changed_files(base_branch: str) -> List[str]:
    """Get list of files changed from base branch using git."""
    try:
        # First, get uncommitted changes (staged and unstaged)
        result = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        uncommitted = [f for f in result.stdout.strip().split("\n") if f]

        # Then, get committed changes from base branch
        result = subprocess.run(
            ["git", "merge-base", "HEAD", base_branch],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        merge_base = result.stdout.strip()

        result = subprocess.run(
            ["git", "diff", "--name-only", f"{merge_base}...HEAD"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        committed = [f for f in result.stdout.strip().split("\n") if f]

        # Combine both, remove duplicates
        all_changes = list(set(uncommitted + committed))
        return [f for f in all_changes if f]  # Filter empty strings

    except subprocess.CalledProcessError:
        # Not a git repo or base branch doesn't exist
        return []


def matches_pattern(path: str, patterns: List[str]) -> bool:
    """Check if path matches any glob pattern."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


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
    changed_files = get_changed_files(base_branch)

    if not changed_files:
        return []  # No changes or not a git repo

    # Get scope patterns
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    if not include_patterns:
        return []  # No scope defined, can't check drift

    # Classify files
    in_scope = []
    out_of_scope = []

    for file_path in changed_files:
        # Check if file matches include patterns
        included = matches_pattern(file_path, include_patterns)
        # Check if file matches exclude patterns
        excluded = matches_pattern(file_path, exclude_patterns)

        if included and not excluded:
            in_scope.append(file_path)
        else:
            out_of_scope.append(file_path)

    # Check forbidden patterns
    drift_rules = phase.get("drift_rules", {})
    forbid_patterns = drift_rules.get("forbid_changes", [])

    if forbid_patterns:
        forbidden_files = [f for f in changed_files
                          if matches_pattern(f, forbid_patterns)]
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
        issues.append(f"3. Split into separate phase for out-of-scope work")

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

    # Run all checks
    all_issues = []

    print("  🔍 Checking artifacts...")
    all_issues.extend(check_artifacts(phase))

    print("  🔍 Checking tests...")
    all_issues.extend(check_tests())

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
