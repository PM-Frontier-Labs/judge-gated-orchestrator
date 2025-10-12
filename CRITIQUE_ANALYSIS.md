# Critique Loop Analysis: Priority Assessment

**Source:** 3 independent critique loops with variance analyzing the complete protocol package

**Goal:** Identify critical gaps, need-to-have changes, and nice-to-have enhancements

---

## 🚨 CRITICAL GAPS (Address Immediately)

These issues appear in **all 3 loops** and have concrete negative impacts:

### 1. Per-Phase Baseline SHA (ALL 3 LOOPS)
**Problem:** Current implementation uses `merge-base` with main branch, which drifts as main advances. Earlier approved commits on same branch appear as "out-of-scope" in later phases.

**Impact:**
- Intermittent drift failures during overnight runs
- False positives blocking autonomous progression
- Inconsistent diff basis across gates

**Solution:**
```python
# In phasectl.py next_phase() around line 300:
baseline_sha = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True, text=True
).stdout.strip()

current_data = {
    "phase_id": next_id,
    "brief_path": str(next_brief.relative_to(REPO_ROOT)),
    "status": "active",
    "started_at": time.time(),
    "baseline_sha": baseline_sha  # NEW: Fixed diff anchor
}
```

```python
# In tools/lib/git_ops.py get_changed_files():
def get_changed_files(
    repo_root: Path,
    baseline_sha: str = None,  # NEW parameter
    include_committed: bool = True,
    base_branch: str = "main"
) -> List[str]:
    if baseline_sha:
        # Use fixed baseline instead of merge-base
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{baseline_sha}...HEAD"],
            cwd=repo_root, capture_output=True, text=True
        )
        committed = result.stdout.strip().split("\n") if result.stdout.strip() else []
    else:
        # Fallback to merge-base (existing logic)
        ...
```

**Files to modify:**
- `tools/phasectl.py` (lines 300-314)
- `tools/lib/git_ops.py` (lines 10-40)
- `tools/judge.py` (pass baseline_sha to drift/docs gates)

**Estimated effort:** 2-3 hours

---

### 2. Docs Gate Doesn't Verify Actual Changes (ALL 3 LOOPS)
**Problem:** Current `check_docs()` only verifies file existence and non-zero size. A stale doc from previous phase satisfies the gate without any update in current phase.

**Impact:**
- Phases pass without documentation updates
- False sense of doc completeness
- Gate doesn't enforce its stated purpose

**Current code (judge.py:81-101):**
```python
def check_docs(phase: Dict[str, Any]) -> List[str]:
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

    # BUG: Only checks existence, not if changed in this phase
    for doc in must_update:
        doc_path = doc.split("#")[0]
        path = REPO_ROOT / doc_path

        if not path.exists():
            issues.append(f"Documentation not found: {doc_path}")
        elif path.stat().st_size == 0:
            issues.append(f"Documentation is empty: {doc_path}")

    return issues
```

**Solution:**
```python
def check_docs(phase: Dict[str, Any], changed_files: List[str]) -> List[str]:
    """Check that required docs were actually updated in this phase."""
    issues = []
    docs_gate = phase.get("gates", {}).get("docs", {})
    must_update = docs_gate.get("must_update", [])

    if not must_update:
        return issues

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

        # NEW: Check if doc was changed in this phase
        if doc_path not in changed_files:
            issues.append(
                f"Documentation not updated in this phase: {doc_path}\n"
                f"   This file must be modified as part of {phase['id']}"
            )
            continue

        # NEW: If anchor specified, verify heading exists
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
```

**Files to modify:**
- `tools/judge.py` (lines 81-101, and caller around line 253)

**Estimated effort:** 1-2 hours

---

### 3. LLM Review Only Inspects Uncommitted Files (ALL 3 LOOPS)
**Problem:** `llm_judge.py` calls `get_changed_files(include_committed=False)` while all other gates use `include_committed=True`. Committed code bypasses LLM scrutiny.

