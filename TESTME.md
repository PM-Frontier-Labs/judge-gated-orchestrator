# Gated Phase Protocol - Testing Guide

**For:** Evaluators, contributors, QA engineers  
**Purpose:** Validate protocol implementation  
**Time:** 25-30 minutes for full validation

**Coverage:**
- Tests 1-9: Core protocol functionality
- Tests 10-11: Phase 1 enhancements (baseline SHA, globstar patterns)
- Test 12: Phase 2.5 enhancements (test scoping, quarantine)

---

## Prerequisites

### Required Setup

```bash
python3 --version                  # Verify Python 3.8+
git --version                      # Verify Git

# Clone and install
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt

# Verify
python3 -c "import yaml; print('✓ pyyaml')"
pytest --version
```

### Optional (Test 5: LLM Review)

```bash
export ANTHROPIC_API_KEY="sk-ant-..."    # Set API key
python3 -c "from anthropic import Anthropic; print('✓ anthropic')"  # Verify
```

---

## Test 1: Basic Pass Flow

**Goal:** Verify phase approval and advancement

```bash
./orient.sh                                    # Check current state
ls .repo/critiques/                            # Verify P01 passed
cat .repo/briefs/P02-impl-feature.md          # Check requirements
ls src/mvp/feature.py tests/mvp/test_feature.py # Verify files exist
./tools/phasectl.py review P02-impl-feature    # Run review
ls .repo/critiques/P02-impl-feature.*          # Check verdict
```

**Expected:** 
- ✅ orient.sh shows P02 as current
- ✅ P01-scaffold.OK exists
- ✅ Review produces .OK (approved) or .md (critique)

**Success:** Judge provides clear, actionable feedback

---

## Test 2: Intentional Failure Flow

**Goal:** Verify judge catches failures and provides critique

```bash
git checkout -b test-failure-flow
echo "def test_broken(): assert False" >> tests/mvp/test_feature.py
./tools/phasectl.py review P02-impl-feature    # Should fail
cat .repo/critiques/P02-impl-feature.md       # Check critique
cat .repo/traces/last_test.txt                # Check test output
git checkout tests/mvp/test_feature.py         # Fix
./tools/phasectl.py review P02-impl-feature    # Should pass
git checkout main && git branch -D test-failure-flow
```

**Expected:**
- ❌ Judge detects test failure
- 📝 Critique created with actionable feedback
- 📊 Trace shows detailed test output
- ✅ After fix, re-review passes

---

## Test 3: Drift Detection

**Goal:** Verify scope enforcement catches out-of-scope changes

**Steps:**

```bash
# 1. Create test branch
git checkout -b test-drift-detection

# 2. Check P02 scope
grep -A5 "scope:" .repo/plan.yaml | grep -A3 "P02"
# Expected: Shows include patterns (src/mvp/feature.py, tests/mvp/test_feature.py)

# 3. Make out-of-scope change
echo "# Out of scope change" >> README.md

# 4. Submit for review
./tools/phasectl.py review P02-impl-feature

# Expected output:
#   📊 Change Summary:
#
#   ❌ Out of scope (1 files):
#     - README.md
#
#   ⚠️  Drift limit: 0 files allowed, 1 found
#
#   💡 Fix options:
#      1. Revert: git checkout HEAD README.md
#      2. Update scope in .repo/briefs/P02-impl-feature.md
#      3. Split into separate phase
#
#   ⚖️  Invoking judge...
#   ❌ Phase P02-impl-feature needs revision:

# 5. Check critique
cat .repo/critiques/P02-impl-feature.md
# Expected: Contains "Out-of-scope changes detected"

# 6. Fix by reverting
git checkout HEAD README.md

# 7. Re-review
./tools/phasectl.py review P02-impl-feature
# Expected: No drift warnings

# 8. Clean up
git checkout main
git branch -D test-drift-detection
```

**Success criteria:**
- ✅ Diff summary shows out-of-scope files BEFORE judge runs
- ✅ Judge blocks approval due to drift
- ✅ Critique suggests fix options
- ✅ After revert, review passes

---

## Test 4: Forbidden Files

**Goal:** Verify forbidden file changes are blocked

**Steps:**

