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
from typing import List, Dict, Any

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

    # Get test command from runtime context if available, otherwise from plan
    if phase and phase.get("runtime", {}).get("test_cmd"):
        test_cmd = shlex.split(phase["runtime"]["test_cmd"])
    else:
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

    # Apply pending amendments before review
    from lib.amendments import apply_amendments
    applied_amendments = apply_amendments(phase_id)
    
    if applied_amendments:
        print(f"✅ Applied {len(applied_amendments)} amendments")
        for amendment in applied_amendments:
            print(f"   {amendment['type']}: {amendment['value']}")
        print()

    # Auto-propose amendments from patterns
    from lib.traces import propose_amendments_from_patterns
    from lib.amendments import propose_amendment
    
    # Get context for pattern matching
    traces_dir = REPO_ROOT / ".repo" / "traces"
    test_trace_file = traces_dir / "last_tests.txt"
    lint_trace_file = traces_dir / "last_lint.txt"
    
    context = {
        "test_output": test_trace_file.read_text() if test_trace_file.exists() else "",
        "lint_output": lint_trace_file.read_text() if lint_trace_file.exists() else "",
        "changed_files": []  # Will be populated later
    }
    
    # Propose amendments from patterns
    pattern_proposals = propose_amendments_from_patterns(context)
    for proposal in pattern_proposals:
        success = propose_amendment(phase_id, proposal["type"], proposal["value"], proposal["reason"])
        if success:
            print(f"🧠 Pattern-based amendment proposed: {proposal['type']} = {proposal['value']}")
    
    if pattern_proposals:
        print()

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
        
        # Learn from successful review
        _learn_from_review(phase_id, applied_amendments)
        
        # Write micro-retrospective
        _write_micro_retro(phase_id, applied_amendments)
        
        return 0
    elif critique_file.exists():
        print(f"❌ Phase {phase_id} needs revision:")
        print()
        print(critique_file.read_text())
        return 1
    else:
        print("⚠️  Judge did not produce feedback. Check for errors above.")
        return 2

def _learn_from_review(phase_id: str, applied_amendments: List[Dict[str, Any]]) -> None:
    """Learn patterns from successful review"""
    from lib.traces import store_pattern
    
    if not applied_amendments:
        return
    
    # Get test output for learning
    traces_dir = REPO_ROOT / ".repo" / "traces"
    test_trace_file = traces_dir / "last_tests.txt"
    
    test_output = ""
    if test_trace_file.exists():
        test_output = test_trace_file.read_text()
    
    # Learn from amendments that fixed issues
    for amendment in applied_amendments:
        if amendment["type"] == "set_test_cmd" and "error" in test_output.lower():
            pattern = {
                "kind": "fix",
                "when": {
                    "pytest_error": "usage: python -m pytest"
                },
                "action": {
                    "amend": "set_test_cmd",
                    "value": amendment["value"]
                },
                "description": "Fix pytest usage error",
                "confidence": 0.9,
                "evidence": [test_output]
            }
            store_pattern(pattern)

def _write_micro_retro(phase_id: str, applied_amendments: List[Dict[str, Any]]) -> None:
    """Write micro-retrospective for successful phase"""
    from lib.traces import write_micro_retro
    
    # Get execution data
    traces_dir = REPO_ROOT / ".repo" / "traces"
    test_trace_file = traces_dir / "last_tests.txt"
    
    test_output = ""
    if test_trace_file.exists():
        test_output = test_trace_file.read_text()
    
    # Determine what helped
    what_helped = []
    if applied_amendments:
        for amendment in applied_amendments:
            what_helped.append(f"Amendment {amendment['type']}: {amendment['value']}")
    
    # Determine root cause
    root_cause = "unknown"
    if "usage:" in test_output.lower():
        root_cause = "test command issue"
    elif "error" in test_output.lower():
        root_cause = "test execution error"
    
    execution_data = {
        "retries": 0,  # Could be tracked in future
        "amendments": applied_amendments,
        "llm_score": 1.0,  # Successful phase
        "root_cause": root_cause,
        "what_helped": what_helped,
        "success": True,
        "execution_time": "unknown"
    }
    
    write_micro_retro(phase_id, execution_data)


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
    
    # Show enhanced brief with hints and guardrails
    enhanced_brief = enhance_brief(next_id, next_brief.read_text())
    if enhanced_brief != next_brief.read_text():
        print("\n🧠 Enhanced Brief:")
        print("=" * 50)
        print(enhanced_brief)
        print("=" * 50)
    
    return 0

