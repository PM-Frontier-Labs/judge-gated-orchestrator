#!/usr/bin/env python3
"""
Phasectl v2: User command interface.

Commands:
- start <phase>        Start a phase
- review <phase>       Submit for review
- justify-scope <phase> Justify out-of-scope changes
- acknowledge-orient   Acknowledge orient.sh reading
- reflect <phase>      Capture learnings
- next                 Advance to next phase
"""

import sys
import subprocess
from pathlib import Path

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.plan import load_plan, get_phase, get_brief, get_next_phase, PlanError
from lib.state import (
    get_current_phase, set_current_phase, clear_current_phase,
    acknowledge_orient, save_scope_justification, append_learning
)
from lib.git_ops import get_changed_files
from lib.scope import classify_files
from lib.traces import run_command_with_trace, build_test_command, build_lint_command

REPO_ROOT = Path.cwd()
REPO_DIR = REPO_ROOT / ".repo"
TRACES_DIR = REPO_DIR / "traces"


def cmd_start(phase_id: str):
    """Start a phase."""
    print(f"🚀 Starting phase {phase_id}...")
    print()
    
    try:
        plan = load_plan(REPO_ROOT)
        phase = get_phase(plan, phase_id)
        brief = get_brief(plan, phase_id, REPO_ROOT)
    except PlanError as e:
        print(f"❌ {e}")
        return 1
    
    # Set as current phase (captures baseline SHA)
    current = set_current_phase(phase_id, REPO_ROOT)
    
    print(f"✅ Phase {phase_id} activated")
    print(f"   Baseline: {current['baseline_sha'][:8]}...")
    print()
    
    # Display brief
    print("="*60)
    print(brief)
    print("="*60)
    print()
    
    # Show scope summary
    scope_config = phase.get("scope", {})
    if scope_config:
        print("📍 Scope:")
        include_patterns = scope_config.get("include", [])
        for pattern in include_patterns:
            print(f"   ✅ {pattern}")
        exclude_patterns = scope_config.get("exclude", [])
        for pattern in exclude_patterns:
            print(f"   ❌ {pattern}")
        print()
    
    print("Next steps:")
    print(f"  1. Implement the phase requirements")
    print(f"  2. Run: ./tools/phasectl.py review {phase_id}")
    print()
    
    return 0


def cmd_review(phase_id: str):
    """Submit phase for review."""
    print(f"📋 Reviewing phase {phase_id}...")
    print()
    
    # Check if phase is active
    current = get_current_phase(REPO_ROOT)
    if not current or current["phase_id"] != phase_id:
        print(f"❌ Phase {phase_id} is not active")
        print(f"   Run: ./tools/phasectl.py start {phase_id}")
        return 1
    
    try:
        plan = load_plan(REPO_ROOT)
        phase = get_phase(plan, phase_id)
    except PlanError as e:
        print(f"❌ {e}")
        return 1
    
    baseline_sha = current.get("baseline_sha")
    
    # Show changed files summary
    changed_files, warnings = get_changed_files(REPO_ROOT, baseline_sha)
    
    if changed_files:
        print(f"📝 Changed files ({len(changed_files)}):")
        for f in changed_files[:10]:
            print(f"   - {f}")
        if len(changed_files) > 10:
            print(f"   ... and {len(changed_files) - 10} more")
        print()
    else:
        print("⚠️  No changed files detected")
        print()
    
    # Run tests if configured
    tests_config = phase.get("gates", {}).get("tests", {})
    if tests_config:
        print("🧪 Running tests...")
        
        # Check for split tests
        if "unit" in tests_config:
            print("   - Unit tests...")
            cmd = build_test_command(phase, plan, "unit")
            exit_code = run_command_with_trace(cmd, REPO_ROOT, TRACES_DIR, "tests_unit")
            if exit_code == 0:
                print("     ✅ Pass")
            else:
                print(f"     ❌ Failed (exit {exit_code})")
        
        if "integration" in tests_config:
            print("   - Integration tests...")
            cmd = build_test_command(phase, plan, "integration")
            exit_code = run_command_with_trace(cmd, REPO_ROOT, TRACES_DIR, "tests_integration")
            if exit_code == 0:
                print("     ✅ Pass")
            else:
                print(f"     ❌ Failed (exit {exit_code})")
        
        if "unit" not in tests_config and "integration" not in tests_config:
            # Simple mode
            cmd = build_test_command(phase, plan, "simple")
            exit_code = run_command_with_trace(cmd, REPO_ROOT, TRACES_DIR, "tests")
            if exit_code == 0:
                print("   ✅ Pass")
            else:
                print(f"   ❌ Failed (exit {exit_code})")
        
        print()
    
    # Run lint if configured
    lint_config = phase.get("gates", {}).get("lint", {})
    if lint_config.get("must_pass", False):
        print("🔍 Running lint...")
        cmd = build_lint_command(phase, plan)
        exit_code = run_command_with_trace(cmd, REPO_ROOT, TRACES_DIR, "lint")
        if exit_code == 0:
            print("   ✅ Pass")
        else:
            print(f"   ❌ Failed (exit {exit_code})")
        print()
    
    # Invoke judge
    print("⚖️  Invoking judge...")
    print()
    
    judge_path = Path(__file__).parent / "judge.py"
    result = subprocess.run(
        [sys.executable, str(judge_path), phase_id],
        cwd=REPO_ROOT
    )
    
    return result.returncode


