# Code Audit - Action Plan

## Critical Issues (Fix Immediately) 🔴

### 1. Protocol Manifest Missing Files
**Files:** `tools/generate_manifest.py`

**Issue:** Critical utilities used by judge are not protected by integrity checking.

**Fix:**
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
    "tools/lib/plan_validator.py",  # ADD THIS
    "tools/lib/file_lock.py",       # ADD THIS
]
```

Then run: `./tools/generate_manifest.py`

**Impact:** Security hole allowing protocol modification mid-phase.

---

## High Priority Issues (This Week) 🟡

### 2. Plan Validator is a Framework (301 lines → 50 lines)
**File:** `tools/lib/plan_validator.py`

**Current Problem:** 301 lines of comprehensive schema validation

**Proposed Solution:**
```python
def validate_plan(plan: Dict[str, Any]) -> List[str]:
    """Minimal validation - let system fail naturally with helpful errors."""
    errors = []
    
    # Check structure
    if "plan" not in plan:
        errors.append("Missing 'plan' key")
        return errors
    
    plan_config = plan["plan"]
    
    # Check required fields only
    if "phases" not in plan_config:
        errors.append("Missing 'phases' list")
        return errors
    
    if not isinstance(plan_config["phases"], list):
        errors.append("'phases' must be a list")
        return errors
    
    # Check phase IDs exist
    for i, phase in enumerate(plan_config["phases"]):
        if "id" not in phase:
            errors.append(f"Phase {i} missing 'id'")
    
    return errors
