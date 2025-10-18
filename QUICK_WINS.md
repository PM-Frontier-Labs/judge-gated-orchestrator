# Quick Wins - Fix These First

These are the simplest, highest-impact changes you can make RIGHT NOW to improve this codebase.

---

## 1. Fix Protocol Manifest (5 minutes) 🔴 CRITICAL

**Why:** Security hole - files used by judge are not integrity-checked.

**File:** `tools/generate_manifest.py`

**Change:**
```python
PROTOCOL_FILES = [
    "tools/judge.py",
    "tools/phasectl.py",
    "tools/llm_judge.py",
    "tools/lib/__init__.py",
    "tools/lib/git_ops.py",
    "tools/lib/scope.py",
    "tools/lib/traces.py",
    "tools/lib/protocol_guard.py",
    "tools/lib/plan_validator.py",  # ADD THIS LINE
    "tools/lib/file_lock.py",       # ADD THIS LINE
]
```

**Then run:**
```bash
./tools/generate_manifest.py
git add .repo/protocol_manifest.json tools/generate_manifest.py
git commit -m "fix: add missing files to protocol manifest"
```

**Impact:** Prevents protocol tampering mid-phase.

---

## 2. Add Git Error Context (10 minutes) 🟡

**Why:** Silent failures hide real problems.

**File:** `tools/lib/git_ops.py`

**Current (line 79-81):**
```python
except subprocess.CalledProcessError:
    # Not a git repo or base branch doesn't exist
    return []
```

**Change to:**
```python
except subprocess.CalledProcessError as e:
    import sys
    print(f"⚠️  Git operation failed: {e}", file=sys.stderr)
    print(f"   This may not be a git repo, or base branch '{base_branch}' doesn't exist", file=sys.stderr)
    return []
```

**Impact:** Helps users debug git issues instead of getting silent empty list.

---

## 3. Fix Trace File Path (5 minutes) 🔵

**Why:** Confusing parent.parent.parent logic.

**File:** `tools/lib/traces.py` (line 59)

**Current:**
```python
f"See {trace_file.relative_to(trace_file.parent.parent.parent)} for details."
```

**Change to:**
```python
f"See .repo/traces/last_{gate_name}.txt for details."
```

**Impact:** Clearer error messages.

---

## 4. Document Concurrent Execution Limitation (2 minutes) 🔵

**Why:** File locking adds 110 lines of complexity for rare edge case.

**File:** `README.md`

**Add section:**
```markdown
## Limitations

- **Concurrent execution:** Don't run multiple reviews of the same phase simultaneously. 
  If you need this (CI/CD with parallel jobs), add `flock` wrapper:
  ```bash
  flock -w 60 .repo/.judge.lock ./tools/phasectl.py review $PHASE_ID
  ```
```

**Impact:** Documents edge case without adding 110 lines of code.

---

## 5. Simplify Error Messages in Judge (15 minutes) 🟠

**Why:** Inconsistent emoji usage and formatting.

**File:** `tools/judge.py`

**Current mix:**
```python
print("❌ Error: {message}")  # Some places
print("⚠️ Warning: {message}")  # Other places  
return ["Error message"]        # Other places
```

**Standardize:**
```python
# At top of file
def error(msg): print(f"❌ {msg}")
def warn(msg): print(f"⚠️  {msg}")
def success(msg): print(f"✅ {msg}")
def info(msg): print(f"ℹ️  {msg}")

# Then use consistently:
error("Plan validation failed")
warn("Git operation failed")
success("Phase approved")
info("Running tests...")
```

**Impact:** Consistent, readable output.

---

## 6. Remove Unused Imports (5 minutes) 🔵

**Why:** Clean code hygiene.

**Check all files for:**
```bash
# Find unused imports
pylint --disable=all --enable=unused-import tools/ src/
```

**Or manually review:**
- `tools/judge.py` - Any unused imports?
- `tools/phasectl.py` - Any unused imports?
- `tools/llm_judge.py` - Any unused imports?

**Impact:** Cleaner code.

---

## 7. Add Docstrings to All Public Functions (30 minutes) 🔵

**Why:** Easier for others to understand and contribute.

**Missing docstrings:**
```bash
# Find functions without docstrings
grep -n "^def " tools/*.py tools/lib/*.py | grep -v '"""'
```

**Add minimal docstrings:**
```python
def classify_files(changed_files, include_patterns, exclude_patterns):
    """
    Classify files as in-scope or out-of-scope based on patterns.
    
    Returns: (in_scope_list, out_of_scope_list)
    """
```

**Impact:** Better documentation.

---

