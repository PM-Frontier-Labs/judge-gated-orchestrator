# Code Audit: Judge-Gated Phase Protocol
**Auditor Perspective:** IC9 Senior Engineer @ Meta  
**Focus:** Protocol simplicity, clarity, maintainability  
**Date:** 2025-10-18

---

## Executive Summary

**Status:** ⚠️ **NEEDS SIMPLIFICATION**

This codebase has **drifted from its core mission**: a simple, powerful protocol for gated phase execution. While the implementation is solid and well-structured, it has accumulated framework-like complexity that violates the "protocol, not framework" philosophy stated in README.md.

**Core Issue:** ~2,400 lines of Python implementing what should be a <1,000 line reference implementation of a simple file-based protocol.

**Recommendation:** Aggressive simplification. Remove 40% of code. Return to protocol essence.

---

## Philosophy Violations

### 1. "Protocol, not Framework" ❌

**Current State:**
```python
# 300+ lines of schema validation
plan_validator.py: validate_plan() with comprehensive type checking

# 220+ lines of LLM integration with budget tracking
llm_judge.py: Cost estimation, file size limits, token counting

# 110+ lines of file locking with platform detection
file_lock.py: fcntl vs Windows fallback, stale lock detection
```

**What README.md Promises:**
> "This is a protocol, not a framework. You don't install it, you follow it."

**Reality:** This IS a framework. File locking abstractions, schema validators, cost tracking are framework concerns.

**Fix:**
- Move complex validation to optional lint/check commands
- Simplify llm_judge to bare essentials
- Use OS-level file locking or remove it entirely

---

## Critical Issues

### ISSUE #1: Schema Validator is a Framework 🔴

**File:** `tools/lib/plan_validator.py` (301 lines)

**Problem:**
```python
def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """280 lines of type checking, bounds validation, duplicate detection"""
    # Validates 20+ fields with custom error messages
    # Checks temperature ranges, token limits, file extensions
    # Framework-level validation for a "simple protocol"
```

**Why This is Wrong:**
- A protocol should define file formats, not enforce them programmatically
- YAML itself provides structure
- Over-validation prevents evolution and experimentation
- Users can't easily fork/modify without breaking validation

**Solution:**
```bash
# Simple validation: Does the file parse?
yaml.safe_load(plan.yaml)  # 1 line

# Let the system fail naturally if config is wrong
# Judge will fail → User fixes config → System works
# This is how Git works. This is how protocols work.
```

**Impact:** Remove 250 lines, keep basic YAML parsing only

---

### ISSUE #2: LLM Judge is Overengineered 🟡

**File:** `tools/llm_judge.py` (223 lines)

**Problem:**
```python
# Budget tracking
if estimated_cost > budget_usd:
    return [f"LLM review exceeded budget: ${estimated_cost:.4f}"]

# File size limits
MAX_FILE_SIZE_BYTES = 50 * 1024
MAX_TOTAL_CONTEXT_BYTES = 200 * 1024

# Token cost calculation
input_cost_per_1k = 0.003
output_cost_per_1k = 0.015
estimated_cost = (input_tokens / 1000 * input_cost_per_1k) + ...
```

**Why This is Wrong:**
- Cost tracking belongs in user's billing dashboard, not protocol
- File size limits are arbitrary and will break for legitimate use cases
- Hard-coded pricing will become stale
- 100+ lines of "framework" for an optional gate

**Solution:**
```python
def llm_code_review(phase, repo_root, plan, baseline_sha):
    """Simple LLM review: 50 lines max"""
    changed_files = get_changed_files(...)
    code_context = "\n\n".join([f.read_text() for f in changed_files[:10]])
    
    response = client.messages.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": f"Review this code:\n{code_context}"}]
    )
    
    if "APPROVED" in response.content[0].text:
        return []
    return [response.content[0].text]
```

**Impact:** Remove 150+ lines of budget/size logic. Keep simple review.

---

### ISSUE #3: File Locking is Framework Territory 🟡

**File:** `tools/lib/file_lock.py` (110 lines)

**Problem:**
```python
@contextmanager
def file_lock(lock_file: Path, timeout: int = 30):
    """110 lines of fcntl vs Windows fallback, stale detection"""
    try:
        import fcntl
        # Unix locking logic (40 lines)
    except ImportError:
        # Windows fallback (40 lines)
        # Stale lock detection (10 lines)
```

**Why This is Wrong:**
- Concurrent execution is an edge case, not core protocol
- OS-level locking (`flock` command) exists
- Platform abstraction is framework thinking
- Adds 110 lines for a rare scenario

**Solution A (Keep it simple):**
```bash
# In judge.py entrypoint:
flock -w 30 .repo/.judge.lock ./tools/judge.py "$@"
```

