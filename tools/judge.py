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

# Import shared utilities
from lib.git_ops import get_changed_files
from lib.scope import classify_files, check_forbidden_files
from lib.traces import check_gate_trace
from lib.protocol_guard import verify_protocol_lock, verify_phase_binding
from lib.state import load_phase_context
from lib.llm_pipeline import review_phase_with_llm

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
    """Get phase configuration from plan + runtime context"""
    phases = plan.get("plan", {}).get("phases", [])
    for phase in phases:
        if phase.get("id") == phase_id:
            # Get runtime state from context
            context = load_phase_context(phase_id)
            
            # Merge runtime state into phase config
            phase["runtime"] = {
                "baseline_sha": context.get("baseline_sha"),
                "test_cmd": context.get("test_cmd"),
                "mode": context.get("mode"),
                "scope_cache": context.get("scope_cache", {})
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




def check_docs(phase: Dict[str, Any], changed_files: List[str] = None) -> List[str]:
    """Check that documentation was actually updated in this phase."""
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

    if changed_files is None:
        changed_files = []

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
        if doc_path not in changed_files:
            issues.append(
                f"Documentation not updated in this phase: {doc_path}\n"
                f"   This file must be modified as part of {phase['id']}"
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


def classify_drift_intelligence(out_of_scope: List[str], phase_id: str, repo_root: str) -> tuple[List[str], List[str]]:
    """Classify out-of-scope changes as legitimate or rogue."""
    legitimate = []
    rogue = []
    
    for file_path in out_of_scope:
        if is_legitimate_change_with_context(file_path, repo_root):
            legitimate.append(file_path)
        else:
            rogue.append(file_path)
    
    return legitimate, rogue


def is_legitimate_change(file_path: str) -> bool:
    """Conservative classification of legitimate changes."""
    return (
        file_path.startswith("tools/") or  # Protocol tools
        file_path.startswith(".repo/") or  # Protocol state
        (file_path.endswith(".py") and "test" in file_path) or  # Test files
        file_path.endswith((".md", ".rst")) or  # Documentation files
        file_path in ["requirements.txt", "pyproject.toml", "setup.py"] or  # Project config
        (file_path.endswith(".py") and "src/" in file_path)  # Python files in src/ (linting fixes)
    )


def is_legitimate_change_with_context(file_path: str, repo_root: str) -> bool:
    """Enhanced classification using git diff context."""
    import subprocess
    
    # First check basic legitimate categories
    if is_legitimate_change(file_path):
        return True
    
    # For Python files in src/, check if it's a modification vs new file
    if file_path.endswith(".py") and "src/" in file_path:
        try:
            # Check if file exists in baseline (modification) vs new file
            result = subprocess.run(
                ["git", "diff", "--name-status", "HEAD~1", "HEAD", "--", file_path],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and result.stdout.strip():
                # File was modified (M) - likely legitimate linting fix
                if result.stdout.strip().startswith("M"):
                    return True
                # File was added (A) - likely rogue feature
                elif result.stdout.strip().startswith("A"):
                    return False
            
            # Fallback: check if file exists in git history
            result = subprocess.run(
                ["git", "log", "--oneline", "-1", "--", file_path],
                cwd=repo_root,
                capture_output=True,
                text=True
            )
            
            # If file has git history, it's a modification (legitimate)
            # If no history, it's likely a new file (rogue)
            return result.returncode == 0 and result.stdout.strip() != ""
            
        except Exception:
            # If git analysis fails, be conservative and block
            return False
    
    return False


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
    changed_files = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )

    if not changed_files:
        return []  # No changes or not a git repo

    # Get scope patterns from plan
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])
    exclude_patterns = scope.get("exclude", [])

    # Load runtime scope amendments
    phase_id = phase.get("id")
    if phase_id:
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
        return []  # No scope defined, can't check drift

    # Classify files using shared utility
    in_scope, out_of_scope = classify_files(
        changed_files,
        include_patterns,
        exclude_patterns
    )

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

    # NEW: Intelligent drift classification
    if out_of_scope:
        legitimate_changes, rogue_changes = classify_drift_intelligence(
            out_of_scope, phase_id, str(REPO_ROOT)
        )
        
        # Log legitimate changes for transparency
        if legitimate_changes:
            print(f"✅ Auto-approved {len(legitimate_changes)} legitimate changes")
        
        # Apply intelligent limits - only count rogue changes against the limit
        allowed_drift = drift_gate.get("allowed_out_of_scope_changes", 0)
        
        if len(rogue_changes) > allowed_drift:
            issues.append(f"Out-of-scope changes detected ({len(rogue_changes)} unauthorized files, {allowed_drift} allowed):")
            for f in rogue_changes:
                issues.append(f"  - {f}")
            issues.append("")
            issues.extend(_generate_drift_remediation(rogue_changes, baseline_sha, phase_id, REPO_ROOT))

    return issues