```bash
# 1. Create test branch
git checkout -b test-forbidden-files

# 2. Check forbidden patterns
grep -A5 "drift_rules:" .repo/plan.yaml
# Expected: Shows forbid_changes: ["requirements.txt", "pyproject.toml", ...]

# 3. Change forbidden file
echo "# Test change" >> requirements.txt

# 4. Submit for review
./tools/phasectl.py review P02-impl-feature

# Expected output:
#   📊 Change Summary:
#   ❌ Out of scope (1 files):
#     - requirements.txt
#
#   ⚖️  Invoking judge...
#   ❌ Phase needs revision:
#
#   # Critique: P02-impl-feature
#   ## Issues Found
#   - Forbidden files changed (these require a separate phase):
#     - requirements.txt
#   - Fix: git checkout HEAD requirements.txt

# 5. Verify critique
cat .repo/critiques/P02-impl-feature.md | grep -i forbidden
# Expected: Shows "Forbidden files changed"

# 6. Revert
git checkout HEAD requirements.txt

# 7. Clean up
git checkout main
git branch -D test-forbidden-files
```

**Success criteria:**
- ✅ Judge identifies forbidden file changes
- ✅ Critique explains these need separate phase
- ✅ Specific fix command provided

---

## Test 5: LLM Review (Optional)

**Goal:** Verify optional LLM code review gate

**Prerequisites:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
pip install anthropic
```

**Steps:**

```bash
# 1. Check if P02 has LLM review enabled
grep -A10 "P02-impl-feature" .repo/plan.yaml | grep llm_review
# Expected: llm_review: { enabled: true }

# 2. Make a code change
git checkout -b test-llm-review
echo "def bad_function(): return 1/0  # Division by zero" >> src/mvp/feature.py

# 3. Submit for review
./tools/phasectl.py review P02-impl-feature

# Expected output:
#   🧪 Running tests...
#   ⚖️  Invoking judge...
#   🤖 Running LLM code review...
#   [May show LLM feedback about division by zero]
#   ❌ Phase needs revision OR ✅ approved
#   (depends on if LLM catches the issue)

# 4. If no API key set, different error
# Unset key to test
ANTHROPIC_API_KEY="" ./tools/phasectl.py review P02-impl-feature
# Expected: "LLM review enabled but ANTHROPIC_API_KEY not set"

# 5. Clean up
git checkout main
git branch -D test-llm-review
```

**Success criteria:**
- ✅ LLM review runs when enabled and key present
- ✅ Clear error when key missing
- ✅ LLM feedback is actionable (if issues found)

---

## Test 6: Phase Advancement

**Goal:** Verify phase transitions work correctly

**Steps:**

```bash
# 1. Ensure P02 is approved
# (If not, fix any issues and get it approved first)

# 2. Check current phase
cat .repo/briefs/CURRENT.json | grep phase_id
# Expected: "phase_id": "P02-impl-feature"

# 3. Try to advance without approval
rm -f .repo/critiques/P02-impl-feature.OK
./tools/phasectl.py next
# Expected: ❌ Error: Phase P02-impl-feature not yet approved

# 4. Approve phase (simulate)
./tools/phasectl.py review P02-impl-feature
# (Assuming it passes)

# 5. Advance to next phase
./tools/phasectl.py next
# Expected:
#   ➡️  Advanced to phase P03-...
#   OR
#   🎉 All phases complete!
#   (depends on plan.yaml phase count)

# 6. Verify CURRENT.json updated
cat .repo/briefs/CURRENT.json
# Expected: phase_id changed to next phase (or stayed at P02 if last)

# 7. Reset to original state
git checkout .repo/briefs/CURRENT.json .repo/critiques/
```

**Success criteria:**
- ✅ Cannot advance without approval
- ✅ Advance succeeds when approved
- ✅ CURRENT.json updates correctly
- ✅ Shows "All phases complete" if at end

---

## Test 7: Context Recovery

**Goal:** Verify orient.sh provides complete status

**Steps:**

```bash
# 1. Run orient
./orient.sh