def enhance_brief(phase_id: str, base_brief: str) -> str:
    """Enhance brief with hints and guardrails"""
    from lib.traces import get_phase_hints
    from lib.state import load_phase_context
    
    # Get hints from recent executions
    hints = get_phase_hints(phase_id, lookback_count=3)
    
    # Get current state for guardrails
    context = load_phase_context(phase_id)
    guardrails = generate_guardrails(phase_id, context)
    
    # Enhance the brief
    enhanced_brief = base_brief
    
    if hints:
        hints_section = "\n## 🧠 Collective Intelligence Hints\n\n"
        for hint in hints:
            hints_section += f"- {hint}\n"
        enhanced_brief += hints_section
    
    if guardrails:
        guardrails_section = "\n## 🛡️ Execution Guardrails\n\n"
        for guardrail in guardrails:
            guardrails_section += f"- {guardrail}\n"
        enhanced_brief += guardrails_section
    
    return enhanced_brief

def generate_guardrails(phase_id: str, context: Dict[str, Any]) -> List[str]:
    """Generate guardrails based on current state"""
    guardrails = []
    
    mode = context.get("mode", "EXPLORE")
    amendments_used = context.get("amendments_used", {})
    amendments_budget = context.get("amendments_budget", {})
    
    if mode == "EXPLORE":
        guardrails.append("EXPLORE mode: You may propose amendments within budget")
        
        for amendment_type, budget in amendments_budget.items():
            used = amendments_used.get(amendment_type, 0)
            remaining = budget - used
            if remaining <= 1:
                guardrails.append(f"⚠️ {amendment_type} budget nearly exhausted ({remaining} remaining)")
    
    elif mode == "LOCK":
        guardrails.append("LOCK mode: Amendments closed (except baseline shifts)")
    
    guardrails.append("Never modify .repo/plan.yaml directly")
    guardrails.append("Always check scope before making changes")
    
    return guardrails


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
    
    elif command == "amend":
        if len(sys.argv) < 4:
            print("Usage: phasectl.py amend propose <type> <value> <reason>")
            return 1
        return handle_amendment_command(sys.argv[2:])
    
    elif command == "patterns":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py patterns <command>")
            return 1
        return handle_patterns_command(sys.argv[2:])

    else:
        print(f"Unknown command: {command}")
        print(__doc__)
        return 1

def load_current_phase():
    """Load current phase from CURRENT.json"""
    if not CURRENT_FILE.exists():
        return None
    
    try:
        return json.loads(CURRENT_FILE.read_text())
    except (json.JSONDecodeError, KeyError):
        return None

def handle_amendment_command(args):
    """Handle amendment commands"""
    from lib.amendments import propose_amendment
    
    if args[0] == "propose":
        if len(args) < 4:
            print("Usage: amend propose <type> <value> <reason>")
            return 1
        
        amendment_type = args[1]
        value = args[2]
        reason = args[3]
        
        # Get current phase
        current = load_current_phase()
        if not current:
            print("❌ No current phase")
            return 1
        
        success = propose_amendment(current["phase_id"], amendment_type, value, reason)
        
        if success:
            print(f"✅ Amendment proposed: {amendment_type} = {value}")
        else:
            print(f"❌ Amendment budget exceeded for {amendment_type}")
            return 1
    
    return 0

def handle_patterns_command(args):
    """Handle patterns commands"""
    from lib.traces import find_matching_patterns
    
    if args[0] == "list":
        patterns_file = REPO_ROOT / ".repo" / "collective_intelligence" / "patterns.jsonl"
        
        if not patterns_file.exists():
            print("No patterns stored yet.")
            return 0
        
        print("Stored patterns:")
        with open(patterns_file, 'r') as f:
            for i, line in enumerate(f, 1):
                pattern = json.loads(line.strip())
                print(f"{i}. {pattern.get('description', 'Unknown')} (confidence: {pattern.get('confidence', 0)})")
                print(f"   When: {pattern.get('when', {})}")
                print(f"   Action: {pattern.get('action', {})}")
                print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