**Solution B (Remove entirely):**
- Document: "Don't run concurrent reviews"
- If users need it, they can add `flock` themselves
- This is a protocol, not a framework

**Impact:** Remove 110 lines OR replace with 1-line OS call

---

### ISSUE #4: Test Scoping is Feature Creep 🟠

**File:** `tools/phasectl.py` lines 64-140

**Problem:**
```python
# Test scoping with quarantine lists
if test_scope == "scope":
    # 50 lines of pathspec matching
    # Directory discovery
    # Fallback pattern matching
    
# Quarantine handling
quarantine = test_gate.get("quarantine", [])
for item in quarantine:
    test_path = item.get("path")
    reason = item.get("reason")
    print(f"Quarantined: {test_path} - {reason}")
    test_cmd.extend(["--deselect", test_path])
```

**Why This is Wrong:**
- Quarantine lists are workarounds for bad tests → Fix the tests
- Test scoping adds 60+ lines and another configuration layer
- Users should run full test suite OR filter with pytest directly
- Protocol shouldn't have opinions about test strategy

**Solution:**
```python
# Simple: Run the test command from plan.yaml
test_cmd = plan.get("test_command", "pytest tests/ -v")
exit_code = subprocess.run(test_cmd, ...)

# Users who want scoping:
test_command: "pytest tests/mvp/ -v"  # Just specify the path
```

**Impact:** Remove 60 lines of test scoping logic

---

### ISSUE #5: Dual Output Formats (.md + .json) 🟠

**Files:** `tools/judge.py` lines 254-401

**Problem:**
```python
def write_critique(phase_id, issues, gate_results):
    """Write both .md and .json atomically with temp files"""
    # MD critique (40 lines with atomic replace)
    # JSON critique (40 lines with atomic replace)
    
def write_approval(phase_id):
    """Write both .OK and .OK.json atomically"""
    # .OK file (30 lines)
    # .OK.json file (30 lines)
```

**Why This is Wrong:**
- Two formats for same data = maintenance burden
- Atomic temp file writes are framework-level concerns
- If users need JSON, they can parse the .md themselves
- Protocol should have ONE canonical format

**Solution:**
```python
# Keep .md for humans (primary format)
def write_critique(phase_id, issues):
    critique = f"# Critique: {phase_id}\n\n" + "\n".join(issues)
    (CRITIQUES_DIR / f"{phase_id}.md").write_text(critique)

def write_approval(phase_id):
    (CRITIQUES_DIR / f"{phase_id}.OK").write_text(f"Approved: {time.time()}\n")

# Users who need JSON can run:
# ./tools/parse_critique.py P01-scaffold  # Optional tool
```

**Impact:** Remove 80 lines, keep simple .md/.OK formats

---

## Medium Priority Issues

### ISSUE #6: Baseline SHA Tracking Adds Complexity 🟡

**Files:** `tools/phasectl.py`, `tools/judge.py`, `tools/lib/git_ops.py`

**Problem:**
```python
# CURRENT.json stores baseline_sha
current_data["baseline_sha"] = baseline_sha

# All git operations check baseline_sha first, fallback to merge-base
changed_files = get_changed_files(
    repo_root,
    include_committed=True,
    base_branch=base_branch,
    baseline_sha=baseline_sha  # Optional parameter
)
```

**Why This Matters:**
- Adds parameter to every git operation
- Conditional logic: "if baseline_sha else merge-base"
- Solving problem that may not exist in practice

**Solution:**
```python
# Simpler: Always use merge-base
merge_base = subprocess.run(["git", "merge-base", "HEAD", base_branch])
changed_files = subprocess.run(["git", "diff", "--name-only", f"{merge_base}...HEAD"])

# If user has issue with base branch advancing, they can:
# 1. Work in short phases (won't advance much)
# 2. Pin base_branch to specific commit in plan.yaml
```

**Impact:** Remove baseline_sha parameter from 5+ functions

---

### ISSUE #7: Plan Validator Missing From Manifest 🔴

**File:** `.repo/protocol_manifest.json`

**Problem:**
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
    # MISSING: "tools/lib/plan_validator.py"  ← Used by judge, not protected!
]
```

**Why This is Critical:**
- `plan_validator.py` is imported by judge.py and phasectl.py
- Not in manifest = can be modified mid-phase without detection
- Security hole in protocol integrity system

**Solution:**
```python
PROTOCOL_FILES = [
    # ... existing ...
    "tools/lib/plan_validator.py",  # ADD THIS
    "tools/lib/file_lock.py",       # ADD THIS
]
```

---

### ISSUE #8: Git Operations Have No Error Context 🟠

**File:** `tools/lib/git_ops.py` lines 79-81

**Problem:**
```python
except subprocess.CalledProcessError:
    # Not a git repo or base branch doesn't exist
    return []
