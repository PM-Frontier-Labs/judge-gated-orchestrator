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

# Import shared utilities
from lib.git_ops import get_changed_files
from lib.scope import classify_files, check_forbidden_files
from lib.traces import check_gate_trace
from lib.protocol_guard import verify_protocol_lock, verify_phase_binding
from lib.state import load_phase_context

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

    # Use simple drift classification (two-tier scope is experimental)
    if is_experimental_enabled("replay_budget"):
        # Two-tier scope classification: inner (free), outer (costed)
        inner_files, outer_files = check_two_tier_scope(phase_id, changed_files)
    else:
        # Simple classification: in-scope vs out-of-scope
        inner_files, outer_files = classify_files(changed_files, include_patterns, exclude_patterns)
    
    # Generalized maintenance burst: allow bounded, priced outer edits for repo-wide maintenance
    try:
        maintenance_triggered = _detect_maintenance_burst(REPO_ROOT, changed_files)
        if maintenance_triggered and outer_files:
            if _apply_maintenance_burst_cost(phase_id, outer_files):
                print(f"  🛠️  Maintenance burst approved for {len(outer_files)} outer files")
            else:
                print("  ❌ Maintenance burst denied (insufficient budget)")
    except Exception as e:
        print(f"  ⚠️  Maintenance burst check error: {e}")

    # Apply scope expansion cost for outer files (post-burst) - experimental feature only
    if outer_files and is_experimental_enabled("replay_budget"):
        if not apply_scope_expansion_cost(phase_id, outer_files):
            issues.append("Insufficient budget for scope expansion:")
            for f in outer_files:
                issues.append(f"  - {f}")
            issues.append("")
            return issues  # Stop here if budget insufficient
    
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

    # NEW: Intelligent drift classification for outer files
    if outer_files:
        legitimate_changes, rogue_changes = classify_drift_intelligence(
            outer_files, phase_id, str(REPO_ROOT)
        )
        
        # Log legitimate changes for transparency
        if legitimate_changes:
            print(f"✅ Auto-approved {len(legitimate_changes)} legitimate outer scope changes")
        
        # Apply intelligent limits - only count rogue changes against the limit
        allowed_drift = drift_gate.get("allowed_out_of_scope_changes", 0)
        
        if len(rogue_changes) > allowed_drift:
            issues.append(f"Out-of-scope changes detected ({len(rogue_changes)} unauthorized files, {allowed_drift} allowed):")
            for f in rogue_changes:
                issues.append(f"  - {f}")
            issues.append("")
            issues.extend(_generate_drift_remediation(rogue_changes, baseline_sha, phase_id, REPO_ROOT))
        else:
            print(f"✅ Scope expansion within budget: {len(outer_files)} files (cost: {len(outer_files)} points)")
            
            # Store scope expansion info for attribution tracking
            scope_info = {
                "inner_files": len(inner_files),
                "outer_files": len(outer_files),
                "scope_cost": len(outer_files)
            }
            # Store in phase context for later attribution
            try:
                from lib.state import save_phase_context
                context = {"scope_expansion": scope_info}
                save_phase_context(phase_id, context, str(REPO_ROOT))
            except Exception:
                pass  # Tolerate missing context

    return issues


def _detect_maintenance_burst(repo_root: Path, changed_files: List[str]) -> bool:
    """Detect generic maintenance events (format/import codemods, linter rule bump).

    Heuristics: high proportion of trivial diffs; presence of codemod receipts; linter config changes.
    """
    # Quick linter config check
    linter_configs = ["pyproject.toml", ".ruff.toml", ".flake8"]
    if any(cfg in changed_files for cfg in linter_configs):
        return True

    # Trivial change ratio could be expensive; keep simple and conservative
    # If many .py files changed and most are in src/ or tests/, allow burst
    py_changes = [f for f in changed_files if f.endswith(".py")]
    return len(py_changes) >= 20  # simple threshold for repo-wide maintenance


