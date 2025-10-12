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
import fnmatch
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
        print("   Install it or update test_command in .repo/plan.yaml")
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


def run_lint(plan, phase_id):
    """Run linter and save results to trace file."""
    # Check if lint gate is enabled for this phase
    phases = plan.get("plan", {}).get("phases", [])
    phase = next((p for p in phases if p["id"] == phase_id), None)

    if not phase:
        return None

    lint_gate = phase.get("gates", {}).get("lint", {})
    if not lint_gate.get("must_pass", False):
        return None  # Lint not enabled for this phase

    print("🔍 Running linter...")

    # Get lint command from plan, default to ruff
    lint_config = plan.get("plan", {}).get("lint_command", {})
    if isinstance(lint_config, str):
        lint_cmd = lint_config.split()
    elif isinstance(lint_config, dict):
        lint_cmd = lint_config.get("command", "ruff check .").split()
    else:
        lint_cmd = ["ruff", "check", "."]

    # Check if linter exists
    try:
        # For ruff, use 'ruff --version' not 'ruff check --version'
        version_cmd = [lint_cmd[0], "--version"] if lint_cmd[0] != "ruff" else ["ruff", "--version"]
        subprocess.run(version_cmd,
                      capture_output=True,
                      check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"❌ Error: {lint_cmd[0]} not installed")
        print("   Install it or update lint_command in .repo/plan.yaml")
        return None

    # Run linter and capture output
    result = subprocess.run(
        lint_cmd,
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )

    # Save results to trace
    TRACES_DIR.mkdir(parents=True, exist_ok=True)
    trace_file = TRACES_DIR / "last_lint.txt"
    trace_file.write_text(
        f"Exit code: {result.returncode}\n"
        f"Timestamp: {time.time()}\n"
        f"\n=== STDOUT ===\n{result.stdout}\n"
        f"\n=== STDERR ===\n{result.stderr}\n"
    )

    return result.returncode


def get_changed_files(base_branch: str) -> list:
    """Get list of files changed from base branch."""
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
        return []


def matches_pattern(path: str, patterns: list) -> bool:
    """Check if path matches any glob pattern."""
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def show_diff_summary(phase_id: str, plan: dict):
    """Show summary of changed files vs phase scope."""
    # Get phase config
    phases = plan.get("plan", {}).get("phases", [])
    phase = next((p for p in phases if p["id"] == phase_id), None)

    if not phase:
        return  # Can't show summary without phase config

    # Get base branch
    base_branch = plan.get("plan", {}).get("base_branch", "main")

    # Get changed files
    changed_files = get_changed_files(base_branch)

    if not changed_files:
        print("📊 No changes detected")
        return

    # Get scope patterns
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    if not include_patterns:
        print(f"📊 {len(changed_files)} files changed (no scope defined)")
        return

    # Classify files
    in_scope = []
    out_of_scope = []

    for file_path in changed_files:
        included = matches_pattern(file_path, include_patterns)
        excluded = matches_pattern(file_path, exclude_patterns)

        if included and not excluded:
            in_scope.append(file_path)
        else:
            out_of_scope.append(file_path)

    # Show summary
    print("📊 Change Summary:")
    print()

    if in_scope:
        print(f"✅ In scope ({len(in_scope)} files):")
        for f in in_scope[:10]:  # Show first 10
            print(f"  - {f}")
        if len(in_scope) > 10:
            print(f"  ... and {len(in_scope) - 10} more")
        print()

    if out_of_scope:
        print(f"❌ Out of scope ({len(out_of_scope)} files):")
        for f in out_of_scope:
            print(f"  - {f}")
        print()

        # Check drift gate
        drift_gate = phase.get("gates", {}).get("drift", {})
        allowed = drift_gate.get("allowed_out_of_scope_changes", 0)

        print(f"⚠️  Drift limit: {allowed} files allowed, {len(out_of_scope)} found")
        print()

        if len(out_of_scope) > allowed:
            print("💡 Fix options:")
            print(f"   1. Revert: git checkout HEAD {' '.join(out_of_scope[:3])}{'...' if len(out_of_scope) > 3 else ''}")
            print(f"   2. Update scope in .repo/briefs/{phase_id}.md")
            print("   3. Split into separate phase")
            print()

    # Check forbidden files
    drift_rules = phase.get("drift_rules", {})
    forbid_patterns = drift_rules.get("forbid_changes", [])

    if forbid_patterns:
        forbidden_files = [f for f in changed_files if matches_pattern(f, forbid_patterns)]
        if forbidden_files:
            print(f"🚫 Forbidden files changed ({len(forbidden_files)}):")
            for f in forbidden_files:
                print(f"  - {f}")
            print()
            print(f"   These require a separate phase. Revert: git checkout HEAD {' '.join(forbidden_files)}")
            print()


def review_phase(phase_id: str):
    """Submit phase for review and block until judge provides feedback."""
    print(f"📋 Submitting phase {phase_id} for review...")
    print()

    # Load plan
    plan = load_plan()

    # Show diff summary
    show_diff_summary(phase_id, plan)

    # Run tests
    test_exit_code = run_tests(plan)
    if test_exit_code is None:
        return 2  # Test runner not available

    # Run lint (if enabled for this phase)
    run_lint(plan, phase_id)
    # Note: Lint failures are checked by judge, not here

    # Trigger judge
    print("⚖️  Invoking judge...")
    subprocess.run(
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