**Current code (tools/llm_judge.py:43-52):**
```python
def llm_code_review(phase: Dict[str, Any], repo_root: Path) -> List[str]:
    # ...

    # BUG: Only gets uncommitted changes
    changed_files = get_changed_files(
        repo_root,
        include_committed=False,  # <-- WRONG
        base_branch=base_branch
    )
```

**Impact:**
- Inconsistent file sets across gates
- Agent can commit bad code to bypass LLM review
- Defeats purpose of semantic review

**Solution:**
```python
def llm_code_review(
    phase: Dict[str, Any],
    repo_root: Path,
    baseline_sha: str = None  # NEW: Same baseline as other gates
) -> List[str]:
    # ...

    # Use same change basis as other gates
    changed_files = get_changed_files(
        repo_root,
        baseline_sha=baseline_sha,  # NEW
        include_committed=True,     # FIXED
        base_branch=base_branch
    )
```

**Files to modify:**
- `tools/llm_judge.py` (lines 43-52)
- `tools/judge.py` (line 264 - pass baseline_sha)

**Estimated effort:** 30 minutes

---

### 4. Scope Matching Uses fnmatch (Lacks Globstar Support) (LOOP 1)
**Problem:** Python's `fnmatch` doesn't support `**` globstar semantics. Pattern like `src/**/*.py` won't match `src/foo/bar/baz.py`.

**Current code (tools/lib/scope.py:10-35):**
```python
import fnmatch

def classify_files(
    files: List[str],
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> Tuple[List[str], List[str]]:
    in_scope = []
    out_of_scope = []

    for file in files:
        # BUG: fnmatch doesn't handle ** properly
        included = any(fnmatch.fnmatch(file, pattern) for pattern in include_patterns)
        excluded = any(fnmatch.fnmatch(file, pattern) for pattern in exclude_patterns)
        # ...
```

**Impact:**
- **Critical:** False negatives/positives in drift detection
- Paths misclassified → blocking legitimate work or missing drift
- Undermines trust in the protocol

**Solution:**
```python
# Use pathspec library (already in Python stdlib alternatives or pip install pathspec)
import pathspec

def classify_files(
    files: List[str],
    include_patterns: List[str],
    exclude_patterns: List[str]
) -> Tuple[List[str], List[str]]:
    """Classify files using .gitignore-style pattern matching."""
    in_scope = []
    out_of_scope = []

    # Create pathspec objects (supports **, negation, etc.)
    include_spec = pathspec.PathSpec.from_lines('gitwildmatch', include_patterns)
    exclude_spec = pathspec.PathSpec.from_lines('gitwildmatch', exclude_patterns)

    for file in files:
        included = include_spec.match_file(file)
        excluded = exclude_spec.match_file(file)

        if excluded:
            out_of_scope.append(file)
        elif included:
            in_scope.append(file)
        else:
            out_of_scope.append(file)

    return in_scope, out_of_scope
```

**Files to modify:**
- `tools/lib/scope.py` (lines 10-50)
- `requirements.txt` (add `pathspec>=0.11.0`)

**Test cases to add:**
```python
# tests/test_scope.py
def test_globstar_matching():
    files = ["src/foo/bar.py", "src/baz.py", "docs/readme.md"]
    include = ["src/**/*.py"]
    exclude = []
    in_scope, out = classify_files(files, include, exclude)
    assert "src/foo/bar.py" in in_scope  # fnmatch would FAIL this
    assert "src/baz.py" in in_scope
    assert "docs/readme.md" in out
```

**Estimated effort:** 2 hours (including tests)

---

## ✅ NEED TO HAVE (High Impact, Not Blocking)

### 5. Atomic Critique Writes (LOOPS 2, 3)
**Problem:** Current code deletes old critiques then writes new ones. Crash during write = no feedback.

**Current code (judge.py:266-273):**
```python
# Clean up old critiques/approvals
for old_file in CRITIQUES_DIR.glob(f"{phase_id}.*"):
    old_file.unlink()  # BUG: Delete before write = not atomic

# Verdict
if all_issues:
    write_critique(phase_id, all_issues)
    return 1
else:
    write_approval(phase_id)
    return 0
```