def _apply_maintenance_burst_cost(phase_id: str, outer_files: List[str]) -> bool:
    """Grant a one-time maintenance burst with hard cap; charge immediately.

    This does not create a new currency; it only tops up scope_expansion_budget once if affordable.
    """
    budget_file = REPO_ROOT / ".repo" / "state" / "next_budget.json"
    if budget_file.exists():
        budget = json.loads(budget_file.read_text())
    else:
        budget = {"self_consistency": 1, "tool_budget_mul": 1.0, "test_scope": "full", "scope_expansion_budget": 1}

    # Hard cap the burst (small)
    cap = 20
    burst_needed = min(len(outer_files), cap)

    # If we already have enough budget, no top-up required
    current = int(budget.get("scope_expansion_budget", 1))
    if current >= burst_needed:
        return True

    # Top-up only up to cap
    budget["scope_expansion_budget"] = burst_needed
    budget_file.write_text(json.dumps(budget, indent=2))
    return True



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

def track_pattern_opt_out(phase_id: str, brief_content: str) -> bool:
    """Track if agent opted out of pattern injection (opt-out cost)."""
    try:
        # Check if patterns were injected
        if "Collective Intelligence (Auto-Injected)" not in brief_content:
            return False  # No patterns injected, no opt-out possible
        
        # Check if agent opted out (look for opt-out comments)
        opt_out_indicators = [
            "not relevant",
            "opt out", 
            "skip patterns",
            "ignore patterns",
            "not applicable"
        ]
        
        brief_lower = brief_content.lower()
        opted_out = any(indicator in brief_lower for indicator in opt_out_indicators)
        
        if opted_out:
            # Store opt-out for replay correlation
            opt_out_file = REPO_ROOT / ".repo" / "state" / "pattern_opt_outs.jsonl"
            opt_out_data = {
                "timestamp": time.time(),
                "phase_id": phase_id,
                "agent_info": get_agent_info(),
                "repo_info": get_repo_info()
            }
            
            with open(opt_out_file, "a") as f:
                f.write(json.dumps(opt_out_data) + "\n")
            
            print(f"  📝 Pattern opt-out tracked for phase {phase_id}")
        
        return opted_out
        
    except Exception as e:
        print(f"  ⚠️  Error tracking pattern opt-out: {e}")
        return False

def apply_opt_out_cost(phase_id: str, replay_score: float) -> None:
    """Apply cost for pattern opt-out if replay performance degraded."""
    # Only run if experimental feature enabled
    if not is_experimental_enabled("replay_budget"):
        return
    
    try:
        # Check if agent opted out
        opt_out_file = REPO_ROOT / ".repo" / "state" / "pattern_opt_outs.jsonl"
        if not opt_out_file.exists():
            return
        
        # Check if this phase had an opt-out
        opted_out = False
        with open(opt_out_file) as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if data.get("phase_id") == phase_id:
                        opted_out = True
                        break
        
        if not opted_out:
            return
        
        # Apply cost if replay performance was poor
        if replay_score < 0.5:  # Poor replay performance
            # Reduce next phase budget
            budget_file = REPO_ROOT / ".repo" / "state" / "next_budget.json"
            if budget_file.exists():
                budget = json.loads(budget_file.read_text())
                # Reduce tool budget multiplier
                budget["tool_budget_mul"] = max(0.8, budget.get("tool_budget_mul", 1.0) * 0.9)
                budget_file.write_text(json.dumps(budget, indent=2))
                print(f"  💰 Opt-out cost applied: Budget reduced due to poor replay performance")
        
    except Exception as e:
        print(f"  ⚠️  Error applying opt-out cost: {e}")

