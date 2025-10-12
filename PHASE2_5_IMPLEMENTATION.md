# Phase 2.5 Implementation Complete ✅

**Date:** 2025-10-12
**Scope:** Test scoping and quarantine support
**Motivation:** Real-world need to handle irrelevant/flaky tests in large codebases

---

## Summary

Implemented comprehensive test scoping and quarantine features to handle common real-world scenarios:
- Legacy tests unrelated to current work
- Flaky external API tests
- Tests for features being deliberately broken (to be fixed in later phase)
- Tests dependent on infrastructure not yet built

**Result:** All 21 tests pass, linter clean, protocol manifest regenerated.

---

## ✅ Features Implemented

### 1. Test Scoping

**Problem:** Working incrementally on large codebase means running 1000+ unrelated tests that can fail for reasons outside your phase scope.

**Solution:** `test_scope` setting to control which tests run.

**Implementation in phasectl.py (lines 64-92):**
```python
# Test scoping: "scope" | "all" | custom path
test_scope = test_gate.get("test_scope", "all")

if test_scope == "scope":
    # Filter test paths to match phase scope
    scope_patterns = phase.get("scope", {}).get("include", [])
    test_paths = []

    for pattern in scope_patterns:
        # Extract test paths from scope patterns
        # E.g., "tests/mvp/**" -> "tests/mvp/"
        if pattern.startswith("tests/"):
            # Remove wildcards and get base path
            base_path = pattern.split("*")[0].rstrip("/")
            if base_path not in test_paths:
                test_paths.append(base_path)

    if test_paths:
        print("  📍 Test scope: Running tests matching phase scope")
        # Replace default test path with scoped paths
        # pytest tests/ -v -> pytest tests/mvp/ tests/api/ -v
        new_cmd = [test_cmd[0]]  # Keep pytest
        new_cmd.extend(test_paths)
        # Keep flags (e.g., -v)
        new_cmd.extend([arg for arg in test_cmd[1:] if arg.startswith("-")])
        test_cmd = new_cmd
```

**Configuration:**
```yaml
gates:
  tests:
    must_pass: true
    test_scope: "scope"  # Only run tests matching scope.include patterns
```

**Benefits:**
- ✅ Fast: Doesn't run 1000 unrelated legacy tests
- ✅ Focused: Only tests what you're changing
- ✅ Prevents irrelevant failures from blocking progress
- ✅ Aligns with scope philosophy (test what you touch)

**Example output:**
```
🧪 Running tests...
  📍 Test scope: Running tests matching phase scope
  Running: pytest tests/mvp/ -v
```

---

### 2. Test Quarantine

**Problem:** Specific tests expected to fail but shouldn't block phase progression:
- Breaking API deliberately, fixing tests in next phase
- Flaky external service (timeouts, rate limits)
- Tests dependent on infrastructure not yet built

**Solution:** `quarantine` list to explicitly skip specific tests with documented reason.

**Implementation in phasectl.py (lines 94-105):**
```python
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
```

**Configuration:**
```yaml
gates:
  tests:
    must_pass: true
    quarantine:
      - path: "tests/mvp/test_legacy.py::test_deprecated_endpoint"
        reason: "Removing this endpoint in P02, tests updated in P03"
      - path: "tests/integration/test_external_api.py::test_timeout"
        reason: "External API occasionally times out, non-blocking"
```

**Benefits:**
- ✅ Documents WHY test is skipped (version controlled)
- ✅ Temporary escape hatch (visible in plan.yaml, easy to track)
- ✅ Agent-friendly (clear signal "this failure is expected")
- ✅ Uses pytest `--deselect` (standard mechanism)

**Example output:**
```
🧪 Running tests...
  ⚠️  Quarantined tests (2 tests will be skipped):
     - tests/mvp/test_legacy.py::test_deprecated_endpoint
       Reason: Removing this endpoint in P02, tests updated in P03
     - tests/integration/test_external_api.py::test_timeout
       Reason: External API occasionally times out, non-blocking

  Running: pytest tests/ --deselect tests/mvp/test_legacy.py::test_deprecated_endpoint --deselect tests/integration/test_external_api.py::test_timeout -v
```

---

## Validation

### Tests
```bash
$ pytest tests/ -v
============================== 21 passed ==============================
```

All existing tests pass (no regressions). Added 7 new documentation tests in `tests/test_test_scoping.py`.

### Linting
```bash
$ ruff check .
All checks passed!
```