# Expected output structure:
# 🎯 Current Phase: <phase-id> (X/Y)
#
# 📊 Progress:
# ✅ P01-scaffold (approved)
# [status] P02-impl-feature (...)
#
# 📄 Current Brief:
# .repo/briefs/<phase-id>.md
#
# 🔍 Status:
# [Approval status or critique location]
#
# ⏭️  Next Steps:
# [Actionable next steps]

# 2. Verify completeness
./orient.sh | grep -q "Current Phase" && echo "✓ Shows current phase"
./orient.sh | grep -q "Progress" && echo "✓ Shows progress"
./orient.sh | grep -q "Next Steps" && echo "✓ Shows next steps"
```

**Success criteria:**
- ✅ Shows current phase ID
- ✅ Shows progress (X/Y phases)
- ✅ Shows status (approved/critique/in-progress)
- ✅ Shows actionable next steps
- ✅ Runs in < 10 seconds

---

## Test 8: Error Handling

**Goal:** Verify graceful error handling

**Steps:**

```bash
# Test 8a: Missing plan.yaml
mv .repo/plan.yaml .repo/plan.yaml.backup
./tools/phasectl.py review P02-impl-feature
# Expected: ❌ Error: .repo/plan.yaml not found
mv .repo/plan.yaml.backup .repo/plan.yaml

# Test 8b: Invalid YAML
echo "invalid: yaml: syntax:" >> .repo/plan.yaml
./tools/phasectl.py review P02-impl-feature
# Expected: ❌ Error: Invalid YAML in .repo/plan.yaml
git checkout .repo/plan.yaml

# Test 8c: Missing brief
./tools/phasectl.py review P99-nonexistent
# Expected: ❌ Error: Phase P99-nonexistent not found in plan

# Test 8d: Missing test runner (if pytest not installed)
# (Skip if pytest is installed)
# Expected: ❌ Error: pytest not installed

# Test 8e: Malformed CURRENT.json
echo "{invalid json" > .repo/briefs/CURRENT.json
./orient.sh
# Expected: Error about invalid JSON
git checkout .repo/briefs/CURRENT.json
```

**Success criteria:**
- ✅ All error messages are clear and actionable
- ✅ No Python stack traces for expected errors
- ✅ Exit codes are appropriate (1 for errors, 0 for success)

---

## Test 9: Protocol Integrity Protection

**Goal:** Verify protocol tamper detection prevents agent self-modification

**Steps:**

```bash
# Test 9a: Judge Tamper Detection
git checkout -b test-protocol-integrity

# 1. Check current judge hash
grep "tools/judge.py" .repo/protocol_manifest.json
# Expected: Shows SHA256 hash like "26c244..."

# 2. Tamper with judge (add innocent comment)
echo "# Test comment" >> tools/judge.py

# 3. Submit for review
./tools/phasectl.py review P02-impl-feature

# Expected output:
#   🔐 Checking protocol integrity...
#   ❌ Phase P02-impl-feature needs revision:
#
#   # Critique: P02-impl-feature
#   ## Issues Found
#   - 🚨 JUDGE TAMPER DETECTED: tools/judge.py
#      Expected: 26c2444577b19139d794adbf2d0a92ee102a746a056ce6af0105bfcb4cf0d82b
#      Actual:   [different hash]
#      The judge has been modified. This is a critical protocol violation.

# 4. Verify critique
cat .repo/critiques/P02-impl-feature.md | grep "JUDGE TAMPER"
# Expected: Shows tamper detection message

# 5. Revert tampering
git checkout tools/judge.py

# 6. Re-review
./tools/phasectl.py review P02-impl-feature
# Expected: No protocol integrity errors

# Test 9b: Plan Change Mid-Phase Detection
# 1. Check current CURRENT.json
cat .repo/briefs/CURRENT.json | grep plan_sha
# Expected: Shows plan_sha if phase binding enabled

# 2. Modify plan.yaml (change description)
sed -i.bak 's/P02-impl-feature/P02-impl-feature-modified/' .repo/plan.yaml

# 3. Submit for review
./tools/phasectl.py review P02-impl-feature

# Expected output (if phase binding active):
#   🔐 Checking protocol integrity...
#   ❌ Phase needs revision:
#   - Plan changed mid-phase: .repo/plan.yaml
#      Expected: [original hash]
#      Actual:   [new hash]

# 4. Restore plan
mv .repo/plan.yaml.bak .repo/plan.yaml