def run_replay_if_passed(phase_id: str):
    """Run replay test if all gates passed with guardrails (experimental feature)."""
    # Check if experimental features are enabled
    if not is_experimental_enabled("replay_budget"):
        return
    
    if not all_gates_passed(phase_id):
        return

    neighbor = select_neighbor_task(phase_id)
    if not neighbor:
        # Neutral fallback when no neighbor available; do not reshape budget
        record_gen_score(phase_id, 0.5, {"reason": "no_neighbor_neutral"})
        return

    budget = budget_for_replay()
    result = run_phase_like(phase_id, task=neighbor, budget=budget)

    # Objective neutral fallback criteria
    neutral_reasons: List[str] = []
    if isinstance(result, dict):
        if result.get("error") in {"Test timeout"}:
            neutral_reasons.append("timeout")
        if result.get("method") == "syntax_check":
            # Environment missing pytest; treat as neutral infra limitation
            neutral_reasons.append("infra_missing_pytest")

    if neutral_reasons:
        record_gen_score(phase_id, 0.5, {"neighbor": neighbor["id"], "neutral": ",".join(neutral_reasons)})
        return  # Do not reshape budget on neutral

    # Compute raw score then apply guardrail shaping
    raw_score = compute_gen_score(result, baseline_steps=2)

    # Track attribution for what helped replay success
    patterns_used = extract_patterns_used_from_brief(phase_id)

    # Load scope expansion info from phase context
    scope_expansion = None
    try:
        from lib.state import load_phase_context
        context = load_phase_context(phase_id, str(REPO_ROOT))
        scope_info = context.get("scope_expansion")
        if scope_info:
            scope_expansion = f"inner:{scope_info['inner_files']},outer:{scope_info['outer_files']},cost:{scope_info['scope_cost']}"
    except Exception:
        pass  # Tolerate missing context

    track_attribution(phase_id, result, patterns_used=patterns_used, scope_expansion=scope_expansion)

    # Shape budget with domain-normalized EWMA + hysteresis
    shaped_score = _apply_guardrailed_budget_shaping(phase_id, raw_score, neighbor_id=neighbor["id"])  # records score internally

    # Apply opt-out cost if patterns were rejected and replay suffered
    apply_opt_out_cost(phase_id, shaped_score)

def all_gates_passed(phase_id: str) -> bool:
    """Check if all gates passed for this phase."""
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    return ok_file.exists()

def select_neighbor_task(phase_id: str) -> Optional[dict]:
    """Select neighbor task for replay."""
    # Strategy 1: From golden set
    golden_neighbors = load_golden_neighbors(phase_id)
    if golden_neighbors:
        import random
        return random.choice(golden_neighbors)
    
    # Strategy 2: From same directory
    similar_files = find_similar_files(phase_id)
    if similar_files:
        return create_neighbor_task(similar_files[0])
    
    return None

def load_golden_neighbors(phase_id: str) -> List[dict]:
    """Load golden neighbor tasks for replay."""
    # For now, return empty list - can be populated with curated tasks
    return []

def find_similar_files(phase_id: str) -> List[str]:
    """Find similar files for neighbor task creation - v0.1 implementation."""
    try:
        # Get current phase files from scope
        plan = load_plan()
        phase = get_phase(plan, phase_id)
        scope = phase.get("scope", {})
        include_patterns = scope.get("include", [])
        
        similar_files = []
        
        # Find files in same directories as scope files
        for pattern in include_patterns:
            if pattern.endswith('.py'):
                dir_path = os.path.dirname(pattern)
                if os.path.exists(dir_path):
                    for f in os.listdir(dir_path):
                        if f.endswith('.py') and f != os.path.basename(pattern):
                            full_path = os.path.join(dir_path, f)
                            if os.path.exists(full_path):
                                similar_files.append(full_path)
        
        # Limit to 3 files to avoid too much overhead
        return similar_files[:3]
        
    except Exception as e:
        print(f"  ⚠️  Error finding similar files: {e}")
        return []

def create_neighbor_task(file_path: str) -> dict:
    """Create a neighbor task from a similar file."""
    return {
        "id": f"neighbor_{file_path.replace('/', '_')}",
        "file_path": file_path,
        "type": "similar_file"
    }