**Solution:**
```python
import tempfile
import os

def write_critique(phase_id: str, issues: List[str]):
    """Atomically write critique file."""
    critique_content = f"""# Critique: {phase_id}

## Issues Found

{chr(10).join(f"- {issue}" for issue in issues)}

## Resolution

Please address the issues above and re-run:
```
./tools/phasectl.py review {phase_id}
```
"""

    critique_file = CRITIQUES_DIR / f"{phase_id}.md"

    # Write to temp file first
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=CRITIQUES_DIR,
        delete=False,
        prefix=f".{phase_id}_",
        suffix=".tmp"
    ) as tmp:
        tmp.write(critique_content)
        tmp_path = tmp.name

    # Atomic replace
    os.replace(tmp_path, critique_file)

    # Clean up old files AFTER successful write
    for old_file in CRITIQUES_DIR.glob(f"{phase_id}.OK"):
        old_file.unlink()

    print(f"📝 Critique written to {critique_file.relative_to(REPO_ROOT)}")
```

**Estimated effort:** 1 hour

---

### 6. Drift Remediation Commands Are Wrong (LOOPS 1, 2)
**Problem:** Critique suggests `git checkout HEAD <file>` to fix drift, but this doesn't revert **committed** changes.

**Current code (judge.py:152, 164):**
```python
issues.append(f"Fix: git checkout HEAD {' '.join(forbidden_files)}")  # WRONG for committed

issues.append(f"1. Revert: git checkout HEAD {' '.join(out_of_scope)}")  # WRONG for committed
```

**Solution:**
```python
def check_drift(phase: Dict[str, Any], plan: Dict[str, Any], baseline_sha: str = None) -> List[str]:
    # ... existing logic ...

    # Determine if changes are committed or uncommitted
    committed_out_of_scope = []
    uncommitted_out_of_scope = []

    if baseline_sha:
        # Check which out-of-scope files are committed vs uncommitted
        committed_result = subprocess.run(
            ["git", "diff", "--name-only", f"{baseline_sha}...HEAD"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )
        committed_files = set(committed_result.stdout.strip().split("\n"))

        for f in out_of_scope:
            if f in committed_files:
                committed_out_of_scope.append(f)
            else:
                uncommitted_out_of_scope.append(f)
    else:
        # Fallback: assume uncommitted
        uncommitted_out_of_scope = out_of_scope

    if len(out_of_scope) > allowed_drift:
        issues.append(f"Out-of-scope changes detected ({len(out_of_scope)} files, {allowed_drift} allowed):")
        for f in out_of_scope:
            issues.append(f"  - {f}")
        issues.append("")
        issues.append("Options to fix:")

        if uncommitted_out_of_scope:
            issues.append(f"1. Revert uncommitted: git restore --worktree --staged -- {' '.join(uncommitted_out_of_scope[:3])}")

        if committed_out_of_scope:
            issues.append(f"2. Restore committed to baseline: git restore --source={baseline_sha} -- {' '.join(committed_out_of_scope[:3])}")
            issues.append(f"   (Or revert commits: git revert <commit-range>)")

        issues.append(f"3. Update phase scope in .repo/briefs/{phase['id']}.md")
        issues.append("4. Split into separate phase for out-of-scope work")
```

**Estimated effort:** 1-2 hours

---

### 7. Machine-Readable Critique JSON (LOOPS 1, 3)
**Problem:** Only human-readable Markdown exists. External tools/CI must parse Markdown (fragile).