# Test 9c: Protocol Maintenance Phase
# 1. Verify protocol maintenance phases are allowed
grep -A5 "protocol_lock:" .repo/plan.yaml
# Expected: Shows allow_in_phases: ["P00-protocol-maintenance"]

# 2. Clean up
git checkout main
git branch -D test-protocol-integrity
```

**Success criteria:**
- ✅ Judge self-check detects tampering immediately
- ✅ Clear error messages with expected vs actual hashes
- ✅ Phase binding detects mid-phase plan changes
- ✅ Protocol files cannot be modified in normal phases
- ✅ After revert, system returns to normal operation

---

## Test 10: Baseline SHA Stability

**Goal:** Verify baseline SHA provides consistent diffs throughout phase lifecycle

**Background:** Phase 1 fix - prevents false drift positives as base branch advances.

**Steps:**

```bash
# 1. Create test branch
git checkout -b test-baseline-stability

# 2. Check current CURRENT.json for baseline_sha
cat .repo/briefs/CURRENT.json | grep baseline_sha
# Expected: "baseline_sha": "abc123..." (captured at phase start)

# 3. Record the baseline
BASELINE=$(cat .repo/briefs/CURRENT.json | python3 -c "import sys, json; print(json.load(sys.stdin).get('baseline_sha', 'none'))")
echo "Baseline SHA: $BASELINE"

# 4. Make a change in scope
echo "# Test change" >> src/mvp/feature.py

# 5. Run review - should show the change
./tools/phasectl.py review P02-impl-feature | grep "Change Summary"
# Expected: Shows src/mvp/feature.py as in-scope

# 6. Verify baseline hasn't changed
BASELINE_AFTER=$(cat .repo/briefs/CURRENT.json | python3 -c "import sys, json; print(json.load(sys.stdin).get('baseline_sha', 'none'))")
test "$BASELINE" = "$BASELINE_AFTER" && echo "✓ Baseline SHA stable" || echo "✗ Baseline changed!"

# 7. Simulate main branch advancing (in real scenario, this would cause drift with merge-base)
# With baseline_sha, the diff anchor remains fixed

# 8. Clean up
git checkout src/mvp/feature.py
git checkout main
git branch -D test-baseline-stability
```

**Success criteria:**
- ✅ CURRENT.json contains baseline_sha field
- ✅ Baseline SHA captured at phase start (git rev-parse HEAD)
- ✅ Baseline remains stable throughout phase (doesn't change with new commits)
- ✅ All gates (drift, docs, LLM) use same baseline
- ✅ Diffs are consistent even as base branch advances

**Why this matters:** Without baseline SHA, diffs use merge-base with main. As main advances during overnight work, earlier commits appear as "out-of-scope" causing false drift positives.

---

## Test 11: Scope Pattern Matching

**Goal:** Verify proper globstar (`**`) support for nested directory matching

**Background:** Phase 1 fix - replaced fnmatch with pathspec for accurate pattern matching.

**Steps:**

```bash
# Run the dedicated scope matching tests
pytest tests/test_scope_matching.py -v

# Expected output:
# test_globstar_recursive_matching PASSED
# test_single_star_vs_double_star PASSED
# test_exclude_patterns PASSED
# test_multiple_include_patterns PASSED
# test_forbidden_files PASSED
# test_forbidden_with_wildcards PASSED
# test_edge_case_empty_patterns PASSED
# test_edge_case_no_files PASSED
# test_gitignore_style_patterns PASSED
```

**What these tests verify:**

1. **Globstar recursion**: `src/**/*.py` matches `src/foo/bar/deep/nested.py`
2. **Single vs double star**: `src/*.py` vs `src/**/*.py` behavior
3. **Exclude overrides**: `**/test_*.py` properly excludes test files
4. **Multiple patterns**: Multiple include patterns work together
5. **Forbidden files**: Forbidden pattern detection (e.g., `.env*`)
6. **Edge cases**: Empty patterns, no files, nested exclusions

**Success criteria:**
- ✅ All 9 scope tests pass
- ✅ Globstar `**` matches nested paths correctly
- ✅ Pattern matching uses pathspec library (.gitignore-style)
- ✅ Graceful fallback to fnmatch if pathspec unavailable

**Why this matters:** Without pathspec, `fnmatch` fails on patterns like `src/**/*.py` for nested directories, causing false drift classification.

---

## Test 12: Test Scoping and Quarantine

**Goal:** Verify test scoping filters tests correctly and quarantine skips specific tests

**Background:** Phase 2.5 feature - handles large codebases with irrelevant/flaky tests.

**Steps:**

```bash
# Test 12a: Test Scoping
# 1. Create test branch
git checkout -b test-scoping

