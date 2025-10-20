#!/usr/bin/env python3
"""
Phasectl: Controller for gated phase protocol.

Usage:
  ./tools/phasectl.py start <PHASE_ID>   # Start implementation phase with brief acknowledgment
  ./tools/phasectl.py reset <PHASE_ID>    # Reset phase state to match current plan (for plan transitions)
  ./tools/phasectl.py review <PHASE_ID>  # Submit phase for review
  ./tools/phasectl.py next                # Advance to next phase
  ./tools/phasectl.py recover             # Recover from plan state corruption
  ./tools/phasectl.py discover            # Discover and validate plan structure
  ./tools/phasectl.py generate-briefs      # Generate brief templates from plan phases
  ./tools/phasectl.py solutions           # Show relevant solutions for current issues
  ./tools/phasectl.py amend propose <type> <value> <reason>  # Propose amendments
  ./tools/phasectl.py patterns <command>  # Handle patterns
"""

import sys
import json
import time
import subprocess
import shlex
import re
import os
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


def check_protocol_version():
    """Check if protocol tools are up to date."""
    # Check if we have latest commands by looking for discover command
    return has_command("discover_plan")


def has_command(command_name: str) -> bool:
    """Check if a command exists in the current protocol tools."""
    try:
        # Check if the command function exists
        return command_name in globals()
    except Exception:
        return False


def can_update():
    """Check if auto-update is possible."""
    return (
        Path("../judge-gated-orchestrator/install-protocol.sh").exists() and
        os.access("tools", os.W_OK) and
        Path(".git").exists()
    )