**Solution:**
```python
def write_critique_json(phase_id: str, all_issues: List[str], gate_results: Dict[str, List[str]]):
    """Write machine-readable critique alongside Markdown."""
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
        "total_issue_count": len(all_issues)
    }

    json_file = CRITIQUES_DIR / f"{phase_id}.json"
    with tempfile.NamedTemporaryFile(
        mode='w', dir=CRITIQUES_DIR, delete=False, suffix='.tmp'
    ) as tmp:
        json.dump(critique_json, tmp, indent=2)
        tmp_path = tmp.name
    os.replace(tmp_path, json_file)

def write_approval_json(phase_id: str):
    """Write machine-readable approval."""
    approval_json = {
        "phase": phase_id,
        "timestamp": time.time(),
        "passed": True,
        "approved_at": time.time()
    }

    json_file = CRITIQUES_DIR / f"{phase_id}.OK.json"
    # ... atomic write ...
```

**Update judge.py to track gate results:**
```python
def judge_phase(phase_id: str):
    # ...
    gate_results = {}

    artifacts_issues = check_artifacts(phase)
    gate_results["artifacts"] = artifacts_issues
    all_issues.extend(artifacts_issues)

    test_issues = check_gate_trace("tests", TRACES_DIR, "Tests")
    gate_results["tests"] = test_issues
    all_issues.extend(test_issues)

    # ... etc for each gate ...

    if all_issues:
        write_critique(phase_id, all_issues)
        write_critique_json(phase_id, all_issues, gate_results)  # NEW
        return 1
    else:
        write_approval(phase_id)
        write_approval_json(phase_id)  # NEW
        return 0
```

**Estimated effort:** 2 hours

---

### 8. LLM Gate Configuration (ALL 3 LOOPS)
**Problem:** LLM settings hardcoded. Can't configure model, budget, timeout per project.

**Current hardcoded values (llm_judge.py:60-68):**
```python
message = client.messages.create(
    model="claude-sonnet-4-20250514",  # Hardcoded
    max_tokens=2000,  # Hardcoded
    temperature=0,
    messages=[...]
)
```

**Solution - Add to plan.yaml:**
```yaml
plan:
  llm_review_config:
    model: "claude-sonnet-4-20250514"
    max_tokens: 2000
    temperature: 0
    timeout_seconds: 60
    budget_usd: 0.50
    fail_on_transport_error: false
    include_extensions: [".py", ".pyx", ".rs", ".go"]
    exclude_patterns: ["**/test_*.py", "**/generated/**"]
```

**Update llm_judge.py:**
```python
def llm_code_review(phase: Dict[str, Any], repo_root: Path, plan: Dict[str, Any], baseline_sha: str = None) -> List[str]:
    # Get config with defaults
    llm_config = plan.get("plan", {}).get("llm_review_config", {})
    model = llm_config.get("model", "claude-sonnet-4-20250514")
    max_tokens = llm_config.get("max_tokens", 2000)
    temperature = llm_config.get("temperature", 0)
    timeout = llm_config.get("timeout_seconds", 60)
    budget_usd = llm_config.get("budget_usd", None)
    fail_on_error = llm_config.get("fail_on_transport_error", False)
    include_exts = llm_config.get("include_extensions", [".py"])

    # ... filter files by include_exts ...

    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            messages=[...]
        )
    except Exception as e:
        if fail_on_error:
            return [f"LLM review failed: {e}"]
        else:
            print(f"⚠️  LLM review skipped due to error: {e}")
            return []
```

**Estimated effort:** 2-3 hours

---

## 🎁 NICE TO HAVE (Lower Priority)

### 9. Judge Runs Tests Directly (LOOP 3)
**Benefit:** Prevents stale traces if judge.py run directly
**Tradeoff:** Adds complexity; phasectl.py already enforces order
**Recommendation:** Keep current architecture (phasectl orchestrates)

### 10. Flaky Test Handling (LOOPS 1, 2)
**Benefit:** Retry logic, quarantine lists
**Tradeoff:** Complexity, may mask real issues
**Recommendation:** Defer until flaky tests become a real problem

### 11. Snapshot-Based Review (LOOP 2)
**Benefit:** Eliminates TOCTOU races
**Tradeoff:** Complex git manipulation
**Recommendation:** Current approach is sufficient; address only if races observed

### 12. Critique History Tracking (LOOP 2)
**Benefit:** Audit trail of all judge attempts
**Tradeoff:** Disk usage, complexity
**Recommendation:** Defer; git history already provides this