# 2. Check if P02 has test_scope configured
grep -A10 "P02-impl-feature" .repo/plan.yaml | grep test_scope
# Expected: test_scope: "scope"

# 3. Run review and check test command
./tools/phasectl.py review P02-impl-feature 2>&1 | grep "Test scope"
# Expected: Shows "📍 Test scope: Running tests matching phase scope"

# 4. Verify only scoped tests run
# (In P02, scope includes tests/mvp/**, so only MVP tests should run)

# Test 12b: Quarantine List
# 1. Add a quarantine entry to plan.yaml
cat >> .repo/plan.yaml << 'EOF'
        quarantine:
          - path: "tests/mvp/test_golden.py::test_hello_world"
            reason: "Test quarantine validation"
EOF

# 2. Run review
./tools/phasectl.py review P02-impl-feature 2>&1 | grep -A5 "Quarantined tests"
# Expected output:
#   ⚠️  Quarantined tests (1 test will be skipped):
#      - tests/mvp/test_golden.py::test_hello_world
#        Reason: Test quarantine validation

# 3. Verify quarantined test was skipped
# (Check last_test.txt to confirm test didn't run)
grep -q "test_hello_world" .repo/traces/last_test.txt && echo "Test ran (unexpected)" || echo "✓ Test skipped"

# 4. Restore plan.yaml
git checkout .repo/plan.yaml

# Test 12c: Run documentation tests
pytest tests/test_test_scoping.py -v
# Expected: All 7 tests pass