def apply_learning_rewards(phase_id: str) -> Dict[str, Any]:
    """Apply immediate rewards for learning behavior."""
    rewards = {}
    
    # Pattern usage bonus
    if _patterns_were_used(phase_id):
        rewards["amendment_budget_bonus"] = 1
        rewards["enhanced_brief_unlock"] = True
    
    # Micro-retrospective contribution bonus
    if _micro_retrospective_contributed(phase_id):
        rewards["advanced_patterns_unlock"] = True
    
    return rewards

def _patterns_were_used(phase_id: str) -> bool:
    """Check if patterns were used in this phase."""
    return _count_pattern_checks(phase_id) > 0

def _micro_retrospective_contributed(phase_id: str) -> bool:
    """Check if micro-retrospective was contributed."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline", "-10", "--grep", "retrospective"],
            capture_output=True,
            text=True
        )
        return "retrospective" in result.stdout.lower()
    except Exception:
        return False

def show_learning_rewards(phase_id: str) -> str:
    """Show learning rewards in critiques."""
    rewards = apply_learning_rewards(phase_id)
    
    if rewards:
        reward_text = "### 🎁 Learning Rewards\n"
        for reward, value in rewards.items():
            reward_text += f"- {reward}: {value}\n"
        return reward_text
    
    return ""

def track_learning_metrics(phase_id: str) -> Dict[str, Any]:
    """Track learning behavior metrics."""
    return {
        "patterns_checked": _count_pattern_checks(phase_id),
        "amendments_based_on_patterns": _count_pattern_based_amendments(phase_id),
        "learning_score": _calculate_learning_score(phase_id)
    }

def _count_pattern_checks(phase_id: str) -> int:
    """Count how many times patterns were checked in this phase."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline", "-10", "--grep", "patterns"],
            capture_output=True,
            text=True
        )
        return len([line for line in result.stdout.split('\n') if 'patterns' in line.lower()])
    except Exception:
        return 0

def _count_pattern_based_amendments(phase_id: str) -> int:
    """Count amendments that reference patterns."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline", "-10", "--grep", "pattern"],
            capture_output=True,
            text=True
        )
        return len([line for line in result.stdout.split('\n') if 'pattern' in line.lower()])
    except Exception:
        return 0

def _calculate_learning_score(phase_id: str) -> int:
    """Calculate learning score based on behavior."""
    patterns_checked = _count_pattern_checks(phase_id)
    pattern_amendments = _count_pattern_based_amendments(phase_id)
    
    # Simple scoring: 1 point per pattern check, 2 points per pattern-based amendment
    score = patterns_checked + (pattern_amendments * 2)
    return min(score, 10)  # Cap at 10

def show_learning_progress(phase_id: str) -> str:
    """Show learning progress in critiques."""
    metrics = track_learning_metrics(phase_id)
    
    if metrics["learning_score"] > 0:
        return f"""