def budget_for_replay() -> dict:
    """Budget for replay test."""
    return {
        "max_steps": 2,
        "test_scope": "scope",
        "time_cap": 90,
        "lint_scope": "scope"
    }

def run_phase_like(phase_id: str, task: dict, budget: dict) -> dict:
    """Run a phase-like test - v0.1 implementation."""
    try:
        file_path = task["file_path"]
        
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "passed": False,
                "steps": 1,
                "time": 0,
                "task": task,
                "error": f"File not found: {file_path}"
            }
        
        # Run a simple test on the neighbor file
        # Try to run pytest on the file, but don't fail if pytest isn't available
        try:
            result = subprocess.run(
                ["python3", "-m", "pytest", file_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=budget["time_cap"],
                cwd=str(REPO_ROOT)
            )
            
            return {
                "passed": result.returncode == 0,
                "steps": 1,
                "time": len(result.stdout.split('\n')),  # Use line count as proxy for complexity
                "task": task,
                "stdout": result.stdout[:500],  # Truncate for storage
                "stderr": result.stderr[:500]
            }
        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "steps": 1,
                "time": budget["time_cap"],
                "task": task,
                "error": "Test timeout"
            }
        except FileNotFoundError:
            # pytest not available, try basic Python syntax check
            result = subprocess.run(
                ["python3", "-m", "py_compile", file_path],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(REPO_ROOT)
            )
            
            return {
                "passed": result.returncode == 0,
                "steps": 1,
                "time": 1,
                "task": task,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "method": "syntax_check"
            }
            
    except Exception as e:
        return {
            "passed": False,
            "steps": 1,
            "time": 0,
            "task": task,
            "error": str(e)
        }

def compute_gen_score(result: dict, baseline_steps: int) -> float:
    """Compute generalization score."""
    w1 = 0.7  # Pass weight
    w2 = 0.3  # Speed weight
    
    pass_score = 1.0 if result["passed"] else 0.0
    speed_score = clamp((baseline_steps - result["steps"]) / baseline_steps, 0, 1)
    
    return w1 * pass_score + w2 * speed_score