## 8. Add Type Hints to Function Signatures (45 minutes) 🔵

**Why:** Makes code more maintainable and catches bugs.

**Current:**
```python
def get_changed_files(repo_root, include_committed=True, base_branch="main", baseline_sha=None):
    ...
```

**Better:**
```python
def get_changed_files(
    repo_root: Path,
    include_committed: bool = True,
    base_branch: str = "main",
    baseline_sha: Optional[str] = None
) -> List[str]:
    ...
```

**Impact:** Better IDE support, catches type errors early.

---

## 9. Create .gitignore for Python (2 minutes) 🔵

**Check if exists:**
```bash
cat .gitignore
```

**If missing or incomplete, add:**
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Project
.repo/.judge.lock
```

**Impact:** Cleaner git status.

---

## 10. Add Tests for Critical Functions (60 minutes) 🟠

**Priority test coverage:**

1. **test_protocol_guard.py** - Protocol integrity checking
2. **test_scope.py** - Scope classification (already exists ✓)
3. **test_git_ops.py** - Git operations
4. **test_plan_validator.py** - Schema validation

**Example test:**
```python
# tests/test_protocol_guard.py
def test_judge_tamper_detection(tmp_path):
    """Verify judge tamper is detected."""
    # Setup: Create judge.py with known hash
    judge_file = tmp_path / "tools/judge.py"
    judge_file.parent.mkdir(parents=True)
    judge_file.write_text("# original")
    
    # Generate manifest
    manifest = generate_manifest([str(judge_file)])
    
    # Tamper with judge
    judge_file.write_text("# TAMPERED")
    
    # Verify detection
    issues = verify_protocol_lock(tmp_path, manifest, "P01")
    assert any("JUDGE TAMPER" in issue for issue in issues)
```

**Impact:** Prevent regressions, increase confidence.

---

## Priority Order (Time-based)

### Can do in <10 minutes:
1. Fix protocol manifest (5 min) 🔴
2. Fix trace file path (5 min)
3. Document concurrent limitation (2 min)
4. Create/update .gitignore (2 min)

**Total:** 14 minutes, 4 quick wins

---

### Can do in <30 minutes:
5. Add git error context (10 min)
6. Simplify error messages (15 min)
7. Remove unused imports (5 min)

**Total:** 30 minutes, 3 more improvements

---

### Can do in <2 hours:
8. Add docstrings (30 min)
9. Add type hints (45 min)
10. Add critical tests (60 min)

**Total:** 2 hours 15 min, professional polish

---

## Impact Summary

| Quick Win | Time | Impact | Priority |
|-----------|------|--------|----------|
| Protocol manifest | 5 min | Security | 🔴 Critical |
| Git error context | 10 min | Debugging | 🟡 High |
| Trace file path | 5 min | Clarity | 🔵 Medium |
| Error messages | 15 min | UX | 🟠 Medium |
| Docstrings | 30 min | Maintainability | 🔵 Low |
| Type hints | 45 min | Maintainability | 🔵 Low |
| Tests | 60 min | Reliability | 🟠 Medium |

---

## Start Here

```bash
# 1. Fix critical security issue (5 min)
vim tools/generate_manifest.py  # Add missing files
./tools/generate_manifest.py
git add .repo/protocol_manifest.json tools/generate_manifest.py
git commit -m "fix: add missing files to protocol manifest"

# 2. Improve error context (10 min)
vim tools/lib/git_ops.py  # Add error context
vim tools/lib/traces.py   # Fix path string

# 3. Run tests
pytest tests/ -v

# 4. Commit
git add tools/lib/
git commit -m "improve: better error context and messages"

# Done! 15 minutes, 2 commits, measurable improvement.
```

---

## What NOT To Do (Yet)

Don't start major refactoring before:
1. Fixing protocol manifest (critical)
2. Discussing breaking changes with team
3. Creating migration plan
4. Setting up v2.0 branch strategy

**Reason:** Quick wins are safe. Major refactoring needs planning.

---

## Questions?

- **"Which should I do first?"** → Protocol manifest (security critical)
- **"What if tests fail?"** → Fix tests, don't skip them
- **"Should I do all 10?"** → Do first 4 (14 min), evaluate impact, continue
- **"What about the big refactor?"** → See AUDIT_ACTION_PLAN.md for that

---

## Success Criteria

After quick wins:
- [ ] Protocol manifest includes all files ✓
- [ ] Git errors show helpful context ✓
- [ ] Error messages are consistent ✓
- [ ] All tests pass ✓
- [ ] No security holes ✓

**Total time investment:** 15-120 minutes depending on depth

**Return:** Measurably better codebase, no breaking changes

