#!/usr/bin/env python3
"""
Phasectl: Blocking controller for judge-gated phases.

Usage:
  ./tools/phasectl.py review <PHASE_ID>  # Submit phase for review
  ./tools/phasectl.py next                # Advance to next phase
"""

import sys
import json
import time
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPO_DIR = REPO_ROOT / ".repo"
CRITIQUES_DIR = REPO_DIR / "critiques"
STATUS_DIR = REPO_DIR / "status"
BRIEFS_DIR = REPO_DIR / "briefs"
CURRENT_FILE = BRIEFS_DIR / "CURRENT.json"


def review_phase(phase_id: str):
    """Submit phase for review and block until judge provides feedback."""
    print(f"📋 Submitting phase {phase_id} for review...")

    # Mark phase as ready for review
    status_file = STATUS_DIR / f"{phase_id}.json"
    status_file.write_text(json.dumps({
        "phase_id": phase_id,
        "status": "reviewing",
        "submitted_at": time.time()
    }, indent=2))

    # Run tests
    print("🧪 Running tests...")
    result = subprocess.run([REPO_ROOT / "tools" / "run_tests.sh"],
                          capture_output=True, text=True)

    # Trigger judge
    print("⚖️  Invoking judge...")
    judge_result = subprocess.run(
        [REPO_ROOT / "tools" / "run_judge.sh", phase_id],
        capture_output=True,
        text=True
    )

    # Check for critique or OK
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"

    if ok_file.exists():
        print(f"✅ Phase {phase_id} approved!")
        status_file.write_text(json.dumps({
            "phase_id": phase_id,
            "status": "approved",
            "approved_at": time.time()
        }, indent=2))
        return 0
    elif critique_file.exists():
        print(f"❌ Phase {phase_id} needs revision:")
        print(critique_file.read_text())
        status_file.write_text(json.dumps({
            "phase_id": phase_id,
            "status": "needs_revision",
            "critique_at": time.time()
        }, indent=2))
        return 1
    else:
        print("⚠️  Judge did not produce feedback. Check logs.")
        return 2


def next_phase():
    """Advance to the next phase."""
    if not CURRENT_FILE.exists():
        print("❌ No CURRENT.json found")
        return 1

    current = json.loads(CURRENT_FILE.read_text())
    current_id = current["phase_id"]

    # Load plan to find next phase
    import yaml
    plan_file = REPO_DIR / "plan.yaml"
    with plan_file.open() as f:
        plan = yaml.safe_load(f)

    phases = plan["plan"]["phases"]
    current_idx = next((i for i, p in enumerate(phases) if p["id"] == current_id), None)

    if current_idx is None:
        print(f"❌ Current phase {current_id} not found in plan")
        return 1

    if current_idx + 1 >= len(phases):
        print("🎉 All phases complete!")
        return 0

    next_phase_data = phases[current_idx + 1]
    next_id = next_phase_data["id"]
    next_brief = BRIEFS_DIR / f"{next_id}.md"

    if not next_brief.exists():
        print(f"❌ Brief for {next_id} not found: {next_brief}")
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
