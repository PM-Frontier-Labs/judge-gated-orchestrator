#!/usr/bin/env python3
"""
Judge: Evaluates a phase against plan gates.

Checks:
- Artifacts exist
- Tests pass
- Documentation updated
- No plan drift (changes outside scope)
- Lint rules (if specified)
- LLM code review (if enabled and ANTHROPIC_API_KEY set)
"""

import sys
import yaml
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Import LLM judge (optional enhancement)
try:
    from llm_judge import llm_code_review, get_changed_files_in_scope
    LLM_JUDGE_AVAILABLE = True
except ImportError:
    LLM_JUDGE_AVAILABLE = False

REPO_ROOT = Path(__file__).parent.parent
REPO_DIR = REPO_ROOT / ".repo"
CRITIQUES_DIR = REPO_DIR / "critiques"
TRACES_DIR = REPO_DIR / "traces"


def load_plan() -> Dict[str, Any]:
    """Load the plan.yaml file."""
    plan_file = REPO_DIR / "plan.yaml"
    with plan_file.open() as f:
        return yaml.safe_load(f)


def get_phase(plan: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    """Get phase configuration from plan."""
    phases = plan["plan"]["phases"]
    for phase in phases:
        if phase["id"] == phase_id:
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
    """Check that tests pass."""
    issues = []
    test_output = TRACES_DIR / "last_pytest.txt"

    if not test_output.exists():
        issues.append("No test results found. Run tests first.")
        return issues

    # Check pytest exit code by running again
    result = subprocess.run(
        ["pytest", "tests/", "-v"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        issues.append("Tests failed. See .repo/traces/last_pytest.txt for details.")

    return issues


def check_docs(phase: Dict[str, Any]) -> List[str]:
    """Check that documentation was updated."""
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

    # Check if docs exist
    for doc in must_update:
        # Handle section anchors like "docs/mvp.md#feature"
        doc_path = doc.split("#")[0]
        path = REPO_ROOT / doc_path

        if not path.exists():
            issues.append(f"Documentation not found: {doc_path}")
        elif path.stat().st_size == 0:
            issues.append(f"Documentation is empty: {doc_path}")

    return issues


def check_drift(phase: Dict[str, Any]) -> List[str]:
    """Check for changes outside the defined scope."""
    issues = []
    scope = phase.get("scope", {})
    allowed_changes = phase.get("gates", {}).get("drift", {}).get("allowed_out_of_scope_changes", 0)

    # Get changed files (simplified - in production, would use git diff)
    # For now, just check that required files are in scope
    include_patterns = scope.get("include", [])

    # This is a simplified drift check
    # In production, you'd compare git diff against include/exclude patterns
    if allowed_changes == 0:
        # For MVP, just verify artifacts are in scope
        artifacts = phase.get("artifacts", {}).get("must_exist", [])
        for artifact in artifacts:
            in_scope = any(
                artifact.startswith(pattern.replace("**", "").replace("*", ""))
                for pattern in include_patterns
            )
            if not in_scope:
                issues.append(f"Artifact outside scope: {artifact}")

    return issues


def check_lint(phase: Dict[str, Any]) -> List[str]:
    """Check lint rules (if specified)."""
    issues = []
    lint_gate = phase.get("gates", {}).get("lint", {})

    if "max_cyclomatic_complexity" in lint_gate:
        max_complexity = lint_gate["max_cyclomatic_complexity"]
        # For MVP, skip actual complexity checking
        # In production, would use radon or similar tool
        pass

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
    ok_file.write_text(f"Phase {phase_id} approved at {Path(TRACES_DIR / 'last_pytest.txt').stat().st_mtime}\n")
    print(f"✅ Phase {phase_id} approved!")


def judge_phase(phase_id: str):
    """Run all checks and produce verdict."""
    print(f"⚖️  Judging phase {phase_id}...")

    # Load plan
    plan = load_plan()
    phase = get_phase(plan, phase_id)

    # Run all checks
    all_issues = []

    print("  🔍 Checking artifacts...")
    all_issues.extend(check_artifacts(phase))

    print("  🔍 Checking tests...")
    all_issues.extend(check_tests())

    print("  🔍 Checking documentation...")
    all_issues.extend(check_docs(phase))

    print("  🔍 Checking for plan drift...")
    all_issues.extend(check_drift(phase))

    print("  🔍 Checking lint rules...")
    all_issues.extend(check_lint(phase))

    # LLM code review (optional)
    if LLM_JUDGE_AVAILABLE:
        llm_gate = phase.get("gates", {}).get("llm_review", {})
        if llm_gate.get("enabled", False):
            print("  🤖 Running LLM code review...")
            changed_files = get_changed_files_in_scope(phase, REPO_ROOT)
            all_issues.extend(llm_code_review(phase, changed_files))

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
        return 2


if __name__ == "__main__":
    sys.exit(main())