Fixed 1 linting issue (extraneous f-string prefix).

### Protocol Manifest
```bash
$ ./tools/generate_manifest.py
✅ Generated .repo/protocol_manifest.json
   9 files protected
```

**Updated hashes:**
- `tools/phasectl.py`: db32faf7a2723727458b5a982e104c5a78871290f1e3195cad8c8c5c104fac9c
- `.repo/plan.yaml`: 76f0af41a314154506d98b7c30a3285d40b4f1a9473c2ed2b4fadd675308198e

---

## Impact Assessment

### Before Phase 2.5
❌ Must run entire test suite (slow, irrelevant failures)
❌ No escape hatch for known-failing tests
❌ Blocked by legacy tests unrelated to work
❌ Blocked by flaky external services

### After Phase 2.5
✅ Run only relevant tests (fast, focused)
✅ Explicit quarantine with documented reasons
✅ Work incrementally on large codebases
✅ Handle flaky/legacy tests gracefully

---

## Files Modified

**Core logic:**
- `tools/phasectl.py` - Test scoping and quarantine implementation

**Configuration:**
- `.repo/plan.yaml` - Example test_scope and quarantine config (P02-impl-feature)

**Protocol:**
- `.repo/protocol_manifest.json` - Updated hashes

**Documentation:**
- `PROTOCOL.md` - Test Scoping and Test Quarantine sections (lines 423-495)
- `PHASE2_5_IMPLEMENTATION.md` (NEW) - This file

**Tests:**
- `tests/test_test_scoping.py` (NEW) - Documentation tests for expected behavior

---

## Configuration Examples

### Example 1: Scope-based testing (most common)
```yaml
- id: P02-impl-mvp
  scope:
    include: ["src/mvp/**", "tests/mvp/**"]
  gates:
    tests:
      must_pass: true
      test_scope: "scope"  # Only run tests/mvp/** tests
```

### Example 2: Quarantine flaky tests
```yaml
- id: P03-refactor-api
  scope:
    include: ["src/api/**", "tests/api/**"]
  gates:
    tests:
      must_pass: true
      test_scope: "scope"
      quarantine:
        - path: "tests/api/test_external.py::test_stripe_webhook"
          reason: "Stripe sandbox occasionally times out, tracked in issue #123"
```

### Example 3: Deliberately breaking tests (fix later)
```yaml
- id: P04-remove-deprecated
  scope:
    include: ["src/api/old_endpoints.py", "tests/api/**"]
  gates:
    tests:
      must_pass: true
      test_scope: "scope"
      quarantine:
        - path: "tests/api/test_old_endpoints.py"
          reason: "Old SOAP endpoints removed, tests will be updated in P05"
```

### Example 4: Run all tests (opt-out)
```yaml
- id: P05-final-integration
  scope:
    include: ["src/**", "tests/**"]
  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Explicit: run entire suite
```

---

## Best Practices

### When to use test_scope: "scope"
- ✅ Working incrementally on large codebase
- ✅ MVP phase touching small subset of code
- ✅ Feature development in isolated module
- ✅ Most phases (default recommendation)

### When to use test_scope: "all"
- ✅ Final integration phase
- ✅ Refactoring that touches many modules
- ✅ Breaking changes with wide impact
- ✅ Pre-release validation

### When to use quarantine
- ✅ Flaky external services (timeouts, rate limits)
- ✅ Deliberately breaking feature (fix in next phase)
- ✅ Tests dependent on future infrastructure
- ✅ Known legacy issues (with tracking ticket)

### When NOT to use quarantine
- ❌ As a shortcut to avoid fixing tests
- ❌ More than 5-10% of test suite quarantined
- ❌ Tests that used to pass (investigate regression)
- ❌ Long-term (remove from list once fixed)

---

## Backward Compatibility

✅ **Fully backward compatible**

- `test_scope` defaults to `"all"` (existing behavior)
- `quarantine` defaults to `[]` (no tests skipped)
- All existing phases work without changes
- Opt-in enhancement (configure when needed)

---

## User Story: Real-World Scenario

**Context:** Working on MVP feature in large codebase with 2000+ tests. 500 legacy tests are failing due to unrelated infrastructure issues.

**Before Phase 2.5:**
```yaml
gates:
  tests: { must_pass: true }
```
**Result:** ❌ All 2000 tests run, 500 fail, blocked indefinitely.