### 📚 Learning Progress
- Patterns checked: {metrics['patterns_checked']}
- Pattern-based amendments: {metrics['amendments_based_on_patterns']}
- Learning score: {metrics['learning_score']}/10
"""
    return ""

def check_learning_requirements(phase_id: str) -> List[str]:
    """Check if agent engaged with collective intelligence."""
    issues = []
    
    # Check if patterns were consulted (for drift issues)
    if _has_drift_issues(phase_id) and not _patterns_were_checked(phase_id):
        issues.append("Pattern checking required: ./tools/phasectl.py patterns list")
    
    return issues

def _has_drift_issues(phase_id: str) -> bool:
    """Check if current phase has drift issues."""
    try:
        critique_file = CRITIQUES_DIR / f"{phase_id}.md"
        if critique_file.exists():
            content = critique_file.read_text()
            return "out-of-scope" in content.lower() or "drift" in content.lower()
    except Exception:
        pass
    return False

def _patterns_were_checked(phase_id: str) -> bool:
    """Check if patterns were consulted in this phase."""
    try:
        # Check if patterns command was run recently
        import subprocess
        result = subprocess.run(
            ["git", "log", "--oneline", "-10", "--grep", "patterns"],
            capture_output=True,
            text=True
        )
        return "patterns" in result.stdout.lower()
    except Exception:
        pass
    return False

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


def _generate_mechanism_resolution(context: Dict[str, Any], phase_id: str) -> str:
    """Generate mechanism-aware resolution based on failure context."""
    
    if context["has_drift"]:
        return f"""### 🚨 REQUIRED: Pattern-Driven Amendment Process

**Step 1: Check available patterns (REQUIRED):**
```bash
./tools/phasectl.py patterns list
```

**Step 2: Propose amendment based on patterns:**
```bash
# If patterns suggest: add_scope for src/ files
./tools/phasectl.py amend propose add_scope "src/file.py" "Following pattern: add_scope for Python files in src/"

# If no patterns apply, explain why:
./tools/phasectl.py amend propose add_scope "src/file.py" "No patterns apply - new scenario requiring scope expansion"
```

**Step 3: Re-run review:**
```bash
./tools/phasectl.py review {phase_id}
```

**💡 Why this works:**
- Patterns may suggest the exact amendment needed
- Amendment system is the proper way to handle scope expansion
- This teaches agents the protocol's collective intelligence capabilities"""

    elif context["has_plan_corruption"]:
        return f"""### 🚨 CRITICAL: Plan State Corruption

**REQUIRED: Use recovery commands (DO NOT manually edit state files):**

```bash
# Detect and recover from corruption
./tools/phasectl.py recover

# Reset phase state to match current plan
./tools/phasectl.py reset {phase_id}

# Re-run review
./tools/phasectl.py review {phase_id}
```

**💡 What happened:**
- Plan file was modified externally (git checkout, etc.)
- Protocol state is inconsistent with current plan
- Recovery commands will fix the state mismatch"""

    elif context["has_test_failures"]:
        return f"""### 🚨 REQUIRED: Fix Test Failures

```bash
# Check test results
cat .repo/traces/last_tests.txt

# Fix failing tests and re-run
./tools/phasectl.py review {phase_id}
```

### 💡 OPTIONAL: Performance Optimization

```bash
# Check patterns for test fixes
./tools/phasectl.py patterns list

# Consider test scoping (if tests are slow)
# Add to plan.yaml:
gates:
  tests:
    test_scope: "scope"  # Run only relevant tests
    quarantine:          # Skip flaky tests
      - path: "tests/flaky_test.py"
        reason: "External API timeout"
```"""

    elif context["has_lint_failures"]:
        return f"""### 🚨 REQUIRED: Fix Linting Issues

```bash
# Check lint results
cat .repo/traces/last_lint.txt

# Fix linting issues and re-run
./tools/phasectl.py review {phase_id}
```

### 💡 OPTIONAL: Check Patterns

```bash
# Check patterns for lint fixes
./tools/phasectl.py patterns list
```"""

    elif context["has_forbidden_files"]:
        return f"""### 🚨 CRITICAL: Forbidden Files Changed

**REQUIRED: Revert forbidden files (these require a separate phase):**

```bash
# Revert forbidden files
git restore requirements.txt pyproject.toml

# Re-run review
./tools/phasectl.py review {phase_id}
```

**💡 What happened:**
- Forbidden files (requirements.txt, pyproject.toml) were modified
- These require a dedicated phase for dependency changes
- Never change forbidden files without creating a separate phase"""

    else:
        return "Please address the issues above and re-run the review."