# 5. Clean up
git checkout main
git branch -D test-scoping
```

**What these features solve:**
1. **Test scoping**: Work incrementally on large codebases without running 1000 unrelated tests
2. **Quarantine**: Handle flaky external APIs, legacy tests, deliberately broken tests

**Success criteria:**
- ✅ test_scope: "scope" filters tests to matching scope patterns
- ✅ Quarantine list skips specific tests with documented reasons
- ✅ Clear output showing which tests are scoped/quarantined
- ✅ All test_test_scoping.py tests pass

**Why this matters:** Real-world codebases have legacy/flaky tests that would block autonomous work. Test scoping (primary) + quarantine (escape hatch) enables incremental progress.

---

## Full System Test

**Goal:** Complete workflow from scratch

**Time:** 5 minutes

**Steps:**

```bash
# 1. Reset to clean state
git checkout main
git clean -fd
rm -rf .repo/critiques/*.md .repo/critiques/*.OK
rm -rf .repo/traces/*

# 2. Start from P01
echo '{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": '$(date +%s)'
}' > .repo/briefs/CURRENT.json

# 3. Orient
./orient.sh
# Expected: Shows P01-scaffold as current

# 4. Verify P01 files exist (already in repo)
ls src/mvp/__init__.py tests/mvp/test_golden.py docs/mvp.md
# Expected: All exist

# 5. Review P01
./tools/phasectl.py review P01-scaffold
# Expected: ✅ Approved (or shows issues to fix)

# 6. Advance to P02
./tools/phasectl.py next
# Expected: ➡️ Advanced to P02-impl-feature

# 7. Orient again
./orient.sh
# Expected: Shows P02-impl-feature as current, P01 as approved

# 8. Review P02
./tools/phasectl.py review P02-impl-feature
# Expected: ✅ Approved or ❌ shows issues

# 9. If all phases complete
./tools/phasectl.py next
# Expected: 🎉 All phases complete! (or advances to P03 if exists)
```

**Success criteria:**
- ✅ Complete flow works without manual intervention
- ✅ Each phase gates correctly
- ✅ Can advance through all phases
- ✅ Orient always shows correct state

---

## Troubleshooting

### P02 fails with out-of-scope changes

**Problem:** README.md, tools/judge.py, or other files show as out-of-scope

**Cause:** Previous development changes not reverted

**Fix:**
```bash
git status
git checkout HEAD <out-of-scope-files>
./tools/phasectl.py review P02-impl-feature
```

### Tests fail on fresh clone

**Problem:** `pytest` shows failures

**Cause:** Missing dependencies or environment issue

**Fix:**
```bash
pip install -r requirements.txt
python3 -m pytest tests/ -v
# Debug specific failures
```

### LLM review not working

**Problem:** "ANTHROPIC_API_KEY not set"

**Fix:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
# OR disable in plan.yaml:
# llm_review: { enabled: false }
```

### orient.sh shows wrong phase

**Problem:** CURRENT.json out of sync

**Fix:**
```bash
cat .repo/briefs/CURRENT.json
# Manually verify phase_id matches plan.yaml
# Reset if needed
```

### Judge produces no output

**Problem:** No .OK or .md file created

**Cause:** Exception in judge.py

**Fix:**
```bash
python3 tools/judge.py P02-impl-feature
# Check for Python errors
```

---

## Validation Checklist

### Core Functionality
- [ ] Orient shows complete status in < 10 seconds
- [ ] Review runs tests and invokes judge
- [ ] Judge enforces all enabled gates
- [ ] Critiques are actionable and specific
- [ ] Approval markers created when gates pass
- [ ] Next command advances phases correctly

### Quality Gates
- [ ] Protocol integrity detects tampering
- [ ] Phase binding catches mid-phase changes
- [ ] Baseline SHA provides stable diffs
- [ ] Tests gate catches failures
- [ ] Test scoping filters tests (Phase 2.5)
- [ ] Test quarantine skips tests (Phase 2.5)
- [ ] Docs gate verifies actual changes
- [ ] Drift gate catches out-of-scope changes
- [ ] Drift gate respects globstar patterns (Phase 1)
- [ ] Forbidden files are blocked
- [ ] LLM review works when enabled (optional)

### Error Handling
- [ ] Missing files → clear errors
- [ ] Invalid YAML → clear errors
- [ ] Missing dependencies → clear errors
- [ ] All errors include fix suggestions

### Context Recovery
- [ ] All state in files (no hidden state)
- [ ] Orient recovers full context
- [ ] Can resume after context exhaustion
- [ ] CURRENT.json always accurate

### Documentation
- [ ] README.md clear for evaluators
- [ ] PROTOCOL.md complete for AI execution
- [ ] TESTME.md validates system
- [ ] All docs accurate and up-to-date

---

## Success Criteria

**Protocol is valid when:**

| Requirement | Status |
|-------------|--------|
| All 12 tests pass | \u2705 |
| Full system test completes | \u2705 |
| Validation checklist 100% | \u2705 |
| Error handling graceful | \u2705 |
| Context recovery works | \u2705 |
| Protocol integrity enforced | \u2705 |
| Baseline SHA stable (Test 10) | \u2705 |
| Globstar patterns work (Test 11) | \u2705 |
| Test scoping works (Test 12) | \u2705 |

**When complete, you can:**
- \u2705 Use for real projects
- \u2705 Extend for your needs
- \u2705 Trust gates enforce quality
- \u2705 Run autonomous multi-phase work

---

## Next Steps After Validation

**If all tests pass:**
1. Read README.md to understand use cases
2. Read PROTOCOL.md to understand execution
3. Create your own plan.yaml for a real project
4. Write phase briefs for your roadmap
5. Run your first autonomous phase

**If tests fail:**
1. Check Troubleshooting section above
2. Verify prerequisites installed
3. Open an issue: https://github.com/PM-Frontier-Labs/judge-gated-orchestrator/issues
4. Include error output and environment details

---

## Feedback

Found issues with this testing guide? Suggestions for additional tests?

Open an issue or PR: https://github.com/PM-Frontier-Labs/judge-gated-orchestrator

---

**Time to complete:** 25-30 minutes for full validation (includes Phase 1 + Phase 2.5 tests)

**Difficulty:** Beginner (just follow steps)

**Result:** Confidence the protocol works as documented, including Phase 1 + Phase 2.5 enhancements
