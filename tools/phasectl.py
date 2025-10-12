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
import shlex
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# Import shared utilities
from lib.git_ops import get_changed_files
from lib.scope import classify_files, check_forbidden_files
from lib.traces import run_command_with_trace

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


def run_tests(plan, phase=None):
    """Run tests and save results to trace file."""
    print("🧪 Running tests...")

    # Get test command from plan
    test_config = plan.get("plan", {}).get("test_command", {})
    if isinstance(test_config, str):
        test_cmd = shlex.split(test_config)
    elif isinstance(test_config, dict):
        test_cmd = shlex.split(test_config.get("command", "pytest tests/ -v"))
    else:
        test_cmd = ["pytest", "tests/", "-v"]

    # Apply test scoping and quarantine if phase provided
    if phase:
        test_gate = phase.get("gates", {}).get("tests", {})

        # Test scoping: "scope" | "all" | custom path
        test_scope = test_gate.get("test_scope", "all")

        if test_scope == "scope":
            # Filter test paths to match phase scope using pathspec
            scope_patterns = phase.get("scope", {}).get("include", [])
            exclude_patterns = phase.get("scope", {}).get("exclude", [])

            # Use pathspec to find matching test files/directories
            try:
                import pathspec

                # Create pathspec for include patterns
                include_spec = pathspec.PathSpec.from_lines('gitwildmatch', scope_patterns)
                exclude_spec = None
                if exclude_patterns:
                    exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', exclude_patterns)

                # Find all test files in tests/ directory
                test_paths = set()
                tests_dir = REPO_ROOT / "tests"
                if tests_dir.exists():
                    for test_file in tests_dir.rglob("test_*.py"):
                        rel_path = str(test_file.relative_to(REPO_ROOT))
                        # Check if matches include patterns
                        if include_spec.match_file(rel_path):
                            # Check if not excluded
                            if not exclude_spec or not exclude_spec.match_file(rel_path):
                                # Add parent directory for better pytest organization
                                test_dir = str(test_file.parent.relative_to(REPO_ROOT))
                                if test_dir.startswith("tests"):
                                    test_paths.add(test_dir)

                if test_paths:
                    print(f"  📍 Test scope: Running tests in {len(test_paths)} directories")
                    # Replace default test path with scoped paths
                    new_cmd = [test_cmd[0]]  # Keep pytest
                    new_cmd.extend(sorted(test_paths))
                    # Keep flags (e.g., -v)
                    new_cmd.extend([arg for arg in test_cmd[1:] if arg.startswith("-")])
                    test_cmd = new_cmd
                else:
                    print("  ⚠️  No test files match scope patterns - running all tests")

            except ImportError:
                # Fallback to simple string matching if pathspec not available
                print("  ⚠️  pathspec not available - using simple pattern matching")
                test_paths = []
                for pattern in scope_patterns:
                    if pattern.startswith("tests/"):
                        base_path = pattern.split("*")[0].rstrip("/")
                        if base_path not in test_paths:
                            test_paths.append(base_path)

                if test_paths:
                    print(f"  📍 Test scope: Running tests in {len(test_paths)} directories (fallback mode)")
                    new_cmd = [test_cmd[0]]
                    new_cmd.extend(test_paths)
                    new_cmd.extend([arg for arg in test_cmd[1:] if arg.startswith("-")])
                    test_cmd = new_cmd

        # Quarantine list: tests expected to fail
        quarantine = test_gate.get("quarantine", [])
        if quarantine:
            print(f"  ⚠️  Quarantined tests ({len(quarantine)} tests will be skipped):")
            for item in quarantine:
                test_path = item.get("path", "")
                reason = item.get("reason", "No reason provided")
                print(f"     - {test_path}")
                print(f"       Reason: {reason}")
                # Add --deselect for pytest
                test_cmd.extend(["--deselect", test_path])
            print()

    # Run command and save trace
    exit_code = run_command_with_trace("tests", test_cmd, REPO_ROOT, TRACES_DIR)

    if exit_code is None:
        print(f"❌ Error: {test_cmd[0]} not installed")
        print("   Install it or update test_command in .repo/plan.yaml")

    return exit_code


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

    # Get lint command from plan
    lint_config = plan.get("plan", {}).get("lint_command", {})
    if isinstance(lint_config, str):
        lint_cmd = shlex.split(lint_config)
    elif isinstance(lint_config, dict):
        lint_cmd = shlex.split(lint_config.get("command", "ruff check ."))
    else:
        lint_cmd = ["ruff", "check", "."]

    # Run command and save trace
    exit_code = run_command_with_trace("lint", lint_cmd, REPO_ROOT, TRACES_DIR)

    if exit_code is None:
        print(f"❌ Error: {lint_cmd[0]} not installed")
        print("   Install it or update lint_command in .repo/plan.yaml")

    return exit_code