```

**Lines Removed:** ~250 lines

---

### 3. LLM Judge Overengineered (223 lines → 70 lines)
**File:** `tools/llm_judge.py`

**Remove:**
- Budget tracking (lines 180-196)
- File size limits (lines 58-59, 106-122)
- Cost estimation (lines 186-196)
- Exclude patterns logic (lines 86-94)

**Keep:**
- Basic file collection
- Simple API call
- APPROVED/LGTM parsing

**Simplified version:**
```python
def llm_code_review(phase, repo_root, plan, baseline_sha):
    """Simple LLM review without budget/size complexity."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ["LLM review enabled but ANTHROPIC_API_KEY not set"]
    
    # Get changed files
    changed_files = get_changed_files_raw(...)
    
    # Build context (simplified)
    code_context = ""
    for file_str in changed_files[:20]:  # Simple limit
        file_path = repo_root / file_str
        if file_path.exists() and file_path.suffix in [".py", ".js", ".ts"]:
            code_context += f"\n{'='*60}\n"
            code_context += f"# {file_str}\n"
            code_context += f"{'='*60}\n"
            try:
                code_context += file_path.read_text()[:10000]  # Simple size limit
            except:
                continue
    
    if not code_context:
        return []
    
    # Call Claude (simplified)
    client = Anthropic(api_key=api_key)
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": f"Review this code for phase: {phase['description']}\n\n{code_context}"
        }]
    )
    
    review_text = response.content[0].text.strip()
    
    if "APPROVED" in review_text.upper():
        return []
    
    return [f"Code quality issues:\n{review_text}"]
```

**Lines Removed:** ~150 lines

---

### 4. File Locking is Framework Territory (110 lines → 0 or 10 lines)
**File:** `tools/lib/file_lock.py`

**Option A (Recommended): Remove Entirely**

Update `tools/judge.py`:
```python
# Remove file_lock import and usage
# Document: "Don't run concurrent reviews of same phase"

def main():
    if len(sys.argv) < 2:
        print("Usage: judge.py <PHASE_ID>")
        return 1
    
    phase_id = sys.argv[1]
    return judge_phase(phase_id)  # No lock
```

**Option B: Use OS flock**
```python
# In judge.py, replace file_lock with:
import subprocess
lock_file = REPO_ROOT / ".repo/.judge.lock"
result = subprocess.run(
    ["flock", "-w", "60", str(lock_file), sys.executable, __file__, sys.argv[1]],
    cwd=REPO_ROOT
)
sys.exit(result.returncode)
```

**Lines Removed:** 110 lines (Option A)

---

### 5. Dual Output Formats (.md + .json)
**File:** `tools/judge.py`

**Remove:**
- JSON critique writing (lines 294-326)
- JSON approval writing (lines 367-389)
- All .json file operations

**Keep:**
- .md critiques (human-readable)
- .OK approvals (simple markers)

**Simplified:**
```python
def write_critique(phase_id: str, issues: List[str]):
    """Write markdown critique only."""
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
    critique_file.write_text(critique_content)
    
    # Clean up old approval
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    if ok_file.exists():
        ok_file.unlink()


def write_approval(phase_id: str):
    """Write simple approval marker."""
    approval_content = f"Phase {phase_id} approved at {time.time()}\n"
    ok_file = CRITIQUES_DIR / f"{phase_id}.OK"
    ok_file.write_text(approval_content)
    
    # Clean up old critique
    critique_file = CRITIQUES_DIR / f"{phase_id}.md"
    if critique_file.exists():
        critique_file.unlink()
```

**Lines Removed:** ~100 lines (temp file logic, JSON writing)

---

## Medium Priority Issues (Next Week) 🟠

### 6. Test Scoping Feature Creep
**File:** `tools/phasectl.py` lines 64-140

**Remove:**
- Test scope logic (lines 69-128)
- Quarantine handling (lines 129-140)

**Replacement:**
```python
def run_tests(plan, phase=None):
    """Run tests - simple version."""
    print("🧪 Running tests...")
    
    # Get test command from plan
    test_config = plan.get("plan", {}).get("test_command", "pytest tests/ -v")
    if isinstance(test_config, str):
        test_cmd = shlex.split(test_config)
    else:
        test_cmd = ["pytest", "tests/", "-v"]
    
    # Run command and save trace
    exit_code = run_command_with_trace("tests", test_cmd, REPO_ROOT, TRACES_DIR)
    
    if exit_code is None:
        print(f"❌ Error: {test_cmd[0]} not installed")
    
    return exit_code
```

**User Migration:**
```yaml
# Old (with test scoping):
phases:
  - id: P01
    scope:
      include: ["src/mvp/**", "tests/mvp/**"]
    gates:
      tests:
        must_pass: true
        test_scope: "scope"

# New (simple):
phases:
  - id: P01
    test_command: "pytest tests/mvp/ -v"  # Just specify the path directly
    gates:
      tests: { must_pass: true }
```

**Lines Removed:** ~70 lines

---

### 7. Baseline SHA Tracking
**Files:** Multiple

**Remove:**
- baseline_sha parameter from all functions
- baseline_sha storage in CURRENT.json
- Conditional git diff logic

**Replacement:**
```python
def get_changed_files(repo_root: Path, base_branch: str = "main") -> List[str]:
    """Simplified: Always use merge-base."""
    try:
        # Get merge base
        result = subprocess.run(
            ["git", "merge-base", "HEAD", base_branch],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        merge_base = result.stdout.strip()
        
        # Get all changes (committed + uncommitted)
        committed = subprocess.run(
            ["git", "diff", "--name-only", f"{merge_base}...HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.strip().split("\n")
        
        uncommitted = subprocess.run(
            ["git", "diff", "--name-only", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, check=True
        ).stdout.strip().split("\n")
        
        all_changes = list(set(committed + uncommitted))
        return [f for f in all_changes if f]
    
    except subprocess.CalledProcessError:
        return []
```

**Lines Removed:** ~30 lines across multiple files

---

### 8. Flatten Configuration
**File:** `.repo/plan.yaml`

**Current (5 layers):**
```yaml
plan:
  test_command: "pytest tests/ -v"           # Layer 1
  llm_review_config:                         # Layer 2
    model: "claude-sonnet-4"
    max_tokens: 2000
    temperature: 0
    # ... 8 more fields
  
  phases:
    - id: P01
      gates:
        tests:
          must_pass: true
          test_scope: "scope"                # Layer 3
          quarantine: [...]                  # Layer 4
        llm_review:
          enabled: true                      # Layer 5
```

**Proposed (2 layers):**
```yaml
plan:
  id: PROJECT
  base_branch: "main"
  
  phases:
    - id: P01
      description: "Scaffold"
      test_command: "pytest tests/mvp/ -v"  # Inline, not nested
      
      scope:
        include: ["src/mvp/**", "tests/mvp/**"]
      
      artifacts:
        must_exist: ["src/mvp/__init__.py"]
      
      gates:
        tests: true                          # Simple boolean
        docs: ["docs/mvp.md"]               # Simple list
        drift: { max: 0 }                   # Simple dict
        llm_review: false                   # Simple boolean
```

**Impact:** Easier to understand, fewer places to check

---

## Low Priority Issues (Backlog) 🔵

### 9. Inconsistent Error Formatting

**Standardize all errors:**
```python
# Always use this format:
print("❌ Error: {message}")
print("⚠️  Warning: {message}")
print("✅ Success: {message}")

# Never mix with:
return ["Error message"]  # Old style
```

---

### 10. Trace File Path Logic

**File:** `tools/lib/traces.py` line 59

**Current:**
```python
f"See {trace_file.relative_to(trace_file.parent.parent.parent)} for details."
```

**Fix:**
```python
f"See .repo/traces/last_{gate_name}.txt for details."
```

---

### 11. Git Error Context

**File:** `tools/lib/git_ops.py` line 79-81

**Current:**
```python
except subprocess.CalledProcessError:
    return []  # Silent failure
```

**Fix:**
```python
except subprocess.CalledProcessError as e:
    print(f"⚠️  Git operation failed: {e}", file=sys.stderr)
    print(f"   Not a git repo or base branch '{base_branch}' doesn't exist")
    return []
```

---

## Implementation Order

### Sprint 1 (Week 1): Critical + High Priority
1. ✅ Fix protocol manifest (5 min)
2. ✅ Simplify plan validator (2 hours)
3. ✅ Simplify LLM judge (2 hours)
4. ✅ Remove file locking (1 hour)
5. ✅ Remove dual formats (1 hour)

**Deliverable:** 540 lines removed, core complexity reduced

---

### Sprint 2 (Week 2): Medium Priority
6. ✅ Remove test scoping (1 hour)
7. ✅ Remove baseline_sha (2 hours)
8. ✅ Flatten configuration (2 hours)
9. ✅ Update documentation (4 hours)

**Deliverable:** 100 more lines removed, simpler mental model

---

### Sprint 3 (Week 3): Polish + Low Priority
10. ✅ Standardize errors (1 hour)
11. ✅ Fix small issues (2 hours)
12. ✅ Final docs review (2 hours)
13. ✅ Create migration guide (2 hours)

**Deliverable:** Production-ready simplified protocol

---

## Metrics

### Code Reduction
- **Current:** ~2,400 lines
- **After Sprint 1:** ~1,860 lines (-22%)
- **After Sprint 2:** ~1,760 lines (-27%)
- **After Sprint 3:** ~1,600 lines (-33%)

### Complexity Reduction
- **Remove:** Schema validator complexity
- **Remove:** Budget tracking
- **Remove:** Platform abstractions
- **Remove:** Feature creep (test scoping, quarantine)
- **Keep:** Core protocol (phases, gates, git integration)

### Philosophy Alignment
- ✅ "Protocol, not framework" - achieved
- ✅ Simple file conventions - achieved
- ✅ Forkable in 1 day - achieved
- ✅ Understandable in 30 min - achieved

---

## Success Criteria

### Before
- 2,400 lines of code
- 5-layer configuration nesting
- Framework-like abstractions
- Hard to explain in one sentence

### After
- 1,600 lines of code
- 2-layer configuration
- Simple file operations
- **Easy to explain:** "Write plan.yaml, run phasectl review, judge checks gates, iterate until approved"

---

## Migration Path for Users

### Removed Features → Alternatives

| Removed Feature | Alternative |
|----------------|-------------|
| Test scoping (`test_scope: "scope"`) | Specify path in `test_command: "pytest tests/mvp/"` |
| Test quarantine lists | Fix flaky tests OR use pytest marks |
| Budget tracking in LLM | Monitor via Anthropic dashboard |
| File size limits in LLM | Let API handle token limits |
| JSON output formats | Parse .md files if needed |
| Baseline SHA tracking | Use merge-base (works 99% of time) |
| Schema validation details | YAML parser + natural failures |

### Breaking Changes
- ⚠️ Remove `test_scope` field from plan.yaml
- ⚠️ Remove `quarantine` field from plan.yaml
- ⚠️ Remove `.json` and `.OK.json` files
- ⚠️ Remove `llm_review_config` nested fields
- ⚠️ Remove `baseline_sha` from CURRENT.json

### Migration Script
```bash
# Update plan.yaml automatically
python tools/migrate_plan.py .repo/plan.yaml

# Clean up old JSON files
rm .repo/critiques/*.json 2>/dev/null

# Regenerate manifest with new file list
./tools/generate_manifest.py
```

---

## Questions Before Starting

1. **File Locking:** Any reports of concurrent execution issues?
   - If NO → Remove entirely
   - If YES → Document limitation, don't add complexity

2. **JSON Outputs:** Any tooling depends on them?
   - If NO → Remove
   - If YES → Create optional parser tool

3. **Budget Tracking:** Used in production?
   - If NO → Remove
   - If YES → Move to external monitoring

4. **Test Scoping:** How many phases use it?
   - If <25% → Remove, document migration
   - If >50% → Keep simplified version

---

## Communication Plan

### Internal
- [ ] Share audit with team
- [ ] Discuss removed features
- [ ] Agree on timeline
- [ ] Assign issues

### External (if open source)
- [ ] Blog post: "Simplifying the Protocol"
- [ ] Migration guide
- [ ] GitHub issues for breaking changes
- [ ] Version bump: 1.x → 2.0

---

## Rollback Plan

If simplification causes issues:

1. **Tag current version:** `git tag v1.0-complex`
2. **Create feature branch:** `git checkout -b feature/simplify`
3. **Make changes in branch**
4. **Test thoroughly**
5. **Merge when ready**

Users who need old features can stay on v1.0 tag.

---

## Final Checklist

### Before Starting
- [x] Audit complete
- [ ] Team reviewed audit
- [ ] Breaking changes approved
- [ ] Timeline agreed

### After Sprint 1
- [ ] Critical fixes deployed
- [ ] High priority simplifications done
- [ ] Tests passing
- [ ] Basic docs updated

### After Sprint 2
- [ ] Medium priority items done
- [ ] Configuration simplified
- [ ] Migration guide created
- [ ] All docs updated

### After Sprint 3
- [ ] All polish items done
- [ ] Full test coverage
- [ ] Blog post published
- [ ] v2.0 released