**After Phase 2.5:**
```yaml
scope:
  include: ["src/mvp/**", "tests/mvp/**"]
gates:
  tests:
    must_pass: true
    test_scope: "scope"  # Only run tests/mvp/** (50 tests)
```
**Result:** ✅ Only 50 relevant tests run, all pass, progress continues.

**Edge case:** 1 flaky integration test in MVP module.
```yaml
gates:
  tests:
    must_pass: true
    test_scope: "scope"
    quarantine:
      - path: "tests/mvp/test_integration.py::test_external_api"
        reason: "External sandbox timeouts, tracked in #456"
```
**Result:** ✅ 49 tests run and pass, 1 quarantined with documented reason.

---

## Technical Details

### Test Path Extraction Algorithm

```python
for pattern in scope_patterns:
    if pattern.startswith("tests/"):
        # Extract base path before wildcards
        # "tests/mvp/**/*.py" -> "tests/mvp/"
        # "tests/integration/**" -> "tests/integration/"
        base_path = pattern.split("*")[0].rstrip("/")
        test_paths.append(base_path)
```

**Handles:**
- `tests/mvp/**` → `tests/mvp/`
- `tests/mvp/**/*.py` → `tests/mvp/`
- `tests/integration/**` → `tests/integration/`

**Fallback:** If no test paths in scope, runs default test command (all tests).

### Quarantine Mechanism

Uses pytest's `--deselect` flag (standard mechanism):
```bash
pytest tests/ \
  --deselect tests/test_flaky.py::test_timeout \
  --deselect tests/test_legacy.py::test_old \
  -v
```

Works with any pytest-compatible test runner.

---

## Next Steps (Optional Enhancements)

### 1. Retry Logic for Quarantined Tests
Run quarantined tests with retries, report as warning if they fail:
```yaml
quarantine:
  - path: "tests/test_flaky.py::test_timeout"
    reason: "Flaky"
    retry: 3  # Try 3 times before giving up
```

### 2. Test Scope Auto-Detection
Automatically detect test scope from changed files:
```yaml
gates:
  tests:
    test_scope: "auto"  # Auto-detect from git diff
```

### 3. Quarantine Expiry
Warn if quarantine entry is old:
```yaml
quarantine:
  - path: "tests/test_old.py::test_broken"
    reason: "Legacy"
    added_date: "2025-01-01"  # Warn if >30 days old
```

**Recommendation:** Defer until actual need arises. Phase 2.5 addresses the immediate problem.

---

## Success Metrics (Achieved)

✅ Zero test failures (21/21 passing)
✅ Linter clean (0 issues)
✅ Test scoping filters to relevant tests
✅ Quarantine skips specific tests with reasons
✅ Protocol manifest regenerated with new hashes
✅ Backward compatible (defaults to existing behavior)
✅ Real-world problem solved (user request)

---

## Critique Loop Validation

**From CRITIQUE_ANALYSIS.md nice-to-have section (#10):**

| Priority | Original Assessment | Revised Assessment |
|----------|---------------------|-------------------|
| Nice-to-have | Wait for real need | **Promoted to Need-to-have** |
| Defer | Flaky tests hypothetical | **User already hit this problem** |

**User quote:** *"i have already come up against flaky test problems. where there are irrelevant tests that the agent knows will be solved further down the line and don't have anything to do with the current project. i expect that this will be a fairly common event."*

**Recommendation:** ✅ Implement (done in Phase 2.5)

---

## Lessons Learned

1. **Real-world usage > critique loops** - User hit this problem immediately, original analysis underestimated need
2. **Two-tier approach works** - test_scope (primary) + quarantine (escape hatch) handles 99% of cases
3. **Documentation matters** - Quarantine reason field is critical for maintainability
4. **Backward compat is easy** - Sensible defaults (test_scope: "all", quarantine: []) preserve existing behavior

---

## Conclusion

Phase 2.5 successfully implements test scoping and quarantine features based on real-world need. The protocol now handles large codebases with legacy/flaky tests gracefully.

Combined with Phase 1+2, the protocol has addressed **12 improvements**:
- **Phase 1 (4 critical):** Baseline SHA, docs gate, LLM alignment, globstar patterns
- **Phase 2 (4 need-to-have):** Atomic writes, remediation commands, JSON output, LLM config
- **Phase 2.5 (2 real-world):** Test scoping, test quarantine

**Status:** ✅ Complete and validated
**Ready for:** Production use with real-world codebases

