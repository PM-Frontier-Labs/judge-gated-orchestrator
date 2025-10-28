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
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    import yaml
except ImportError:
    print("❌ Error: pyyaml not installed. Run: pip install pyyaml")
    sys.exit(1)

# Add tools directory to path for imports
tools_dir = Path(__file__).parent
sys.path.insert(0, str(tools_dir))

from lib.error_utils import log_error, log_warning, log_info, ProtocolError, ExecutionError
from lib.path_utils import get_relative_path

# Import shared utilities
from lib.git_ops import get_changed_files
from lib.scope import classify_files, check_forbidden_files
from lib.traces import check_gate_trace
from lib.protocol_guard import verify_protocol_lock, verify_phase_binding
from lib.state import load_phase_context
from lib.gate_interface import run_gates

# Import LLM judge (optional)
try:
    import sys
    from pathlib import Path
    tools_dir = Path(__file__).parent
    sys.path.insert(0, str(tools_dir))
    from llm_judge import llm_code_review
    LLM_JUDGE_AVAILABLE = True
except ImportError:
    LLM_JUDGE_AVAILABLE = False

REPO_ROOT = Path(__file__).parent.parent
REPO_DIR = REPO_ROOT / ".repo"
CRITIQUES_DIR = REPO_DIR / "critiques"
TRACES_DIR = REPO_DIR / "traces"


def is_experimental_enabled(feature: str) -> bool:
    """Check if experimental feature is enabled in plan."""
    try:
        plan = load_plan()
        exp_features = plan.get("plan", {}).get("experimental_features", {})
        return exp_features.get(feature, False)
    except Exception:
        return False


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
    """Get phase configuration from plan + runtime context"""
    phases = plan.get("plan", {}).get("phases", [])
    for phase in phases:
        if phase.get("id") == phase_id:
            # Get runtime state from context
            context = load_phase_context(phase_id)
            
            # Merge runtime state into phase config (amendment system removed)
            phase["runtime"] = {
                "baseline_sha": context.get("baseline_sha"),
                "test_cmd": context.get("test_cmd"),
                "mode": context.get("mode")
            }
            
            return phase
    raise ValueError(f"Phase {phase_id} not found in plan")


def check_artifacts(phase: Dict[str, Any]) -> List[str]:
    """Check that required artifacts exist and are non-empty."""
    issues = []
    artifacts = phase.get("artifacts", {}).get("must_exist", [])

    for artifact in artifacts:
        path = REPO_ROOT / artifact
        if not path.exists():
            issues.append(f"Missing required artifact: {artifact}")
        elif path.stat().st_size == 0:
            issues.append(f"Artifact is empty: {artifact}")

    return issues




def check_docs(phase: Dict[str, Any], changed_files: List[str]) -> List[str]:
    """Check that documentation was actually updated in this phase."""
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

    # Defensive check for empty changed_files
    if not changed_files:
        issues.append(
            "Documentation gate failed: No changed files detected\n"
            "   This usually means:\n"
            "   - Files are not committed yet (run 'git add' and 'git commit')\n"
            "   - Baseline SHA is incorrect\n"
            "   - No files were actually modified\n"
            f"   Required documentation: {', '.join(must_update)}"
        )
        return issues

    # Check each required doc
    for doc in must_update:
        # Handle section anchors like "docs/mvp.md#feature"
        doc_path = doc.split("#")[0]
        anchor = doc.split("#")[1] if "#" in doc else None
        path = REPO_ROOT / doc_path

        # Check existence
        if not path.exists():
            issues.append(f"Documentation not found: {doc_path}")
            continue

        # Check non-empty
        if path.stat().st_size == 0:
            issues.append(f"Documentation is empty: {doc_path}")
            continue

        # CRITICAL: Check if doc was actually changed in this phase
        # Handle both files and directories (prefix matching for directories)
        doc_was_changed = (
            doc_path in changed_files or  # Exact file match
            any(f.startswith(doc_path) for f in changed_files)  # Directory prefix match
        )
        if not doc_was_changed:
            # Show what files WERE detected for debugging
            detected_files = changed_files[:5]  # Show first 5 files
            more_files = f" and {len(changed_files) - 5} more" if len(changed_files) > 5 else ""
            
            issues.append(
                f"Documentation not updated in this phase: {doc_path}\n"
                f"   This file must be modified as part of {phase['id']}\n"
                f"   Files detected as changed: {', '.join(detected_files)}{more_files}\n"
                f"   To fix: Modify {doc_path} and ensure changes are committed"
            )
            continue

        # If anchor specified, verify heading exists
        if anchor:
            content = path.read_text()
            # Look for markdown heading: # anchor or ## anchor, etc.
            import re
            pattern = rf'^#+\s+{re.escape(anchor)}'
            if not re.search(pattern, content, re.MULTILINE | re.IGNORECASE):
                issues.append(
                    f"Documentation section not found: {doc}#{anchor}\n"
                    f"   Expected heading '{anchor}' in {doc_path}"
                )

    return issues