def cmd_justify_scope(phase_id: str):
    """Justify out-of-scope changes."""
    print(f"🤔 Justifying scope drift for {phase_id}...")
    print()
    
    current = get_current_phase(REPO_ROOT)
    if not current or current["phase_id"] != phase_id:
        print(f"❌ Phase {phase_id} is not active")
        return 1
    
    try:
        plan = load_plan(REPO_ROOT)
        phase = get_phase(plan, phase_id)
    except PlanError as e:
        print(f"❌ {e}")
        return 1
    
    baseline_sha = current.get("baseline_sha")
    
    # Get changed files and classify
    changed_files, _ = get_changed_files(REPO_ROOT, baseline_sha)
    
    scope_config = phase.get("scope", {})
    include_patterns = scope_config.get("include", [])
    exclude_patterns = scope_config.get("exclude", [])
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    if not out_of_scope:
        print("✅ No out-of-scope changes detected")
        return 0
    
    print(f"Out-of-scope files ({len(out_of_scope)}):")
    for f in out_of_scope:
        print(f"  - {f}")
    print()
    
    # Prompt for justification
    print("Please provide justification for these changes.")
    print("Explain why these out-of-scope modifications were necessary.")
    print()
    print("Enter justification (end with Ctrl+D or Ctrl+Z):")
    print("-" * 60)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    justification = "\n".join(lines).strip()
    
    if not justification:
        print()
        print("❌ No justification provided")
        return 1
    
    print()
    print("-" * 60)
    print()
    
    # Save justification
    save_scope_justification(phase_id, out_of_scope, justification, REPO_ROOT)
    
    print(f"✅ Justification recorded to .repo/scope_audit/{phase_id}.md")
    print()
    print("This will be reviewed by humans later.")
    print("Gates will now pass with this justification.")
    print()
    print("Re-run review:")
    print(f"  ./tools/phasectl.py review {phase_id}")
    print()
    
    return 0


def cmd_acknowledge_orient():
    """Acknowledge reading orient.sh."""
    print("📖 Orient Acknowledgment")
    print()
    
    current = get_current_phase(REPO_ROOT)
    if not current:
        print("❌ No active phase")
        print("   Run: ./tools/phasectl.py start <phase-id>")
        return 1
    
    phase_id = current["phase_id"]
    
    # Prompt for summary
    print("Please summarize what you learned from ./orient.sh:")
    print("(2-3 sentences about current state, progress, next steps)")
    print()
    print("Enter summary (end with Ctrl+D or Ctrl+Z):")
    print("-" * 60)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    summary = "\n".join(lines).strip()
    
    if not summary:
        print()
        print("❌ No summary provided")
        return 1
    
    print()
    print("-" * 60)
    print()
    
    # Save acknowledgment
    acknowledge_orient(phase_id, summary, REPO_ROOT)
    
    print(f"✅ Orient acknowledged for {phase_id}")
    print()
    print("Gates will now pass.")
    print()
    
    return 0


