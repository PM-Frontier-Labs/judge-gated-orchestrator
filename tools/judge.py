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