def _generate_forbidden_remediation(forbidden_files: List[str], baseline_sha: str, repo_root: Path) -> List[str]:
    """Generate remediation hints for forbidden file changes."""
    import subprocess
    
    # Get uncommitted changes
    uncommitted_result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    uncommitted_set = set(uncommitted_result.stdout.strip().split("\n")) if uncommitted_result.returncode == 0 else set()
    
    uncommitted_forbidden = [f for f in forbidden_files if f in uncommitted_set]
    committed_forbidden = [f for f in forbidden_files if f not in uncommitted_set]
    
    remediation = []
    if uncommitted_forbidden:
        remediation.append(f"Fix uncommitted: git restore --worktree --staged -- {' '.join(uncommitted_forbidden)}")
    if committed_forbidden:
        if baseline_sha:
            remediation.append(f"Fix committed: git restore --source={baseline_sha} -- {' '.join(committed_forbidden)}")
        else:
            remediation.append(f"Fix committed: git revert <commits> (or restore: git restore --source=<baseline> -- {' '.join(committed_forbidden[:2])})")
    
    return remediation


def _generate_drift_remediation(out_of_scope: List[str], baseline_sha: str, phase_id: str, repo_root: Path) -> List[str]:
    """Generate remediation hints for out-of-scope changes."""
    import subprocess
    
    # Get uncommitted changes
    uncommitted_result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    uncommitted_set = set(uncommitted_result.stdout.strip().split("\n")) if uncommitted_result.returncode == 0 else set()
    
    # Classify files
    uncommitted_out = [f for f in out_of_scope if f in uncommitted_set]
    committed_out = [f for f in out_of_scope if f not in uncommitted_set]
    
    remediation = ["Options to fix:"]
    
    if uncommitted_out:
        remediation.append(f"1. Revert uncommitted changes: git restore --worktree --staged -- {' '.join(uncommitted_out[:3])}")
        if len(uncommitted_out) > 3:
            remediation.append(f"   (and {len(uncommitted_out) - 3} more)")
    
    if committed_out:
        if baseline_sha:
            remediation.append(f"2. Restore committed files to baseline: git restore --source={baseline_sha} -- {' '.join(committed_out[:3])}")
        else:
            remediation.append("2. Revert committed changes: git revert <commit-range> (or restore specific files)")
        if len(committed_out) > 3:
            remediation.append(f"   (and {len(committed_out) - 3} more)")
    
    remediation.append(f"3. Update phase scope in .repo/briefs/{phase_id}.md")
    remediation.append("4. Split into separate phase for out-of-scope work")
    
    return remediation


# Drift intelligence classification removed (protocol simplification)


def check_drift(phase: Dict[str, Any], plan: Dict[str, Any], baseline_sha: str = None) -> List[str]:
    """Check for changes outside phase scope (plan drift)."""
    issues = []

    # Check if drift gate is enabled
    drift_gate = phase.get("gates", {}).get("drift")
    if not drift_gate:
        return []  # Drift checking not enabled for this phase

    # Get base branch (fallback only)
    base_branch = plan.get("plan", {}).get("base_branch", "main")

    # Get changed files using baseline SHA for consistent diffs
    changed_files, warnings = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )
    
    # Display warnings if any
    for warning in warnings:
        print(f"  ⚠️  {warning}")

    if not changed_files:
        return []  # No changes or not a git repo

    # Get scope patterns from plan
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    # Amendment system removed - scope is now static from plan

    if not include_patterns:
        return []  # No scope defined, can't check drift

    # Simple classification: in-scope vs out-of-scope
    inner_files, outer_files = classify_files(changed_files, include_patterns, exclude_patterns)
    
    # Check forbidden patterns using shared utility
    drift_rules = phase.get("drift_rules", {})
    forbid_patterns = drift_rules.get("forbid_changes", [])
    forbidden_files = check_forbidden_files(changed_files, forbid_patterns)

    if forbidden_files:
        issues.append("Forbidden files changed (these require a separate phase):")
        for f in forbidden_files:
            issues.append(f"  - {f}")
        issues.extend(_generate_forbidden_remediation(forbidden_files, baseline_sha, REPO_ROOT))
        issues.append("")

    # Check out-of-scope files
    if outer_files:
        allowed_drift = drift_gate.get("allowed_out_of_scope_changes", 0)
        
        if len(outer_files) > allowed_drift:
            issues.append(f"Out-of-scope changes detected ({len(outer_files)} files, {allowed_drift} allowed):")
            for f in outer_files:
                issues.append(f"  - {f}")
            issues.append("")
            issues.extend(_generate_drift_remediation(outer_files, baseline_sha, phase_id, REPO_ROOT))
        else:
            print(f"✅ Scope expansion allowed: {len(outer_files)} files")

    return issues


