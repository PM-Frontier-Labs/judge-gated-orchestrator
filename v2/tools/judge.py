#!/usr/bin/env python3
"""
Judge v2: Simple gate coordinator.

Responsibilities:
1. Load phase configuration
2. Run all enabled gates
3. Write critique or approval

That's it. No ML, no patterns, no budget shaping.
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.plan import load_plan, get_phase, PlanError
from lib.state import get_current_phase, StateError
from lib.gates import (
    check_artifacts,
    check_tests,
    check_lint,
    check_docs,
    check_scope,
    check_llm_review,
    check_orient_acknowledgment
)
from lib.git_ops import get_changed_files

REPO_ROOT = Path.cwd()
REPO_DIR = REPO_ROOT / ".repo"
CRITIQUES_DIR = REPO_DIR / "critiques"
TRACES_DIR = REPO_DIR / "traces"


def judge_phase(phase_id: str) -> int:
    """
    Run all gates for phase and produce verdict.
    
    Returns:
        0 = Approved
        1 = Rejected (needs fixes)
        2 = Error (judge couldn't run)
    """
    print(f"⚖️  Judging phase {phase_id}...")
    
    # Load plan and phase
    try:
        plan = load_plan(REPO_ROOT)
        phase = get_phase(plan, phase_id)
    except PlanError as e:
        print(f"❌ {e}")
        return 2
    
    # Get current phase state (for baseline SHA)
    current = get_current_phase(REPO_ROOT)
    if not current or current["phase_id"] != phase_id:
        print(f"❌ Phase {phase_id} is not the current active phase")
        print(f"   Run: ./v2/tools/phasectl.py start {phase_id}")
        return 2
    
    baseline_sha = current.get("baseline_sha")
    
    # Get changed files
    changed_files, warnings = get_changed_files(
        REPO_ROOT,
        baseline_sha=baseline_sha,
        include_uncommitted=True
    )
    
    for warning in warnings:
        print(f"  ⚠️  {warning}")
    
    # Run all gates
    print("  🔍 Running gates...")
    
    all_issues = []
    gate_results = {}
    
    # Gate 1: Artifacts
    print("    - Artifacts...")
    issues = check_artifacts(phase, REPO_ROOT)
    gate_results["artifacts"] = issues
    all_issues.extend(issues)
    if issues:
        print(f"      ❌ {len(issues)} issues")
    else:
        print("      ✅ Pass")
    
    # Gate 2: Tests
    print("    - Tests...")
    issues = check_tests(phase, REPO_ROOT, TRACES_DIR)
    gate_results["tests"] = issues
    all_issues.extend(issues)
    if issues:
        print(f"      ❌ {len(issues)} issues")
    else:
        print("      ✅ Pass")
    
    # Gate 3: Lint
    lint_config = phase.get("gates", {}).get("lint", {})
    if lint_config.get("must_pass", False):
        print("    - Lint...")
        issues = check_lint(phase, REPO_ROOT, TRACES_DIR)
        gate_results["lint"] = issues
        all_issues.extend(issues)
        if issues:
            print(f"      ❌ {len(issues)} issues")
        else:
            print("      ✅ Pass")
    
    # Gate 4: Docs
    print("    - Docs...")
    issues = check_docs(phase, changed_files, REPO_ROOT)
    gate_results["docs"] = issues
    all_issues.extend(issues)
    if issues:
        print(f"      ❌ {len(issues)} issues")
    else:
        print("      ✅ Pass")
    
    # Gate 5: Scope
    drift_config = phase.get("gates", {}).get("drift")
    if drift_config:
        print("    - Scope...")
        issues = check_scope(phase, changed_files, REPO_ROOT, baseline_sha)
        gate_results["scope"] = issues
        all_issues.extend(issues)
        if issues:
            print(f"      ❌ {len(issues)} issues")
        else:
            print("      ✅ Pass")
    
    # Gate 6: LLM Review (optional)
    llm_config = phase.get("gates", {}).get("llm_review", {})
    if llm_config.get("enabled", False):
        print("    - LLM Review...")
        issues = check_llm_review(phase, plan, changed_files, REPO_ROOT, baseline_sha)
        gate_results["llm_review"] = issues
        all_issues.extend(issues)
        if issues:
            print(f"      ❌ {len(issues)} issues")
        else:
            print("      ✅ Pass")
    
    # Gate 7: Orient Acknowledgment
    print("    - Orient Acknowledgment...")
    issues = check_orient_acknowledgment(phase, REPO_ROOT)
    gate_results["orient"] = issues
    all_issues.extend(issues)
    if issues:
        print(f"      ❌ {len(issues)} issues")
    else:
        print("      ✅ Pass")
    
    # Verdict
    print()
    time.sleep(0.5)
    
    if all_issues:
        print("😤 VERDICT: REJECTED!")
        print("   Issues found. Please address and resubmit.")
        print()
        _write_critique(phase_id, all_issues, gate_results)
        return 1
    else:
        print("🎉 VERDICT: APPROVED!")
        print("   Excellent work! Phase complete.")
        print()
        _write_approval(phase_id)
        return 0


def _write_critique(phase_id: str, issues: List[str], gate_results: Dict[str, List[str]]):
    """Write critique file."""
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)
    
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    
    content = f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

## Resolution

Please fix the issues above and re-run:
```
./v2/tools/phasectl.py review {phase_id}
```

## Gate Results

{_format_gate_results(gate_results)}
"""
    
    critique_file.write_text(content)
    
    print(f"📝 Critique: {critique_file.relative_to(REPO_ROOT)}")
    
    # Clean up approval files if they exist
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    if ok_file.exists():
        ok_file.unlink()


def _write_approval(phase_id: str):
    """Write approval marker."""
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)
    
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    
    content = f"Phase {phase_id} approved at {time.time()}\n"
    ok_file.write_text(content)
    
    print(f"✅ Approval: {ok_file.relative_to(REPO_ROOT)}")
    
    # Clean up critique files if they exist
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    if critique_file.exists():
        critique_file.unlink()


def _format_gate_results(gate_results: Dict[str, List[str]]) -> str:
    """Format gate results for critique."""
    lines = []
    for gate_name, issues in gate_results.items():
        if issues:
            lines.append(f"**{gate_name}:** ❌ Failed")
            for issue in issues:
                lines.append(f"  - {issue}")
        else:
            lines.append(f"**{gate_name}:** ✅ Passed")
    return "\n".join(lines)


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