```

**Why This Matters:**
- Silent failures hide real problems
- "Not a git repo" vs "base branch missing" are different issues
- No way to debug when git operations fail

**Solution:**
```python
except subprocess.CalledProcessError as e:
    # Print warning, don't silently return []
    print(f"⚠️  Git operation failed: {e}", file=sys.stderr)
    print(f"   This may not be a git repo, or base branch '{base_branch}' doesn't exist")
    return []
```

---

### ISSUE #9: Multiple Configuration Layers 🟠

**Current Structure:**
```yaml
plan:
  test_command: "pytest tests/ -v"           # Layer 1: Global
  llm_review_config:                         # Layer 2: Global LLM config
    model: "claude-sonnet-4"
    max_tokens: 2000
  
  phases:
    - id: P01
      gates:
        tests:
          test_scope: "scope"                # Layer 3: Phase-specific
          quarantine: [...]                  # Layer 4: Test-specific exceptions
        llm_review:
          enabled: true                      # Layer 5: Gate-specific
```

**Why This is Wrong:**
- 5 layers of configuration for a "simple protocol"
- Users must understand: global → phase → gate → gate-specific config
- Harder to debug: "Why isn't my test running?" → Check 4 places

**Solution:**
```yaml
plan:
  phases:
    - id: P01
      test_command: "pytest tests/mvp/ -v"   # Simple: One place, one config
      gates:
        tests: true
        docs: ["docs/mvp.md"]
        drift: { max: 0 }
```

**Impact:** Flatten configuration, remove nesting

---

## Low Priority / Style Issues

### ISSUE #10: Inconsistent Error Message Format 🔵

**Current:**
```python
# Some errors:
print("❌ Error: Phase not found")

# Other errors:
return ["Missing required artifact: file.py"]

# Other errors:
print(f"⚠️  Warning: {message}")
```

**Fix:** Standardize on one format (e.g., always emoji + prefix)

---

### ISSUE #11: Trace Files Have Weird Relative Path Logic 🔵

**File:** `tools/lib/traces.py` line 59

```python
f"See {trace_file.relative_to(trace_file.parent.parent.parent)} for details."
# What is parent.parent.parent? Just hardcode .repo/traces/
```

**Fix:**
```python
f"See .repo/traces/last_{gate_name}.txt for details."
```

---

## What This Codebase Does Well ✅

### 1. **Clean Separation of Concerns**
- `lib/` utilities are well-factored
- Judge, phasectl, and llm_judge are separate
- Each file has clear responsibility

### 2. **Good Test Coverage**
- Scope matching tests
- Test scoping tests
- Golden path tests

### 3. **Comprehensive Documentation**
- README.md is excellent
- PROTOCOL.md is detailed
- LLM_PLANNING.md for AI assistants
- Orient.sh for quick context recovery

### 4. **Protocol Integrity System**
- SHA256 manifest checking
- Phase binding (plan_sha, manifest_sha)
- Self-check of judge.py before running

### 5. **Git Integration**
- Uncommitted + committed change detection
- Merge-base fallback
- Proper pathspec pattern matching

---

## Recommended Changes (Priority Order)

### Phase 1: Remove Framework Bloat (Week 1)

1. **Simplify plan_validator.py** (Remove 250 lines)
   - Keep: YAML parsing, basic structure check
   - Remove: Type validation, bounds checking, duplicate detection
   - Let system fail naturally with helpful errors

2. **Simplify llm_judge.py** (Remove 150 lines)
   - Keep: Basic code review
   - Remove: Budget tracking, file size limits, cost estimation

3. **Replace or remove file_lock.py** (Remove 110 lines)
   - Option A: Use `flock` command
   - Option B: Document "don't run concurrent reviews"

4. **Remove test scoping** (Remove 60 lines)
   - Users specify test path in test_command directly
   - Remove quarantine lists feature

5. **Remove dual formats** (Remove 80 lines)
   - Keep .md and .OK files only
   - Remove .json outputs

**Total Reduction:** ~650 lines (27% smaller)

---

### Phase 2: Simplify Architecture (Week 2)

6. **Flatten configuration**
   - Remove nested config layers
   - One place per setting

7. **Remove baseline_sha tracking**
   - Always use merge-base
   - Simpler mental model

8. **Fix protocol manifest**
   - Add plan_validator.py
   - Add file_lock.py

9. **Improve error messages**
   - Consistent format
   - Better context on failures

**Total Reduction:** ~100 lines

---

### Phase 3: Documentation (Week 3)

10. **Update README.md**
    - Reflect simplified protocol
    - Remove mentions of removed features

11. **Update PROTOCOL.md**
    - Remove test scoping docs
    - Remove quarantine docs
    - Simplify configuration examples

12. **Update GETTING_STARTED.md**
    - Simpler examples
    - Fewer configuration options

---

## Final State (After Refactor)

### Codebase Size
```
Current:  ~2,400 lines
Target:   ~1,600 lines (33% reduction)
```

### Core Files (Target)
```
tools/judge.py          ~300 lines (was 547)
tools/phasectl.py       ~250 lines (was 472)
tools/llm_judge.py      ~50 lines  (was 223)
tools/lib/scope.py      ~80 lines  (unchanged)
tools/lib/git_ops.py    ~80 lines  (unchanged)
tools/lib/traces.py     ~65 lines  (unchanged)
tools/lib/protocol_guard.py ~150 lines (unchanged)
tools/lib/plan_validator.py ~50 lines (was 301)
tools/lib/file_lock.py  REMOVED or ~10 lines
```

### Philosophy Alignment
- ✅ Protocol, not framework
- ✅ Simple file conventions
- ✅ <1,000 lines of core logic
- ✅ Forkable and hackable
- ✅ Easy to understand in 30 minutes

---

## Specific Code Smells

### 1. Over-abstraction
```python
# tools/lib/traces.py
def check_gate_trace(gate_name: str, traces_dir: Path, error_prefix: str) -> List[str]:
    """12 lines to read exit code from file and return error"""
    