def _analyze_failure_context(issues: List[str], gate_results: Dict[str, List[str]]) -> Dict[str, Any]:
    """Analyze what mechanisms are relevant for this failure."""
    context = {
        "has_drift": any("out-of-scope" in issue.lower() for issue in issues),
        "has_test_failures": any("test" in issue.lower() for issue in issues),
        "has_plan_corruption": any("plan changed mid-phase" in issue.lower() for issue in issues),
        "has_lint_failures": any("lint" in issue.lower() for issue in issues),
        "has_forbidden_files": any("forbidden" in issue.lower() for issue in issues),
    }
    return context


def write_critique(phase_id: str, issues: List[str], gate_results: Dict[str, List[str]] = None):
    """Write critique files with mechanism-aware resolution."""
    import tempfile
    import os
    import json

    # Ensure critiques directory exists
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)

    # Simplified critique (amendment system removed)
    context = _analyze_failure_context(issues, gate_results)

    # Markdown critique
    critique_content = f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

## Next Steps

Please address the issues above and re-run:
```
./tools/phasectl.py review {phase_id}
```
"""

    critique_file = CRITIQUES_DIR / f"{phase_id}.md"

    # Write MD to temp file first (atomic operation)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_",
        suffix=".tmp"
    ) as tmp:
        tmp.write(critique_content)
        tmp_path = tmp.name

    # Atomic replace MD
    os.replace(tmp_path, critique_file)

    # JSON critique (machine-readable)
    if gate_results is None:
        gate_results = {}

    critique_json = {
        "phase": phase_id,
        "timestamp": time.time(),
        "passed": False,
        "issues": [
            {
                "gate": gate,
                "messages": msgs
            }
            for gate, msgs in gate_results.items() if msgs
        ],
        "total_issue_count": len(issues),
        "context": context  # Include context for debugging
    }

    json_file = CRITIQUES_DIR / f"{phase_id}.json"

    # Write JSON to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_json_",
        suffix=".tmp"
    ) as tmp:
        json.dump(critique_json, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic replace JSON
    os.replace(tmp_path, json_file)

    # Clean up old approval files AFTER successful write
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    ok_json_file = CRITIQUES_DIR / f"{phase_id}.OK.json"
    if ok_file.exists():
        ok_file.unlink()
    if ok_json_file.exists():
        ok_json_file.unlink()

    log_info(f"Critique written to {get_relative_path(critique_file, REPO_ROOT)}")
    log_info(f"JSON critique: {get_relative_path(json_file, REPO_ROOT)}")


def write_approval(phase_id: str):
    """Write approval markers atomically (both .OK and .OK.json)."""
    import tempfile
    import os
    import json

    # Ensure critiques directory exists
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)

    approval_timestamp = time.time()
    approval_content = f"Phase {phase_id} approved at {approval_timestamp}\n"
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"

    # Write .OK to temp file first (atomic operation)
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_",
        suffix=".tmp"
    ) as tmp:
        tmp.write(approval_content)
        tmp_path = tmp.name

    # Atomic replace .OK
    os.replace(tmp_path, ok_file)

    # JSON approval (machine-readable)
    approval_json = {
        "phase": phase_id,
        "timestamp": approval_timestamp,
        "passed": True,
        "approved_at": approval_timestamp
    }

    ok_json_file = CRITIQUES_DIR / f"{phase_id}.OK.json"

    # Write JSON to temp file
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_ok_json_",
        suffix=".tmp"
    ) as tmp:
        json.dump(approval_json, tmp, indent=2)
        tmp_path = tmp.name

    # Atomic replace JSON
    os.replace(tmp_path, ok_json_file)

    # Clean up old critique files AFTER successful write
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    critique_json_file = CRITIQUES_DIR / f"{phase_id}.json"
    if critique_file.exists():
        critique_file.unlink()
    if critique_json_file.exists():
        critique_json_file.unlink()

    log_info(f"Approval written to {get_relative_path(ok_file, REPO_ROOT)}")
    log_info(f"JSON approval: {get_relative_path(ok_json_file, REPO_ROOT)}")


def explain_error(error_type: str, error_details: dict = None) -> str:
    """Convert technical errors to actionable guidance."""
    explanations = {
        "insufficient_budget": "💡 Run 'phasectl solutions' to see budget recovery options",
        "missing_brief": "💡 Run 'phasectl generate-briefs' to create missing briefs",
        "plan_mismatch": "💡 Run 'phasectl discover' to validate plan state",
        "scope_drift": "💡 Run 'phasectl reset' to update baseline SHA",
        "lint_scope": "💡 Check scope patterns in plan.yaml",
        "docs_gate": "💡 Verify documentation requirements in plan.yaml",
        "protocol_outdated": "💡 Run '../judge-gated-orchestrator/install-protocol.sh'",
        "baseline_corrupted": "💡 Run 'phasectl recover' to fix state corruption",
        "experimental_disabled": "💡 Enable experimental features in plan.yaml or use standard features"
    }
    
    base_message = explanations.get(error_type, f"💡 Run 'phasectl solutions' for help with {error_type}")
    
    # Add specific details if available
    if error_details:
        if error_type == "scope_drift" and "files" in error_details:
            files = error_details["files"][:3]  # Show first 3 files
            more = f" and {len(error_details['files']) - 3} more" if len(error_details['files']) > 3 else ""
            base_message += f"\n   Out-of-scope files: {', '.join(files)}{more}"
        elif error_type == "insufficient_budget" and "needed" in error_details:
            base_message += f"\n   Budget needed: {error_details['needed']}, available: {error_details.get('available', 'unknown')}"
    
    return base_message


def classify_error(exception: Exception) -> str:
    """Classify exception into error type for smart messaging."""
    error_msg = str(exception).lower()
    
    if "budget" in error_msg or "insufficient" in error_msg:
        return "insufficient_budget"
    elif "brief" in error_msg or "missing" in error_msg:
        return "missing_brief"
    elif "plan" in error_msg and ("mismatch" in error_msg or "corrupted" in error_msg):
        return "plan_mismatch"
    elif "scope" in error_msg and "drift" in error_msg:
        return "scope_drift"
    elif "lint" in error_msg:
        return "lint_scope"
    elif "documentation" in error_msg or "docs" in error_msg:
        return "docs_gate"
    elif "protocol" in error_msg and "outdated" in error_msg:
        return "protocol_outdated"
    elif "baseline" in error_msg and "corrupted" in error_msg:
        return "baseline_corrupted"
    elif "experimental" in error_msg:
        return "experimental_disabled"
    else:
        return "unknown_error"


def extract_error_details(exception: Exception) -> dict:
    """Extract relevant details from exception for smart messaging."""
    error_msg = str(exception)
    details = {}
    
    # Extract file lists from scope drift errors
    if "out-of-scope" in error_msg.lower():
        import re
        files_match = re.search(r'files: \[(.*?)\]', error_msg)
        if files_match:
            files_str = files_match.group(1)
            files = [f.strip().strip("'\"") for f in files_str.split(',')]
            details["files"] = files
    
    # Extract budget information
    if "budget" in error_msg.lower():
        import re
        needed_match = re.search(r'need (\d+)', error_msg)
        available_match = re.search(r'have (\d+)', error_msg)
        if needed_match:
            details["needed"] = needed_match.group(1)
        if available_match:
            details["available"] = available_match.group(1)
    
    return details

def judge_phase(phase_id: str):
    """Run all checks and produce verdict."""
    log_info(f"Judging phase {phase_id}...")

    # Load plan
    plan = load_plan()

    # Validate plan schema
    from lib.plan_validator import validate_plan
    validation_errors = validate_plan(plan)
    if validation_errors:
        log_error("Plan validation failed:")
        for error in validation_errors:
            log_error(f"   - {error}")
        log_error("Fix errors in .repo/plan.yaml and try again.")
        return 2

    try:
        phase = get_phase(plan, phase_id)
    except ValueError as e:
        log_error(f"Error: {e}")
        return 2

    # Load baseline SHA from CURRENT.json for consistent diffs
    baseline_sha = None
    current_file = REPO_DIR / "briefs/CURRENT.json"
    if current_file.exists():
        try:
            import json
            current = json.loads(current_file.read_text())
            baseline_sha = current.get("baseline_sha")
            if baseline_sha:
                # Verify baseline exists in git before using it
                import subprocess
                try:
                    subprocess.run(["git", "cat-file", "-e", baseline_sha], 
                                 check=True, capture_output=True)
                    print(f"  📍 Using baseline: {baseline_sha[:8]}...")
                except (subprocess.CalledProcessError, FileNotFoundError):
                    log_error(f"Baseline SHA {baseline_sha[:8]}... not found in git repository")
                    baseline_sha = None
        except (json.JSONDecodeError, KeyError):
            pass  # Tolerate missing or malformed CURRENT.json

    # CRITICAL: Verify protocol integrity FIRST
    print("  🔐 Checking protocol integrity...")

    # Check phase binding (plan/manifest unchanged mid-phase)
    current_file = REPO_DIR / "briefs/CURRENT.json"
    if current_file.exists():
        try:
            import json
            current = json.loads(current_file.read_text())
            binding_issues = verify_phase_binding(REPO_ROOT, current)
            if binding_issues:
                write_critique(phase_id, binding_issues)
                return 1
        except (json.JSONDecodeError, KeyError):
            pass  # Tolerate missing or malformed CURRENT.json

    # Check protocol lock (judge/tools haven't been tampered with)
    lock_issues = verify_protocol_lock(REPO_ROOT, plan, phase_id, baseline_sha)
    if lock_issues:
        write_critique(phase_id, lock_issues)
        return 1

    # Run all checks - Phase → Gates → Verdict
    all_issues = []
    
    # Get changed files for gates that need them
    base_branch = plan.get("plan", {}).get("base_branch", "main")
    changed_files, warnings = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )
    
    # Display warnings if any
    for warning in warnings:
        print(f"  ⚠️  {warning}")
    
    # Prepare execution context
    context = {
        "changed_files": changed_files,
        "baseline_sha": baseline_sha,
        "repo_root": REPO_ROOT,
        "traces_dir": TRACES_DIR
    }
    
    # Run all enabled gates
    print("  🔍 Running gates...")
    gate_results = run_gates(phase, plan, context)
    
    # Collect all issues
    for gate_name, issues in gate_results.items():
        all_issues.extend(issues)
        if issues:
            print(f"  ❌ {gate_name}: {len(issues)} issues")
        else:
            print(f"  ✅ {gate_name}: passed")

    # Fun UI sequence before verdict
    print("\n⚖️  Judge is deliberating...")
    time.sleep(1)
    print("🔍 Examining evidence...")
    time.sleep(0.5)
    print("🧪 Checking tests...")
    time.sleep(0.5)
    print("📋 Reviewing scope compliance...")
    time.sleep(0.5)

    # Verdict (write functions handle cleanup atomically)
    if all_issues:
        log_info("😤 VERDICT: REJECTED! 😤")
        log_info("   'Issues found. Please address and resubmit.'")
        write_critique(phase_id, all_issues, gate_results)
        
        # Add smart error messages for common issues
        print("\n💡 Smart Error Messages:")
        for issue in all_issues:
            if "insufficient budget" in issue.lower():
                print(f"   💡 {explain_error('insufficient_budget')}")
            elif "missing brief" in issue.lower():
                print(f"   💡 {explain_error('missing_brief')}")
            elif "plan mismatch" in issue.lower():
                print(f"   💡 {explain_error('plan_mismatch')}")
        print()
        
        return 1
    else:
        log_info("🎉 VERDICT: APPROVED! 🎉")
        log_info("   'Excellent work! Proceed to next phase.'")
        write_approval(phase_id)
        
        # Budget shaping and replay gate removed as part of protocol simplification
        
        return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: judge.py <PHASE_ID>")
        return 1

    phase_id = sys.argv[1]

    # Use file lock to prevent concurrent judge runs
    from lib.file_lock import acquire_file_lock as file_lock
    lock_file = REPO_ROOT / ".repo/.judge.lock"

    try:
        with file_lock(lock_file, timeout=60):
            return judge_phase(phase_id)
    except TimeoutError as e:
        print(f"❌ Could not acquire judge lock: {e}")
        print("   Another judge process may be running. Wait and try again.")
        return 2
    except Exception as e:
        error_type = classify_error(e)
        error_details = extract_error_details(e)
        smart_message = explain_error(error_type, error_details)
        
        print(f"❌ {error_type.replace('_', ' ').title()}: {e}")
        print(smart_message)
        
        # Only show traceback for unknown errors
        if error_type == "unknown_error":
            import traceback
            traceback.print_exc()
        
        return 2


if __name__ == "__main__":
    sys.exit(main())
