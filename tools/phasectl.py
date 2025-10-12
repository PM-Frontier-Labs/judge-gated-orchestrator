#!/usr/bin/env python3
"""
Phasectl: Controller for gated phase protocol.

Usage:
  ./tools/phasectl.py review <PHASE_ID>  # Submit phase for review
  ./tools/phasectl.py next                # Advance to next phase
"""

import sys
import json
import time
import subprocess
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

REPO_ROOT = Path(__file__).parent.parent
REPO_DIR = REPO_ROOT / ".repo"
CRITIQUES_DIR = REPO_DIR / "critiques"
TRACES_DIR = REPO_DIR / "traces"
BRIEFS_DIR = REPO_DIR / "briefs"
CURRENT_FILE = BRIEFS_DIR / "CURRENT.json"


def load_plan():
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


def run_tests(plan):
    """Run tests and save results to trace file."""
    print("🧪 Running tests...")

    # Get test command from plan, default to pytest
    test_config = plan.get("plan", {}).get("test_command", {})
    if isinstance(test_config, str):
        test_cmd = test_config.split()
    elif isinstance(test_config, dict):
        test_cmd = test_config.get("command", "pytest tests/ -v").split()
    else:
        test_cmd = ["pytest", "tests/", "-v"]

    # Check if test runner exists
    try:
        subprocess.run([test_cmd[0], "--version"],
                      capture_output=True,
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ Error: {test_cmd[0]} not installed")
        print(f"   Install it or update test_command in .repo/plan.yaml")
        return None

    # Run tests and capture output
    result = subprocess.run(
        test_cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )

    # Save results to trace
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    trace_file = TRACES_DIR / "last_test.txt"
    trace_file.write_text(
        f"Exit code: {result.returncode}\n"
        f"Timestamp: {time.time()}\n"
        f"\n=== STDOUT ===\n{result.stdout}\n"
        f"\n=== STDERR ===\n{result.stderr}\n"
    )

    return result.returncode


def review_phase(phase_id: str):
    """Submit phase for review and block until judge provides feedback."""
    print(f"📋 Submitting phase {phase_id} for review...")

    # Load plan
    plan = load_plan()

    # Run tests
    test_exit_code = run_tests(plan)
    if test_exit_code is None:
        return 2  # Test runner not available

    # Trigger judge
    print("⚖️  Invoking judge...")
    judge_result = subprocess.run(
        [sys.executable, REPO_ROOT / "tools" / "judge.py", phase_id],
        cwd=REPO_ROOT
    )

    # Check for critique or OK
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"

    if ok_file.exists():
        print(f"✅ Phase {phase_id} approved!")
        return 0
    elif critique_file.exists():
        print(f"❌ Phase {phase_id} needs revision:")
        print()
        print(critique_file.read_text())
        return 1
    else:
        print("⚠️  Judge did not produce feedback. Check for errors above.")
        return 2


def next_phase():
    """Advance to the next phase."""
    if not CURRENT_FILE.exists():
        print("❌ Error: No CURRENT.json found")
        return 1

    try:
        current = json.loads(CURRENT_FILE.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in {CURRENT_FILE}: {e}")
        return 1

    current_id = current.get("phase_id")
    if not current_id:
        print("❌ Error: No phase_id in CURRENT.json")
        return 1

    # Load plan
    plan = load_plan()
    phases = plan.get("plan", {}).get("phases", [])

    if not phases:
        print("❌ Error: No phases defined in plan.yaml")
        return 1

    # Find current phase
    current_idx = next((i for i, p in enumerate(phases) if p["id"] == current_id), None)

    if current_idx is None:
        print(f"❌ Error: Current phase {current_id} not found in plan")
        return 1

    # Check if current phase is approved
    ok_file = CRITIQUES_DIR / f"{current_id}.OK"
    if not ok_file.exists():
        print(f"❌ Error: Phase {current_id} not yet approved")
        print(f"   Run: ./tools/phasectl.py review {current_id}")
        return 1

    # Check if we're at the last phase
    if current_idx + 1 >= len(phases):
        print("🎉 All phases complete!")
        return 0

    # Advance to next phase
    next_phase_data = phases[current_idx + 1]
    next_id = next_phase_data["id"]
    next_brief = BRIEFS_DIR / f"{next_id}.md"

    if not next_brief.exists():
        print(f"❌ Error: Brief for {next_id} not found: {next_brief}")
        return 1

    # Update CURRENT.json
    CURRENT_FILE.write_text(json.dumps({
        "phase_id": next_id,
        "brief_path": str(next_brief.relative_to(REPO_ROOT)),
        "status": "active",
        "started_at": time.time()
    }, indent=2))

    print(f"➡️  Advanced to phase {next_id}")
    print(f"📄 Brief: {next_brief.relative_to(REPO_ROOT)}")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1]

    if command == "review":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py review <PHASE_ID>")
            return 1
        return review_phase(sys.argv[2])

    elif command == "next":
        return next_phase()

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