### 13. Container Runner (LOOP 2)
**Benefit:** Hermetic test execution
**Tradeoff:** Adds Docker dependency, complexity
**Recommendation:** Keep protocol simple; users can wrap in Docker if needed

### 14. Language Profiles (LOOP 3)
**Benefit:** Better defaults for non-Python projects
**Tradeoff:** More configuration surface area
**Recommendation:** Make test_command and lint_command explicit in plan.yaml (already supported)

### 15. Plan Schema Validation (LOOP 3)
**Benefit:** Catch config errors early
**Tradeoff:** Maintenance burden for schema
**Recommendation:** Add basic validation (required keys) without full schema

### 16. Concurrency Locks (LOOPS 2, 3)
**Benefit:** Prevents race conditions
**Tradeoff:** Complexity, likely not needed for single-developer use
**Recommendation:** Defer unless concurrent execution becomes common

### 17. Rename Detection in Drift (LOOP 3)
**Benefit:** Better handling of file renames
**Tradeoff:** More complex git parsing
**Recommendation:** Nice polish, not critical

---

## 📋 Implementation Priority Order

### Phase 1: Critical Gaps (1-2 days)
**Must do immediately:**
1. ✅ Per-phase baseline SHA (#1) - 2-3 hours
2. ✅ Fix docs gate to verify changes (#2) - 1-2 hours
3. ✅ LLM review file set alignment (#3) - 30 min
4. ✅ Replace fnmatch with pathspec (#4) - 2 hours

**Total: ~6-8 hours of focused work**

### Phase 2: Need to Have (2-3 days)
**High value, lower urgency:**
5. ✅ Atomic critique writes (#5) - 1 hour
6. ✅ Fix drift remediation commands (#6) - 1-2 hours
7. ✅ Machine-readable JSON critiques (#7) - 2 hours
8. ✅ LLM gate configuration (#8) - 2-3 hours

**Total: ~6-8 hours**

### Phase 3: Nice to Have (defer until needed)
9. Judge runs tests directly - Skip (current design is better)
10. Flaky test handling - Wait for real need
11. Snapshot review - Wait for race conditions
12. Critique history - Defer
13. Container runner - Out of scope (users can wrap)
14. Language profiles - Defer (already configurable)
15. Plan validation - Add basic checks only
16. Concurrency locks - Defer
17. Rename detection - Polish later

---

## 🎯 Recommended Action Plan

### Immediate (This Week)
1. **Start with baseline SHA** - This fixes the most critical architectural issue
2. **Fix docs gate** - 1-line change, huge impact
3. **LLM file alignment** - Quick win
4. **Replace fnmatch** - Prevents false drift

### Next Sprint (1-2 weeks)
5. Add atomic writes
6. Fix remediation messages
7. Add JSON critique output
8. Make LLM configurable

### Backlog
- Everything in "Nice to Have" section
- Revisit based on real usage patterns

---

## 📊 Success Metrics After Phase 1+2

**Reliability:**
- ✅ Zero false drift positives in stacked phases (baseline SHA fixes this)
- ✅ Docs gate accurately enforces updates (change detection fixes this)
- ✅ Consistent file sets across all gates (LLM alignment fixes this)
- ✅ Proper globstar matching (pathspec fixes this)

**Usability:**
- ✅ Atomic writes prevent lost critiques
- ✅ Accurate remediation commands
- ✅ Machine-readable output for CI/tooling
- ✅ Configurable LLM settings per project

**Unchanged (Good):**
- File-based protocol
- Zero dependencies (except pathspec)
- Terminal-native
- Language-agnostic

---

## 🚫 What NOT to Change

**All 3 loops agree to keep:**
- File-based state (no servers, no daemons)
- Single judge architecture
- Terminal-native commands
- Explicit phase briefs
- Protocol simplicity

**Resist:**
- Adding frameworks or heavy dependencies
- Moving away from files as API
- Introducing long-running processes
- Over-engineering for hypothetical scale issues