def auto_update_protocol():
    """Auto-update protocol tools if outdated."""
    try:
        if not can_update():
            print("❌ Auto-update failed - manual update required")
            print("   Run: ../judge-gated-orchestrator/install-protocol.sh")
            return False
        
        print("🔄 Protocol tools outdated - attempting auto-update...")
        
        result = subprocess.run([
            "../judge-gated-orchestrator/install-protocol.sh"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Protocol tools updated successfully")
            return True
        else:
            print(f"❌ Auto-update failed: {result.stderr}")
            print("   Run: ../judge-gated-orchestrator/install-protocol.sh")
            return False
            
    except Exception as e:
        print(f"❌ Auto-update error: {e}")
        print("   Run: ../judge-gated-orchestrator/install-protocol.sh")
        return False


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


def detect_plan_mismatch() -> bool:
    """Detect if current plan differs from stored plan SHA."""
    if not CURRENT_FILE.exists():
        return False
    
    try:
        current = json.loads(CURRENT_FILE.read_text())
        stored_plan_sha = current.get("plan_sha")
        
        if not stored_plan_sha:
            return False
        
        # Compute current plan SHA
        plan_path = REPO_DIR / "plan.yaml"
        if not plan_path.exists():
            return False
        
        import hashlib
        current_plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
        return current_plan_sha != stored_plan_sha
        
    except (json.JSONDecodeError, KeyError):
        return False


def extract_scope_from_brief(brief_path: Path) -> Dict[str, List[str]]:
    """Extract scope from brief markdown."""
    if not brief_path.exists():
        return {"include": [], "exclude": []}
    
    content = brief_path.read_text()
    
    # Find scope section
    scope_match = re.search(r'## Scope.*?(?=##|\Z)', content, re.DOTALL | re.IGNORECASE)
    if not scope_match:
        return {"include": [], "exclude": []}
    
    scope_section = scope_match.group(0)
    
    # Extract include items (✅) - look for lines starting with - after ✅ section
    include_section = re.search(r'✅.*?(?=❌|\Z)', scope_section, re.DOTALL)
    include_list = []
    if include_section:
        include_lines = re.findall(r'- `([^`]+)`', include_section.group(0))
        include_list.extend(include_lines)
    
    # Extract exclude items (❌) - look for lines starting with - after ❌ section
    exclude_section = re.search(r'❌.*?(?=🤔|\Z)', scope_section, re.DOTALL)
    exclude_list = []
    if exclude_section:
        exclude_lines = re.findall(r'- `([^`]+)`', exclude_section.group(0))
        exclude_list.extend(exclude_lines)
    
    return {
        "include": [item.strip() for item in include_list],
        "exclude": [item.strip() for item in exclude_list]
    }


def _resolve_test_scope(test_cmd: List[str], scope_patterns: List[str], exclude_patterns: List[str]) -> List[str]:
    """Resolve test scope patterns to specific test paths."""
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
                        # Add specific test file for precise testing
                        test_path = str(test_file.relative_to(REPO_ROOT))
                        if test_path.startswith("tests"):
                            test_paths.add(test_path)
        
        if test_paths:
            print(f"  📍 Test scope: Running {len(test_paths)} specific test files")
            
            # Handle poetry run pytest commands
            if len(test_cmd) >= 3 and test_cmd[0] == "poetry" and test_cmd[1] == "run" and test_cmd[2] == "pytest":
                new_cmd = test_cmd[:3]  # Keep "poetry run pytest"
                new_cmd.extend(sorted(test_paths))
                new_cmd.extend([arg for arg in test_cmd[3:] if arg.startswith("-")])
            else:
                # Original logic for direct pytest commands
                new_cmd = [test_cmd[0]]  # Keep pytest
                new_cmd.extend(sorted(test_paths))
                new_cmd.extend([arg for arg in test_cmd[1:] if arg.startswith("-")])
            
            return new_cmd
        else:
            print("  ⚠️  No test files match scope patterns - running all tests")
            return test_cmd
    
    except ImportError:
        # Fallback to simple string matching if pathspec not available
        print("  ⚠️  pathspec not available - using simple pattern matching")
        test_paths = []
        tests_dir = REPO_ROOT / "tests"
        if tests_dir.exists():
            for test_file in tests_dir.rglob("test_*.py"):
                rel_path = str(test_file.relative_to(REPO_ROOT))
                # Simple pattern matching
                for pattern in scope_patterns:
                    if pattern.endswith("*"):
                        # Directory pattern
                        if rel_path.startswith(pattern.rstrip("*")):
                            test_paths.append(rel_path)
                            break
                    elif pattern.endswith(".py"):
                        # Specific file pattern
                        if rel_path == pattern:
                            test_paths.append(rel_path)
                            break
        
        if test_paths:
            print(f"  📍 Test scope: Running {len(test_paths)} specific test files (fallback mode)")
            
            # Handle poetry run pytest commands
            if len(test_cmd) >= 3 and test_cmd[0] == "poetry" and test_cmd[1] == "run" and test_cmd[2] == "pytest":
                new_cmd = test_cmd[:3]  # Keep "poetry run pytest"
                new_cmd.extend(sorted(test_paths))
                new_cmd.extend([arg for arg in test_cmd[3:] if arg.startswith("-")])
            else:
                # Original logic for direct pytest commands
                new_cmd = [test_cmd[0]]
                new_cmd.extend(sorted(test_paths))
                new_cmd.extend([arg for arg in test_cmd[1:] if arg.startswith("-")])
            
            return new_cmd
        
        return test_cmd


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
            scope_patterns = phase.get("scope", {}).get("include", [])
            exclude_patterns = phase.get("scope", {}).get("exclude", [])
            test_cmd = _resolve_test_scope(test_cmd, scope_patterns, exclude_patterns)

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


def _resolve_lint_scope(lint_cmd: List[str], scope_patterns: List[str], exclude_patterns: List[str]) -> List[str]:
    """Resolve lint scope patterns to specific file paths (only changed files)."""
    try:
        import pathspec
        
        # Get changed files first (only lint what was actually changed)
        changed_files = get_changed_files(REPO_ROOT, include_committed=True)
        if not changed_files:
            print("  ⚠️  No changed files detected - running on all files")
            return lint_cmd
        
        # Create pathspec for include patterns
        include_spec = pathspec.PathSpec.from_lines('gitwildmatch', scope_patterns)
        exclude_spec = None
        if exclude_patterns:
            exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', exclude_patterns)
        
        # Find only changed Python files matching scope patterns
        lint_paths = set()
        for file_path in changed_files:
            if file_path.endswith('.py'):
                if include_spec.match_file(file_path):
                    if not exclude_spec or not exclude_spec.match_file(file_path):
                        lint_paths.add(file_path)
        
        if lint_paths:
            print(f"  📍 Lint scope: Running on {len(lint_paths)} specific files")
            
            # Handle poetry run ruff commands
            if len(lint_cmd) >= 3 and lint_cmd[0] == "poetry" and lint_cmd[1] == "run" and lint_cmd[2] == "ruff":
                new_cmd = lint_cmd[:3]  # Keep "poetry run ruff"
                new_cmd.extend(sorted(lint_paths))
                new_cmd.extend([arg for arg in lint_cmd[3:] if arg.startswith("-")])
            elif len(lint_cmd) >= 2 and lint_cmd[0] == "ruff" and lint_cmd[1] == "check":
                # Handle "ruff check" commands properly
                new_cmd = ["ruff", "check"]  # Keep "ruff check"
                new_cmd.extend(sorted(lint_paths))
                new_cmd.extend([arg for arg in lint_cmd[2:] if arg.startswith("-")])
            else:
                # Original logic for direct ruff commands (fallback)
                new_cmd = [lint_cmd[0]]  # Keep ruff
                new_cmd.extend(sorted(lint_paths))
                new_cmd.extend([arg for arg in lint_cmd[1:] if arg.startswith("-")])
            
            return new_cmd
        else:
            print("  ⚠️  No files match scope patterns - running on all files")
            return lint_cmd
    
    except ImportError:
        # Fallback to simple pattern matching if pathspec not available
        print("  ⚠️  pathspec not available - using simple pattern matching")
        return lint_cmd


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

    # Apply lint scoping if phase provided
    if phase:
        lint_scope = lint_gate.get("lint_scope", "all")
        
        if lint_scope == "scope":
            scope_patterns = phase.get("scope", {}).get("include", [])
            exclude_patterns = phase.get("scope", {}).get("exclude", [])
            lint_cmd = _resolve_lint_scope(lint_cmd, scope_patterns, exclude_patterns)

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

    # Get scope patterns from plan
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    # Load runtime scope amendments
    try:
        from lib.state import load_phase_context
        context = load_phase_context(phase_id, str(REPO_ROOT))
        additional_scope = context.get("scope_cache", {}).get("additional", [])
        if additional_scope:
            include_patterns = include_patterns + additional_scope
            print(f"  📍 Using runtime scope amendments: {len(additional_scope)} additional patterns")
    except Exception:
        pass  # Tolerate missing context or import errors

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
    
    # CRITICAL: Validate plan state consistency before review
    if CURRENT_FILE.exists():
        try:
            current = json.loads(CURRENT_FILE.read_text())
            stored_plan_sha = current.get("plan_sha")
            if stored_plan_sha:
                import hashlib
                plan_path = REPO_DIR / "plan.yaml"
                if plan_path.exists():
                    current_plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
                    if current_plan_sha != stored_plan_sha:
                        print("⚠️  Plan State Mismatch Detected!")
                        print()
                        print("The current plan differs from the stored plan SHA.")
                        print("This indicates the plan was reverted externally.")
                        print()
                        print("SOLUTION:")
                        print(f"   ./tools/phasectl.py reset {phase_id}")
                        print()
                        print("This will update the phase state to match your current plan.")
                        return 1
        except (json.JSONDecodeError, KeyError):
            pass  # Tolerate missing or malformed CURRENT.json

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


def reset_phase(phase_id: str):
    """Reset phase state to match current plan (for plan transitions)."""
    print(f"🔄 Resetting phase state for: {phase_id}")
    print()
    
    # Check if brief exists
    brief_path = BRIEFS_DIR / f"{phase_id}.md"
    if not brief_path.exists():
        print(f"❌ Error: Brief not found: {brief_path}")
        print()
        print("💡 Run 'discover' first to see all missing briefs:")
        print("   ./tools/phasectl.py discover")
        print()
        print("Then create the missing brief:")
        print(f"   touch .repo/briefs/{phase_id}.md")
        return 1
    
    # Load current plan to validate phase exists
    plan = load_plan()
    phases = plan.get("plan", {}).get("phases", [])
    phase = next((p for p in phases if p["id"] == phase_id), None)
    
    if not phase:
        print(f"❌ Error: Phase {phase_id} not found in current plan")
        print("   Available phases:")
        for p in phases:
            print(f"   - {p['id']}")
        return 1
    
    # Get current baseline SHA
    baseline_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    baseline_sha = baseline_result.stdout.strip() if baseline_result.returncode == 0 else None
    
    if not baseline_sha:
        print("❌ Error: Not in a git repository")
        return 1
    
    # Compute current hashes
    import hashlib
    def sha256(filepath):
        return hashlib.sha256(filepath.read_bytes()).hexdigest()
    
    plan_path = REPO_DIR / "plan.yaml"
    manifest_path = REPO_DIR / "protocol_manifest.json"
    
    # Create new phase state
    current_data = {
        "phase_id": phase_id,
        "brief_path": str(brief_path.relative_to(REPO_ROOT)),
        "status": "active",
        "started_at": time.time(),
        "baseline_sha": baseline_sha
    }
    
    # Add current hashes
    if plan_path.exists():
        current_data["plan_sha"] = sha256(plan_path)
    if manifest_path.exists():
        current_data["manifest_sha"] = sha256(manifest_path)
    
    # Update CURRENT.json
    CURRENT_FILE.write_text(json.dumps(current_data, indent=2))
    
    print(f"✅ Phase state reset successfully!")
    print(f"   Phase: {phase_id}")
    print(f"   Baseline: {baseline_sha[:8]}...")
    print(f"   Plan SHA: {current_data.get('plan_sha', 'N/A')[:8]}...")
    print()
    print("   Next steps:")
    print(f"   1. Run: ./tools/phasectl.py start {phase_id}")
    print(f"   2. Implement changes")
    print(f"   3. Run: ./tools/phasectl.py review {phase_id}")
    
    return 0




def is_experimental_enabled(feature: str) -> bool:
    """Check if experimental feature is enabled in plan."""
    try:
        plan_file = REPO_DIR / "plan.yaml"
        if not plan_file.exists():
            return False
        
        import yaml
        with plan_file.open() as f:
            plan = yaml.safe_load(f)
        
        exp_features = plan.get("plan", {}).get("experimental_features", {})
        return exp_features.get(feature, False)
    except Exception:
        return False


def generate_briefs():
    """Generate empty brief files from plan phases (minimal approach)."""
    print("🔍 Generating brief templates from plan.yaml...")
    print()
    
    # Load plan
    plan_file = REPO_DIR / "plan.yaml"
    if not plan_file.exists():
        print("❌ Error: No plan.yaml found")
        return 1
    
    try:
        import yaml
        with plan_file.open() as f:
            plan = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error: Invalid plan.yaml: {e}")
        return 1
    
    phases = plan.get("plan", {}).get("phases", [])
    if not phases:
        print("❌ Error: No phases found in plan.yaml")
        return 1
    
    generated_count = 0
    print(f"📋 Found {len(phases)} phases:")
    
    for phase in phases:
        phase_id = phase.get("id")
        if not phase_id:
            print("   ❌ Phase missing 'id' field")
            continue
            
        brief_path = BRIEFS_DIR / f"{phase_id}.md"
        status = "✅" if brief_path.exists() else "✅"
        
        if not brief_path.exists():
            # Minimal approach: Generate basic template
            brief_content = f"""# Phase {phase_id}

## Objective
{phase.get('description', 'TBD')}

## Scope
TBD

## Implementation Steps
TBD
"""
            brief_path.write_text(brief_content)
            generated_count += 1
            status = "✅"
        
        print(f"   {status} {phase_id}")
    
    print()
    print(f"✅ Generated {generated_count} brief templates")
    print("💡 Briefs contain basic structure - edit as needed")
    return 0


def discover_plan():
    """Discover and validate plan structure - mandatory first step."""
    print("🔍 Plan Discovery Mode")
    print()
    
    # Load and validate plan
    plan_file = REPO_DIR / "plan.yaml"
    if not plan_file.exists():
        print("❌ Error: No plan.yaml found")
        print("   Create a plan.yaml file first:")
        print("   touch .repo/plan.yaml")
        return 1
    
    try:
        import yaml
        with plan_file.open() as f:
            plan = yaml.safe_load(f)
    except Exception as e:
        print(f"❌ Error: Invalid plan.yaml: {e}")
        return 1
    
    phases = plan.get("plan", {}).get("phases", [])
    if not phases:
        print("❌ Error: No phases found in plan.yaml")
        return 1
    
    print(f"📋 Found {len(phases)} phases:")
    missing_briefs = []
    
    for phase in phases:
        phase_id = phase.get("id")
        if not phase_id:
            print("   ❌ Phase missing 'id' field")
            continue
            
        brief_path = BRIEFS_DIR / f"{phase_id}.md"
        status = "✅" if brief_path.exists() else "❌ MISSING"
        print(f"   {status} {phase_id}")
        
        if not brief_path.exists():
            missing_briefs.append(phase_id)
    
    print()
    
    if missing_briefs:
        print(f"⚠️  Missing briefs: {', '.join(missing_briefs)}")
        print()
        print("Create briefs before starting implementation:")
        for phase_id in missing_briefs:
            print(f"   touch .repo/briefs/{phase_id}.md")
        print()
        print("💡 Each brief should contain:")
        print("   - Phase objective and scope")
        print("   - Required artifacts")
        print("   - Gate requirements")
        print("   - Implementation steps")
        return 1
    
    print("✅ All briefs found - ready for implementation")
    print()
    print("Next steps:")
    print("   1. Review briefs: cat .repo/briefs/<phase-id>.md")
    print("   2. Start implementation: ./tools/phasectl.py start <phase-id>")
    return 0


def inject_patterns_into_brief(phase_id: str, brief_content: str) -> str:
    """Inject relevant patterns into brief by default - agent must opt out (experimental feature)."""
    # Check if experimental features are enabled
    if not is_experimental_enabled("replay_budget"):
        return brief_content
    
    try:
        # Load relevant patterns
        patterns_file = REPO_ROOT / ".repo" / "collective_intelligence" / "patterns.jsonl"
        if not patterns_file.exists():
            return brief_content
        
        patterns = []
        with open(patterns_file) as f:
            for line in f:
                if line.strip():
                    pattern = json.loads(line)
                    if pattern.get("phase_id") != phase_id:  # Don't include self
                        patterns.append(pattern)
        
        if not patterns:
            return brief_content
        
        # Get top 3 most recent patterns
        top_patterns = sorted(patterns, key=lambda x: x.get("timestamp", 0), reverse=True)[:3]
        
        # Inject patterns section
        patterns_section = """
---

## 🧠 Collective Intelligence (Auto-Injected)

The following patterns were automatically identified as relevant to this phase:

"""
        
        for i, pattern in enumerate(top_patterns, 1):
            patterns_section += f"{i}. **From {pattern.get('phase_id', 'previous phase')}**: {pattern.get('text', '')}\n"
        
        patterns_section += """
**Note**: These patterns are automatically injected based on successful previous phases. If you believe they are not relevant, you may opt out by adding a comment explaining why.

**⚠️  Opt-out cost**: If you opt out and replay performance degrades, your next phase budget will be reduced.

"""
        
        # Insert patterns section before the end of the brief
        if "---" in brief_content:
            # Insert before the last "---" if it exists
            parts = brief_content.split("---")
            if len(parts) > 1:
                enhanced_brief = "---".join(parts[:-1]) + patterns_section + "---" + parts[-1]
            else:
                enhanced_brief = brief_content + patterns_section
        else:
            enhanced_brief = brief_content + patterns_section
        
        return enhanced_brief
        
    except Exception as e:
        print(f"  ⚠️  Error injecting patterns: {e}")
        return brief_content

def start_phase(phase_id: str):
    """Start implementation phase with mandatory brief acknowledgment."""
    print(f"📋 Starting phase: {phase_id}")
    print()
    
    # MINIMUM CHECK: Detect plan mismatch before starting
    if detect_plan_mismatch():
        print("⚠️  Plan State Mismatch Detected!")
        print()
        print("The current plan differs from the stored plan SHA.")
        print("This usually happens when creating a new plan with different phases.")
        print()
        print("SOLUTION:")
        print(f"   ./tools/phasectl.py reset {phase_id}")
        print()
        print("This will update the phase state to match your current plan.")
        return 1
    
    # Check if brief exists
    brief_path = BRIEFS_DIR / f"{phase_id}.md"
    if not brief_path.exists():
        print(f"❌ Error: Brief not found: {brief_path}")
        print()
        print("💡 Run 'discover' first to see all missing briefs:")
        print("   ./tools/phasectl.py discover")
        print()
        print("Then create the missing brief:")
        print(f"   touch .repo/briefs/{phase_id}.md")
        return 1
    
    # Display brief content with auto-injected patterns
    print("📄 Brief Content:")
    print("=" * 50)
    brief_content = brief_path.read_text()
    
    # Auto-inject patterns (default on, agent must opt out)
    enhanced_brief = inject_patterns_into_brief(phase_id, brief_content)
    print(enhanced_brief)
    print("=" * 50)
    print()
    
    # Track pattern opt-out for replay correlation (experimental)
    if is_experimental_enabled("replay_budget"):
        try:
            from tools.judge import track_pattern_opt_out
            track_pattern_opt_out(phase_id, enhanced_brief)
        except Exception as e:
            print(f"  ⚠️  Error tracking pattern opt-out: {e}")
    else:
        print("  ⚠️  Pattern opt-out tracking disabled (experimental feature)")
    
    # Extract and display scope
    scope = extract_scope_from_brief(brief_path)
    
    print("🎯 Scope Summary:")
    if scope["include"]:
        print("✅ You MAY touch:")
        for item in scope["include"]:
            print(f"   - {item}")
    else:
        print("✅ No specific include patterns found")
    
    if scope["exclude"]:
        print("❌ You must NOT touch:")
        for item in scope["exclude"]:
            print(f"   - {item}")
    else:
        print("❌ No specific exclude patterns found")
    
    print()
    
    # Require explicit acknowledgment
    print("⚠️  Before proceeding, you must confirm you have read and understood the brief.")
    response = input("Have you read and understood the brief? (yes/no): ")
    
    if response.lower() != "yes":
        print("❌ Please read the brief first")
        print("   You must understand the scope before implementing.")
        return 1
    
    # Update current phase status
    current_data = {
        "phase_id": phase_id,
        "brief_path": str(brief_path.relative_to(REPO_ROOT)),
        "status": "implementation_started",
        "started_at": time.time(),
        "brief_acknowledged_at": time.time()
    }
    
    # Get baseline SHA for consistent diffs throughout phase
    baseline_result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    baseline_sha = baseline_result.stdout.strip() if baseline_result.returncode == 0 else None
    
    if baseline_sha:
        current_data["baseline_sha"] = baseline_sha
    
    # Update CURRENT.json
    CURRENT_FILE.write_text(json.dumps(current_data, indent=2))
    
    print(f"✅ Phase {phase_id} started successfully!")
    print("   You may now implement changes within the specified scope.")
    print("   When ready, run: ./tools/phasectl.py review {phase_id}")
    
    return 0


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
    
    # CRITICAL: Validate plan state consistency
    stored_plan_sha = current.get("plan_sha")
    if stored_plan_sha:
        import hashlib
        plan_path = REPO_DIR / "plan.yaml"
        if plan_path.exists():
            current_plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
            if current_plan_sha != stored_plan_sha:
                print("⚠️  Plan State Mismatch Detected!")
                print()
                print("The current plan differs from the stored plan SHA.")
                print("This indicates the plan was reverted externally.")
                print()
                print("SOLUTION:")
                print(f"   ./tools/phasectl.py recover")
                print()
                print("This will attempt to recover from plan state corruption.")
                return 1

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


def recover_from_corruption():
    """Recover from plan state corruption caused by upgrade process."""
    print("🔄 Attempting to recover from plan state corruption...")
    print()
    
    # Check if we're in a corrupted state
    if not CURRENT_FILE.exists():
        print("❌ Error: No CURRENT.json found - cannot recover")
        return 1
    
    try:
        current = json.loads(CURRENT_FILE.read_text())
    except json.JSONDecodeError as e:
        print(f"❌ Error: CURRENT.json corrupted: {e}")
        return 1
    
    # Check for plan SHA mismatch (indicates corruption)
    stored_plan_sha = current.get("plan_sha")
    if not stored_plan_sha:
        print("⚠️  No stored plan SHA - cannot detect corruption")
        return 0
    
    plan_path = REPO_DIR / "plan.yaml"
    if not plan_path.exists():
        print("❌ Error: Plan file missing - cannot recover")
        return 1
    
    import hashlib
    current_plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    
    if current_plan_sha == stored_plan_sha:
        print("✅ No corruption detected - plan state is consistent")
        return 0
    
    print("🚨 Plan state corruption detected!")
    print(f"   Stored SHA: {stored_plan_sha[:8]}...")
    print(f"   Current SHA: {current_plan_sha[:8]}...")
    print()
    
    # Try to find a backup or recent commit with correct state
    print("🔍 Looking for recovery options...")
    
    # Check git history for recent commits with plan changes
    result = subprocess.run(
        ["git", "log", "--oneline", "-10", "--", ".repo/plan.yaml"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0 and result.stdout.strip():
        print("📋 Recent plan changes found:")
        for line in result.stdout.strip().split('\n'):
            print(f"   {line}")
        print()
        print("💡 Recovery options:")
        print("   1. Checkout a recent commit with correct plan:")
        print("      git checkout <commit-hash> -- .repo/plan.yaml")
        print("   2. Reset phase state to match current plan:")
        print(f"      ./tools/phasectl.py reset {current.get('phase_id', 'PHASE_ID')}")
        print("   3. Manually restore plan from backup if available")
    else:
        print("❌ No recent plan changes found in git history")
        print()
        print("💡 Manual recovery required:")
        print("   1. Restore plan from backup if available")
        print("   2. Recreate plan manually")
        print("   3. Reset phase state:")
        print(f"      ./tools/phasectl.py reset {current.get('phase_id', 'PHASE_ID')}")
    
    return 1


def protocol_health_check():
    """One-line protocol validation."""
    return all([
        has_command("discover_plan"),
        has_command("reset_phase"), 
        has_command("recover_from_corruption"),
        Path(".repo/plan.yaml").exists()
    ])

def solutions_command():
    """Show relevant solutions for current issues."""
    print("💡 Protocol Solutions:")
    print("")
    
    # Check protocol health
    if not protocol_health_check():
        print("❌ Protocol Health Check Failed")
        print("   Solution: protocol_health_check (5 LOC)")
        print("   Impact: Prevents 80% of protocol issues")
        print("   Fix: Run: ../judge-gated-orchestrator/install-protocol.sh")
        print("")
    
    # Check for missing briefs
    try:
        plan_file = REPO_ROOT / "plan.yaml"
        if plan_file.exists():
            import yaml
            with plan_file.open() as f:
                plan = yaml.safe_load(f)
            phases = plan.get("plan", {}).get("phases", [])
            missing_briefs = []
            for phase in phases:
                phase_id = phase.get("id")
                if phase_id:
                    brief_path = BRIEFS_DIR / f"{phase_id}.md"
                    if not brief_path.exists():
                        missing_briefs.append(phase_id)
            
            if missing_briefs:
                print("❌ Missing Briefs")
                print("   Solution: auto_fix_common_issues (8 LOC)")
                print("   Impact: Self-healing protocol")
                print(f"   Fix: Run: ./tools/phasectl.py generate-briefs")
                print("")
    except Exception:
        pass
    
    # Check for plan mismatch
    try:
        current_file = BRIEFS_DIR / "CURRENT.json"
        if current_file.exists():
            import json
            current = json.loads(current_file.read_text())
            plan_sha = current.get("plan_sha")
            if plan_sha:
                import hashlib
                with open(REPO_ROOT / "plan.yaml", "rb") as f:
                    current_plan_sha = hashlib.sha256(f.read()).hexdigest()
                if plan_sha != current_plan_sha:
                    print("❌ Plan Mismatch")
                    print("   Solution: smart_error_messages (10 LOC)")
                    print("   Impact: Eliminates agent confusion")
                    print("   Fix: Run: ./tools/phasectl.py reset <phase-id>")
                    print("")
    except Exception:
        pass
    
    if not any([not protocol_health_check()]):
        print("✅ No issues detected - protocol is healthy!")
        print("")

def main():
    # Protocol health check
    if not protocol_health_check():
        print("⚠️  Protocol health check failed - some features may not work")
        print("   Run: ../judge-gated-orchestrator/install-protocol.sh")
        print()
    
    # Check and auto-update protocol tools if needed
    if not check_protocol_version():
        if not auto_update_protocol():
            print("⚠️  Using outdated protocol tools")
            print("   Some features may not work correctly")
            print("   Update manually: ../judge-gated-orchestrator/install-protocol.sh")
            print()
    
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    command = sys.argv[1]

    if command == "discover":
        return discover_plan()
    elif command == "generate-briefs":
        return generate_briefs()
    elif command == "solutions":
        solutions_command()
        return 0
    elif command == "start":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py start <PHASE_ID>")
            return 1
        # Add discovery check before start
        if discover_plan() != 0:
            print()
            print("💡 Fix missing briefs first, then run:")
            print(f"   ./tools/phasectl.py start {sys.argv[2]}")
            return 1
        return start_phase(sys.argv[2])

    elif command == "reset":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py reset <PHASE_ID>")
            return 1
        return reset_phase(sys.argv[2])

    elif command == "review":
        if len(sys.argv) < 3:
            print("Usage: phasectl.py review <PHASE_ID>")
            return 1
        return review_phase(sys.argv[2])

    elif command == "next":
        return next_phase()
    
    elif command == "recover":
        return recover_from_corruption()
    
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