# Could be:
trace = Path(f".repo/traces/last_{gate_name}.txt").read_text()
exit_code = int(trace.split("\n")[0].split(": ")[1])
return [] if exit_code == 0 else [f"{gate_name} failed"]
```

### 2. Premature Optimization
```python
# tools/llm_judge.py
if total_size + file_size > MAX_TOTAL_CONTEXT_BYTES:
    files_skipped += 1
    break

# Why? Let LLM API handle token limits. YAGNI.
```

### 3. Configuration Sprawl
```yaml
# 22 lines of LLM config for optional gate
llm_review_config:
  model: "claude-sonnet-4-20250514"
  max_tokens: 2000
  temperature: 0
  timeout_seconds: 60
  budget_usd: null
  fail_on_transport_error: false
  include_extensions: [".py"]
  exclude_patterns: []

# Should be:
llm_review:
  model: "claude-sonnet-4"
```

---

## Questions for Team

1. **File Locking:** Do we actually need it? Has anyone reported concurrent execution issues?

2. **Test Scoping:** Can we push this to users via test_command configuration?

3. **Budget Tracking:** Is this used in production? Or YAGNI?

4. **JSON Outputs:** Does any tooling depend on .json files? Or can we remove them?

5. **Plan Validation:** What breaks if we remove 90% of validator?

---

## Comparison to Similar Systems

### Git (The Gold Standard)
```bash
.git/HEAD                  # Points to current branch
.git/refs/heads/main       # Branch pointer
.git/config                # Simple INI format

# Simple, hackable, no validation
```

### This Protocol (Current)
```python
.repo/briefs/CURRENT.json  # Points to current phase
.repo/critiques/P01.OK     # Approval marker
.repo/plan.yaml            # Configuration

# BUT: 300 lines of validation, 200 lines of LLM budget tracking, 110 lines of file locking
```

### This Protocol (Target)
```bash
.repo/briefs/CURRENT.json  # Points to current phase
.repo/critiques/P01.OK     # Approval marker
.repo/plan.yaml            # Configuration

# Simple validator: yaml.safe_load()
# Let system fail naturally
```

---

## Action Items

### Critical (Fix Now)
- [ ] Add plan_validator.py to protocol manifest
- [ ] Add file_lock.py to protocol manifest

### High Priority (This Sprint)
- [ ] Remove 250 lines from plan_validator.py
- [ ] Remove 150 lines from llm_judge.py
- [ ] Remove or replace file_lock.py
- [ ] Remove dual output formats (.json files)

### Medium Priority (Next Sprint)
- [ ] Remove test scoping feature
- [ ] Remove baseline_sha tracking
- [ ] Flatten configuration structure
- [ ] Standardize error messages

### Low Priority (Backlog)
- [ ] Update all documentation
- [ ] Add "Simple Architecture" doc
- [ ] Create migration guide for removed features

---

## Conclusion

This is **good code** with **wrong complexity**. The core protocol is sound:
- File-based state
- Clear phase boundaries
- Quality gates
- Git integration

But it's been **over-engineered** into a framework:
- Schema validators
- Budget tracking
- Platform abstractions
- Configuration layers

**The fix:** Aggressive simplification. Remove 33% of code. Return to protocol essence.

**Timeline:** 3 weeks of focused refactoring

**Result:** A protocol so simple you can understand it in 30 minutes and fork it in 1 day.

---

**Sign-off:** This audit recommends **major simplification** before wider adoption. Current state creates maintenance burden and philosophical inconsistency with stated goals.