def write_critique(phase_id: str, issues: List[str], gate_results: Dict[str, List[str]] = None):
    """Write critique files with mechanism-aware resolution."""
    import tempfile
    import os
    import json

    # Ensure critiques directory exists
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)

    # Analyze failure context
    context = _analyze_failure_context(issues, gate_results)
    
    # NEW: Check learning requirements
    learning_issues = check_learning_requirements(phase_id)
    if learning_issues:
        issues.extend(learning_issues)
    
    # Generate mechanism-aware resolution
    resolution = _generate_mechanism_resolution(context, phase_id)
    
    # NEW: Add learning progress
    learning_progress = show_learning_progress(phase_id)
    
    # NEW: Add learning rewards
    learning_rewards = show_learning_rewards(phase_id)

    # Markdown critique
    critique_content = f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

{learning_progress}
{learning_rewards}

## Resolution

{resolution}

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

    print(f"📝 Critique written to {critique_file.relative_to(REPO_ROOT)}")
    print(f"📊 JSON critique: {json_file.relative_to(REPO_ROOT)}")


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

    print(f"✅ Approval written to {ok_file.relative_to(REPO_ROOT)}")
    print(f"📊 JSON approval: {ok_json_file.relative_to(REPO_ROOT)}")


def judge_phase(phase_id: str):
    """Run all checks and produce verdict."""
    print(f"⚖️  Judging phase {phase_id}...")

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

    try:
        phase = get_phase(plan, phase_id)
    except ValueError as e:
        print(f"❌ Error: {e}")
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
                print(f"  📍 Using baseline: {baseline_sha[:8]}...")
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
    gate_results = {}  # Track results per gate for JSON output

    print("  🔍 Checking artifacts...")
    artifacts_issues = check_artifacts(phase)
    gate_results["artifacts"] = artifacts_issues
    all_issues.extend(artifacts_issues)

    print("  🔍 Checking tests...")
    tests_issues = check_gate_trace("tests", TRACES_DIR, "Tests")
    gate_results["tests"] = tests_issues
    all_issues.extend(tests_issues)

    # Lint check (optional)
    lint_gate = phase.get("gates", {}).get("lint", {})
    if lint_gate.get("must_pass", False):
        print("  🔍 Checking linting...")
        lint_issues = check_gate_trace("lint", TRACES_DIR, "Linting")
        gate_results["lint"] = lint_issues
        all_issues.extend(lint_issues)

    # Get changed files for docs and drift gates
    base_branch = plan.get("plan", {}).get("base_branch", "main")
    changed_files = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )

    print("  🔍 Checking documentation...")
    docs_issues = check_docs(phase, changed_files)
    gate_results["docs"] = docs_issues
    all_issues.extend(docs_issues)

    print("  🔍 Checking for plan drift...")
    drift_issues = check_drift(phase, plan, baseline_sha)
    gate_results["drift"] = drift_issues
    all_issues.extend(drift_issues)

    # LLM code review (optional)
    if LLM_JUDGE_AVAILABLE:
        llm_gate = phase.get("gates", {}).get("llm_review", {})
        if llm_gate.get("enabled", False):
            print("  🤖 Running LLM code review...")
            llm_issues = llm_code_review(phase, REPO_ROOT, plan, baseline_sha)
            gate_results["llm_review"] = llm_issues
            all_issues.extend(llm_issues)

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
        print("😤 VERDICT: REJECTED! 😤")
        print("   'Issues found. Please address and resubmit.'")
        write_critique(phase_id, all_issues, gate_results)
        return 1
    else:
        print("🎉 VERDICT: APPROVED! 🎉")
        print("   'Excellent work! Proceed to next phase.'")
        write_approval(phase_id)
        return 0


def main():
    if len(sys.argv) < 2:
        print("Usage: judge.py <PHASE_ID>")
        return 1

    phase_id = sys.argv[1]

    # Use file lock to prevent concurrent judge runs
    from lib.file_lock import file_lock
    lock_file = REPO_ROOT / ".repo/.judge.lock"

    try:
        with file_lock(lock_file, timeout=60):
            return judge_phase(phase_id)
    except TimeoutError as e:
        print(f"❌ Could not acquire judge lock: {e}")
        print("   Another judge process may be running. Wait and try again.")
        return 2
    except Exception as e:
        print(f"❌ Judge error: {e}")
        import traceback
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