def cmd_reflect(phase_id: str):
    """Reflect on learnings after phase completion."""
    print(f"💭 Reflection: {phase_id}")
    print()
    
    # Check if phase is approved
    ok_file = REPO_DIR / "critiques" / f"{phase_id}.OK"
    if not ok_file.exists():
        print(f"❌ Phase {phase_id} is not approved yet")
        print(f"   Complete review first: ./tools/phasectl.py review {phase_id}")
        return 1
    
    print("What did you learn during this phase?")
    print("Consider:")
    print("  - What worked well?")
    print("  - What didn't work?")
    print("  - What would you do differently?")
    print("  - Any insights for future phases?")
    print()
    print("Enter reflection (end with Ctrl+D or Ctrl+Z):")
    print("-" * 60)
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    learning = "\n".join(lines).strip()
    
    if not learning:
        print()
        print("❌ No reflection provided")
        return 1
    
    print()
    print("-" * 60)
    print()
    
    # Save learning
    append_learning(phase_id, learning, REPO_ROOT)
    
    print(f"✅ Learning recorded to .repo/learnings.md")
    print()
    print("This will be shown in future orient.sh output.")
    print()
    
    return 0


def cmd_next():
    """Advance to next phase."""
    print("➡️  Advancing to next phase...")
    print()
    
    current = get_current_phase(REPO_ROOT)
    if not current:
        print("❌ No active phase")
        return 1
    
    phase_id = current["phase_id"]
    
    # Check if current phase is approved
    ok_file = REPO_DIR / "critiques" / f"{phase_id}.OK"
    if not ok_file.exists():
        print(f"❌ Phase {phase_id} is not approved yet")
        print(f"   Run: ./tools/phasectl.py review {phase_id}")
        return 1
    
    try:
        plan = load_plan(REPO_ROOT)
        next_phase = get_next_phase(plan, phase_id)
    except PlanError as e:
        print(f"❌ {e}")
        return 1
    
    if not next_phase:
        print(f"🎉 All phases complete!")
        print()
        clear_current_phase(REPO_ROOT)
        return 0
    
    next_id = next_phase["id"]
    
    print(f"✅ Current phase {phase_id} complete")
    print(f"➡️  Next phase: {next_id}")
    print()
    print("Before starting, please:")
    print("  1. Run: ./orient.sh")
    print("  2. Review the current state")
    print(f"  3. Start next phase: ./tools/phasectl.py start {next_id}")
    print()
    
    return 0


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  phasectl.py start <phase>")
        print("  phasectl.py review <phase>")
        print("  phasectl.py justify-scope <phase>")
        print("  phasectl.py acknowledge-orient")
        print("  phasectl.py reflect <phase>")
        print("  phasectl.py next")
        return 1
    
    command = sys.argv[1]
    
    if command == "start":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py start <phase-id>")
            return 1
        return cmd_start(sys.argv[2])
    
    elif command == "review":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py review <phase-id>")
            return 1
        return cmd_review(sys.argv[2])
    
    elif command == "justify-scope":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py justify-scope <phase-id>")
            return 1
        return cmd_justify_scope(sys.argv[2])
    
    elif command == "acknowledge-orient":
        return cmd_acknowledge_orient()
    
    elif command == "reflect":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py reflect <phase-id>")
            return 1
        return cmd_reflect(sys.argv[2])
    
    elif command == "next":
        return cmd_next()
    
    else:
        print(f"Unknown command: {command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