def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp value between min and max."""
    return max(min_val, min(max_val, value))

def record_gen_score(phase_id: str, score: float, meta: dict):
    """Record generalization score with telemetry."""
    gen_file = REPO_ROOT / ".repo" / "state" / "generalization.json"
    
    if not gen_file.exists():
        gen_file.write_text('{"by_component": {}, "by_model_profile": {}}')
    
    data = json.loads(gen_file.read_text())
    
    # Update by component
    component = extract_component(phase_id)
    if component not in data["by_component"]:
        data["by_component"][component] = {"avg": 0.0, "n": 0, "last": 0.0}
    
    data["by_component"][component]["n"] += 1
    data["by_component"][component]["last"] = score
    data["by_component"][component]["avg"] = (
        (data["by_component"][component]["avg"] * (data["by_component"][component]["n"] - 1) + score) 
        / data["by_component"][component]["n"]
    )
    
    gen_file.write_text(json.dumps(data, indent=2))
    
    # Add telemetry data
    telemetry = {
        "timestamp": time.time(),
        "phase_id": phase_id,
        "score": score,
        "meta": meta,
        "component": component,
        "agent_info": get_agent_info(),
        "repo_info": get_repo_info()
    }
    
    # Store in telemetry file
    telemetry_file = REPO_ROOT / ".repo" / "state" / "telemetry.jsonl"
    with open(telemetry_file, "a") as f:
        f.write(json.dumps(telemetry) + "\n")

def get_agent_info() -> dict:
    """Get agent information for telemetry."""
    try:
        # Try to get git user info
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        user_name = result.stdout.strip() if result.returncode == 0 else "unknown"
        
        return {
            "user": user_name,
            "timestamp": time.time()
        }
    except Exception:
        return {
            "user": "unknown",
            "timestamp": time.time()
        }

def get_repo_info() -> dict:
    """Get repository information for telemetry."""
    try:
        # Get current branch
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        branch = result.stdout.strip() if result.returncode == 0 else "unknown"
        
        # Get current commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT)
        )
        commit = result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
        
        return {
            "branch": branch,
            "commit": commit,
            "timestamp": time.time()
        }
    except Exception:
        return {
            "branch": "unknown",
            "commit": "unknown",
            "timestamp": time.time()
        }

def extract_component(phase_id: str) -> str:
    """Extract component name from phase ID."""
    # Simple extraction - can be made more sophisticated
    if "collective-intelligence" in phase_id:
        return "collective_intelligence"
    elif "execution-pattern" in phase_id:
        return "execution_patterns"
    else:
        return "general"

def auto_capture_patterns_from_critique(phase_id: str):
    """Extract patterns from successful critiques automatically - zero agent work."""
    try:
        critique_file = CRITIQUES_DIR / f"{phase_id}.md"
        if not critique_file.exists():
            return
        
        critique_content = critique_file.read_text()
        
        # Extract successful patterns from critique
        patterns = []
        
        # Look for successful fixes in the critique
        if "VERDICT: APPROVED" in critique_content:
            # Extract the resolution section
            lines = critique_content.split('\n')
            in_resolution = False
            
            for line in lines:
                if line.startswith('## Resolution'):
                    in_resolution = True
                    continue
                elif line.startswith('##') and in_resolution:
                    break
                elif in_resolution and line.strip():
                    # This is a resolution step - capture as pattern
                    if line.strip().startswith('-'):
                        pattern_text = line.strip()[1:].strip()
                        if pattern_text and len(pattern_text) > 10:
                            patterns.append({
                                "text": pattern_text,
                                "phase_id": phase_id,
                                "timestamp": time.time(),
                                "source": "auto_capture"
                            })
        
        # Store patterns
        if patterns:
            patterns_file = REPO_ROOT / ".repo" / "collective_intelligence" / "patterns.jsonl"
            patterns_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(patterns_file, "a") as f:
                for pattern in patterns:
                    f.write(json.dumps(pattern) + "\n")
            
            print(f"  📚 Auto-captured {len(patterns)} patterns from successful critique")
            
    except Exception as e:
        print(f"  ⚠️  Error auto-capturing patterns: {e}")

def load_relevant_patterns(phase_id: str) -> List[dict]:
    """Load patterns relevant to current phase."""
    try:
        patterns_file = REPO_ROOT / ".repo" / "collective_intelligence" / "patterns.jsonl"
        if not patterns_file.exists():
            return []
        
        relevant_patterns = []
        with open(patterns_file) as f:
            for line in f:
                if line.strip():
                    pattern = json.loads(line)
                    # Simple relevance check - can be made more sophisticated
                    if pattern.get("phase_id") != phase_id:  # Don't include self
                        relevant_patterns.append(pattern)
        
        # Return top 5 most recent patterns
        return sorted(relevant_patterns, key=lambda x: x.get("timestamp", 0), reverse=True)[:5]
        
    except Exception as e:
        print(f"  ⚠️  Error loading patterns: {e}")
        return []

def check_two_tier_scope(phase_id: str, changed_files: List[str]) -> tuple:
    """Check two-tier scope: inner (free), outer (costed)."""
    # Only run if experimental feature enabled
    if not is_experimental_enabled("replay_budget"):
        # Fallback to simple classification
        plan = load_plan()
        phase = get_phase(plan, phase_id)
        scope = phase.get("scope", {})
        include_patterns = scope.get("include", [])
        exclude_patterns = scope.get("exclude", [])
        return classify_files(changed_files, include_patterns, exclude_patterns)
    
    try:
        plan = load_plan()
        phase = get_phase(plan, phase_id)
        scope = phase.get("scope", {})
        include_patterns = scope.get("include", [])
        
        inner_files = []
        outer_files = []
        
        for file_path in changed_files:
            # Check if file is in inner scope (free)
            in_inner = False
            for pattern in include_patterns:
                if file_path.startswith(pattern) or pattern in file_path:
                    in_inner = True
                    break
            
            if in_inner:
                inner_files.append(file_path)
            else:
                outer_files.append(file_path)
        
        return inner_files, outer_files
        
    except Exception as e:
        print(f"  ⚠️  Error checking two-tier scope: {e}")
        return changed_files, []

def apply_scope_expansion_cost(phase_id: str, outer_files: List[str]) -> bool:
    """Apply cost for scope expansion (outer files)."""
    # Only run if experimental feature enabled
    if not is_experimental_enabled("replay_budget"):
        return True  # No cost if experimental feature disabled
    
    try:
        if not outer_files:
            return True  # No cost if no outer files
        
        # Load current budget
        budget_file = REPO_ROOT / ".repo" / "state" / "next_budget.json"
        if budget_file.exists():
            budget = json.loads(budget_file.read_text())
        else:
            budget = {"self_consistency": 1, "tool_budget_mul": 1.0, "test_scope": "full"}
        
        # Cost: 1 budget point per outer file
        cost = len(outer_files)
        current_budget = budget.get("scope_expansion_budget", 3)
        
        if cost <= current_budget:
            # Apply cost
            budget["scope_expansion_budget"] = current_budget - cost
            budget_file.write_text(json.dumps(budget, indent=2))
            print(f"  💰 Scope expansion cost: {cost} points (remaining: {budget['scope_expansion_budget']})")
            return True
        else:
            print(f"  ❌ Insufficient budget for scope expansion: need {cost}, have {current_budget}")
            return False
            
    except Exception as e:
        print(f"  ⚠️  Error applying scope expansion cost: {e}")
        return False

def apply_budget_shaping(score: float):
    """Apply budget shaping based on score (kept for legacy direct calls)."""
    budget = _budget_for_score(score)
    budget_file = REPO_ROOT / ".repo" / "state" / "next_budget.json"
    budget_file.write_text(json.dumps(budget, indent=2))


def _budget_for_score(score: float) -> dict:
    """Map score to 3-tier budget table with risk caps applied later."""
    if score >= 0.8:
        return {"self_consistency": 3, "tool_budget_mul": 1.25, "test_scope": "scope", "scope_expansion_budget": 5}
    if score >= 0.5:
        return {"self_consistency": 2, "tool_budget_mul": 1.10, "test_scope": "scope", "scope_expansion_budget": 3}
    return {"self_consistency": 1, "tool_budget_mul": 1.0, "test_scope": "full", "scope_expansion_budget": 1}


def _apply_guardrailed_budget_shaping(phase_id: str, raw_score: float, neighbor_id: str) -> float:
    """Normalize by domain anchor, smooth with EWMA, clamp tier movement, apply cooldown, write budget.

    Returns the shaped score used for tiering.
    """
    # Load generalization state
    gen_file = REPO_ROOT / ".repo" / "state" / "generalization.json"
    if gen_file.exists():
        try:
            gen_state = json.loads(gen_file.read_text())
        except Exception:
            gen_state = {"by_component": {}, "by_model_profile": {}}
    else:
        gen_state = {"by_component": {}, "by_model_profile": {}}

    domain = extract_component(phase_id)
    dom = gen_state.setdefault("by_component", {}).setdefault(domain, {"avg": 0.0, "n": 0, "last": 0.0, "anchor": 0.5, "ewma": 0.5, "last_tier": "medium"})

    # Blend with static anchor to prevent moving goalposts (λ=0.8)
    lam = 0.8
    normalized = lam * raw_score + (1 - lam) * float(dom.get("anchor", 0.5))

    # EWMA smoothing (α=0.3)
    alpha = 0.3
    ewma_prev = float(dom.get("ewma", 0.5))
    ewma_now = alpha * normalized + (1 - alpha) * ewma_prev

    # Determine desired tier
    desired_budget = _budget_for_score(ewma_now)
    tier_from_budget = {3: "high", 2: "medium", 1: "low"}
    desired_tier = tier_from_budget.get(desired_budget["self_consistency"], "medium")

    # Hysteresis: clamp movement to ±1 step
    order = {"low": 0, "medium": 1, "high": 2}
    last_tier = dom.get("last_tier", "medium")
    move = order[desired_tier] - order.get(last_tier, 1)
    if move > 1:
        desired_tier = "high" if last_tier == "medium" else last_tier
    elif move < -1:
        desired_tier = "medium" if last_tier == "high" else last_tier

    # Apply risk caps (simple: cap outer scope/self_consistency for sensitive components later if needed)
    final_budget = _budget_for_score({"low": 0.3, "medium": 0.6, "high": 0.85}[desired_tier])

    # Persist domain state
    dom["ewma"] = ewma_now
    dom["last"] = normalized
    dom["n"] = int(dom.get("n", 0)) + 1
    dom["last_tier"] = desired_tier
    gen_file.write_text(json.dumps(gen_state, indent=2))

    # Write budget
    budget_file = REPO_ROOT / ".repo" / "state" / "next_budget.json"
    budget_file.write_text(json.dumps(final_budget, indent=2))

    # Record shaped score with meta
    record_gen_score(phase_id, ewma_now, {"neighbor": neighbor_id, "normalized": True})

    return ewma_now

def track_attribution(phase_id: str, replay_result: dict, patterns_used: List[str] = None, amendments_accepted: List[dict] = None, scope_expansion: str = None):
    """Track which mechanisms helped replay success for attribution."""
    try:
        attribution = {
            "timestamp": time.time(),
            "phase_id": phase_id,
            "replay_result": replay_result,
            "patterns_used": patterns_used or [],
            "amendments_accepted": amendments_accepted or [],
            "scope_expansion": scope_expansion,
            "agent_info": get_agent_info(),
            "repo_info": get_repo_info()
        }
        
        # Store attribution data
        attribution_file = REPO_ROOT / ".repo" / "state" / "attribution.jsonl"
        with open(attribution_file, "a") as f:
            f.write(json.dumps(attribution) + "\n")
        
        print(f"  📊 Attribution tracked: {len(patterns_used or [])} patterns, {len(amendments_accepted or [])} amendments")
        
    except Exception as e:
        print(f"  ⚠️  Error tracking attribution: {e}")

def extract_patterns_used_from_brief(phase_id: str) -> List[str]:
    """Extract which patterns were used from the brief content."""
    try:
        brief_path = REPO_ROOT / ".repo" / "briefs" / f"{phase_id}.md"
        if not brief_path.exists():
            return []
        
        brief_content = brief_path.read_text()
        patterns_used = []
        
        # Look for pattern references in the brief
        if "Collective Intelligence (Auto-Injected)" in brief_content:
            # Extract pattern IDs from the brief
            lines = brief_content.split('\n')
            for line in lines:
                if "**From" in line and "**: " in line:
                    # Extract phase ID from pattern reference
                    phase_match = line.split("**From ")[1].split("**:")[0]
                    patterns_used.append(phase_match)
        
        return patterns_used
        
    except Exception as e:
        print(f"  ⚠️  Error extracting patterns used: {e}")
        return []

def auto_suggest_amendments_from_errors(phase_id: str, issues: List[str]) -> List[dict]:
    """Generate amendment suggestions from errors and patterns (binary classification)."""
    try:
        suggestions = []
        
        # Load relevant patterns
        patterns = load_relevant_patterns(phase_id)
        
        # Analyze issues and match to patterns
        for issue in issues:
            # Look for common error patterns
            if "out-of-scope" in issue.lower():
                # Suggest scope expansion (needs approval)
                suggestions.append({
                    "type": "add_scope",
                    "value": "tools/",
                    "reason": "Auto-suggested: Protocol tools need scope access",
                    "safe_to_auto": False,
                    "source": "error_analysis"
                })
            
            elif "test" in issue.lower() and "fail" in issue.lower():
                # Suggest test scoping (safe-to-auto)
                suggestions.append({
                    "type": "set_test_cmd",
                    "value": "python3 -m pytest -q",
                    "reason": "Auto-suggested: Simplify test command for reliability",
                    "safe_to_auto": True,
                    "source": "error_analysis"
                })
            
            elif "lint" in issue.lower():
                # Suggest lint scoping (safe-to-auto)
                suggestions.append({
                    "type": "set_lint_cmd",
                    "value": "python3 -m ruff check",
                    "reason": "Auto-suggested: Use Python module for linting",
                    "safe_to_auto": True,
                    "source": "error_analysis"
                })
        
        # Match issues to stored patterns
        for pattern in patterns:
            pattern_text = pattern.get("text", "").lower()
            for issue in issues:
                issue_lower = issue.lower()
                # Simple keyword matching - can be made more sophisticated
                if any(keyword in pattern_text for keyword in ["scope", "test", "lint"]) and \
                   any(keyword in issue_lower for keyword in ["scope", "test", "lint"]):
                    suggestions.append({
                        "type": "pattern_match",
                        "pattern_id": pattern.get("phase_id", "unknown"),
                        "pattern_text": pattern_text,
                        "reason": f"Auto-suggested: Matches pattern from {pattern.get('phase_id', 'previous phase')}",
                        "confidence": 0.6,
                        "source": "pattern_match"
                    })
        
        return suggestions
        
    except Exception as e:
        print(f"  ⚠️  Error auto-suggesting amendments: {e}")
        return []

def auto_apply_amendments(phase_id: str, suggestions: List[dict]) -> List[dict]:
    """Auto-apply only safe-to-auto amendments (minimal auto-apply)."""
    try:
        applied = []
        
        # Safe-to-auto catalog (pre-approved by Security/Owners)
        safe_to_auto_types = {
            "set_test_cmd": "Test command simplification",
            "set_lint_cmd": "Lint command simplification", 
            "quarantine_test": "Test quarantine for known issues"
        }
        
        # Apply only safe-to-auto suggestions
        for suggestion in suggestions:
            if suggestion.get("safe_to_auto", False):
                applied.append(suggestion)
                print(f"  ✅ Auto-applied (safe-to-auto): {suggestion['type']} - {suggestion['reason']}")
            else:
                print(f"  📝 Suggestion (needs approval): {suggestion['type']} - {suggestion['reason']}")
        
        return applied
        
    except Exception as e:
        print(f"  ⚠️  Error auto-applying amendments: {e}")
        return []

def write_critique(phase_id: str, issues: List[str], gate_results: Dict[str, List[str]] = None):
    """Write critique files with mechanism-aware resolution."""
    import tempfile
    import os
    import json

    # Ensure critiques directory exists
    CRITIQUES_DIR.mkdir(parents=True, exist_ok=True)

    # Analyze failure context
    context = _analyze_failure_context(issues, gate_results)
    
    # Auto-suggest amendments from errors
    suggestions = auto_suggest_amendments_from_errors(phase_id, issues)
    applied = auto_apply_amendments(phase_id, suggestions)
    
    # Generate mechanism-aware resolution
    resolution = _generate_mechanism_resolution(context, phase_id)

    # Markdown critique
    critique_content = f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

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
    changed_files, warnings = get_changed_files(
        REPO_ROOT,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )
    
    # Display warnings if any
    for warning in warnings:
        print(f"  ⚠️  {warning}")

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
        print("🎉 VERDICT: APPROVED! 🎉")
        print("   'Excellent work! Proceed to next phase.'")
        write_approval(phase_id)
        
        # Auto-capture patterns from successful critique
        print("  📚 Auto-capturing patterns...")
        auto_capture_patterns_from_critique(phase_id)
        
        # Run replay gate for generalization scoring (experimental)
        if is_experimental_enabled("replay_budget"):
            print("  🔍 Running replay gate...")
            run_replay_if_passed(phase_id)
        else:
            print("  ⚠️  Replay gate disabled (experimental feature)")
        
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