def show_diff_summary(phase_id: str, plan: dict):
    """Show summary of changed files vs phase scope."""
    # Get phase config
    phases = plan.get("plan", {}).get("phases", [])
    phase = next((p for p in phases if p["id"] == phase_id), None)

    if not phase:
        return  # Can't show summary without phase config

    # Load baseline SHA from CURRENT.json for consistent diffs
    baseline_sha = None
    if CURRENT_FILE.exists():
        try:
            current = json.loads(CURRENT_FILE.read_text())
            baseline_sha = current.get("baseline_sha")
        except (json.JSONDecodeError, KeyError):
            pass  # Tolerate missing or malformed CURRENT.json

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
        print("📊 No changes detected")
        return

    # Get scope patterns
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    if not include_patterns:
        print(f"📊 {len(changed_files)} files changed (no scope defined)")
        return

    # Classify files using shared utility
    in_scope, out_of_scope = classify_files(
        changed_files,
        include_patterns,
        exclude_patterns
    )

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
            print(f"   1. Revert: git restore {' '.join(out_of_scope[:3])}{'...' if len(out_of_scope) > 3 else ''}")
            print(f"   2. Update scope in .repo/briefs/{phase_id}.md")
            print("   3. Split into separate phase")
            print()

    # Check forbidden files using shared utility
    drift_rules = phase.get("drift_rules", {})
    forbid_patterns = drift_rules.get("forbid_changes", [])
    forbidden_files = check_forbidden_files(changed_files, forbid_patterns)

    if forbidden_files:
        print(f"🚫 Forbidden files changed ({len(forbidden_files)}):")
        for f in forbidden_files:
            print(f"  - {f}")
        print()
        print(f"   These require a separate phase. Revert: git restore {' '.join(forbidden_files)}")
        print()


def review_phase(phase_id: str):
    """Submit phase for review and block until judge provides feedback."""
    print(f"📋 Submitting phase {phase_id} for review...")
    print()

    # Load plan
    plan = load_plan()

    # Validate plan schema
    from lib.plan_validator import validate_plan
    validation_errors = validate_plan(plan)
    if validation_errors:
        print("❌ Plan validation failed:")
        for error in validation_errors:
            print(f"   - {error}")
        print("\nFix errors in .repo/plan.yaml and try again.")
        return 2

    # Get phase config for test scoping
    phases = plan.get("plan", {}).get("phases", [])
    phase = next((p for p in phases if p["id"] == phase_id), None)

    # Show diff summary
    show_diff_summary(phase_id, plan)

    # Run tests (with phase-specific scoping/quarantine)
    test_exit_code = run_tests(plan, phase)
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

    # Validate plan schema
    from lib.plan_validator import validate_plan
    validation_errors = validate_plan(plan)
    if validation_errors:
        print("❌ Plan validation failed:")
        for error in validation_errors:
            print(f"   - {error}")
        print("\nFix errors in .repo/plan.yaml and try again.")
        return 2

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

    # Compute binding hashes for phase
    import hashlib

    def sha256(filepath):
        return hashlib.sha256(filepath.read_bytes()).hexdigest()

    plan_path = REPO_DIR / "plan.yaml"
    manifest_path = REPO_DIR / "protocol_manifest.json"

    # Get baseline SHA for consistent diffs throughout phase
    baseline_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    baseline_sha = baseline_result.stdout.strip() if baseline_result.returncode == 0 else None

    current_data = {
        "phase_id": next_id,
        "brief_path": str(next_brief.relative_to(REPO_ROOT)),
        "status": "active",
        "started_at": time.time()
    }

    # Add baseline SHA for consistent diff anchor
    if baseline_sha:
        current_data["baseline_sha"] = baseline_sha

    # Add phase binding hashes if files exist
    if plan_path.exists():
        current_data["plan_sha"] = sha256(plan_path)
    if manifest_path.exists():
        current_data["manifest_sha"] = sha256(manifest_path)

    # Update CURRENT.json
    CURRENT_FILE.write_text(json.dumps(current_data, indent=2))

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
