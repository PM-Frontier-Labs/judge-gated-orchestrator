# Gated Phase Protocol - Testing Guide

**Audience:** Evaluators, contributors, QA engineers

**Purpose:** Validate the protocol implementation works correctly

**Time:** 15-20 minutes for full validation

---

## Prerequisites

### Required

```bash
# Python 3.8+
python3 --version

# Git
git --version

# Clone repo
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator

# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "import yaml; print('✓ pyyaml installed')"
pytest --version
```

### Optional (for LLM review test)

```bash
# Anthropic API key
export ANTHROPIC_API_KEY="sk-ant-..."

# Verify
python3 -c "from anthropic import Anthropic; print('✓ anthropic package installed')"
```

---

## Test 1: Basic Pass Flow

**Goal:** Verify a phase can pass all gates and advance

**Steps:**

```bash
# 1. Check current state
./orient.sh
# Expected: Shows P02-impl-feature as current phase
# (P01 already completed in repo)

# 2. Verify P01 passed
ls .repo/critiques/
# Expected: P01-scaffold.OK exists

# 3. Check what P02 requires
cat .repo/briefs/P02-impl-feature.md
# Expected: Shows scope, artifacts, gates

# 4. Verify required files exist
ls src/mvp/feature.py tests/mvp/test_feature.py
# Expected: Both files exist (already implemented)

# 5. Run review
./tools/phasectl.py review P02-impl-feature
# Expected output:
#   📊 Change Summary: (may show changes)
#   🧪 Running tests...
#   ⚖️  Invoking judge...
#   Either: ✅ Phase approved OR ❌ Phase needs revision

# 6. Check critique
ls .repo/critiques/P02-impl-feature.*
# If .OK exists → test passed
# If .md exists → see "Troubleshooting" below
```

**Success criteria:**
- ✅ orient.sh runs without errors
- ✅ Tests run and show results
- ✅ Judge produces either .OK or .md file
- ✅ Feedback is actionable

**Note:** P02 may fail due to out-of-scope changes from previous work. That's expected - see Test 3.

---

## Test 2: Intentional Failure Flow

**Goal:** Verify judge catches issues and provides critique

**Steps:**

```bash
# 1. Create a branch for testing
git checkout -b test-failure-flow

# 2. Break the tests
echo "def test_broken(): assert False" >> tests/mvp/test_feature.py

# 3. Submit for review
./tools/phasectl.py review P02-impl-feature

# Expected output:
#   📊 Change Summary: tests/mvp/test_feature.py in scope
#   🧪 Running tests...
#   ⚖️  Invoking judge...
#   ❌ Phase P02-impl-feature needs revision:
#
#   # Critique: P02-impl-feature
#   ## Issues Found
#   - Tests failed with exit code 1. See .repo/traces/last_test.txt

# 4. Verify critique exists
cat .repo/critiques/P02-impl-feature.md
# Expected: Shows "Tests failed" issue

# 5. Check test trace
cat .repo/traces/last_test.txt
# Expected: Shows pytest output with FAILED test_broken

# 6. Fix the issue
git checkout tests/mvp/test_feature.py

# 7. Re-review
./tools/phasectl.py review P02-impl-feature
# Expected: ✅ Phase approved (assuming no other issues)

# 8. Clean up
git checkout main
git branch -D test-failure-flow
```

**Success criteria:**
- ✅ Judge detected test failure
- ✅ Critique file created with actionable feedback
- ✅ Trace file shows detailed test output
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

Use this to verify the system is production-ready:

**Core Functionality:**
- [ ] Orient shows complete status in < 10 seconds
- [ ] Review command runs tests and invokes judge
- [ ] Judge enforces all enabled gates
- [ ] Critiques are actionable and specific
- [ ] Approval markers created when all gates pass
- [ ] Next command advances phases correctly

**Quality Gates:**
- [ ] Protocol integrity detects judge tampering
- [ ] Phase binding catches mid-phase plan changes
- [ ] Tests gate catches test failures
- [ ] Docs gate catches missing documentation
- [ ] Drift gate catches out-of-scope changes
- [ ] Drift gate respects include/exclude patterns
- [ ] Forbidden files are blocked
- [ ] LLM review works when enabled (optional)

**Error Handling:**
- [ ] Missing files produce clear errors
- [ ] Invalid YAML produces clear errors
- [ ] Missing dependencies produce clear errors
- [ ] All errors include fix suggestions

**Context Recovery:**
- [ ] All state stored in files (no hidden state)
- [ ] Orient recovers full context from files
- [ ] Can resume work after context window exhaustion
- [ ] CURRENT.json always accurate

**Documentation:**
- [ ] README.md clear for humans evaluating
- [ ] PROTOCOL.md complete for LLM execution
- [ ] TESTME.md (this file) validates system
- [ ] All docs accurate and up-to-date

---

## Success Criteria

**The protocol implementation is valid if:**

1. ✅ All 9 tests pass without modification
2. ✅ Full system test completes successfully
3. ✅ Validation checklist 100% checked
4. ✅ Error handling graceful for all error conditions
5. ✅ Context recovery works from any state
6. ✅ Protocol integrity prevents agent self-modification

**When complete, you can confidently:**
- Use the protocol for real projects
- Extend it for your needs
- Trust the gates enforce quality
- Run autonomous multi-phase work

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

**Time to complete:** 15-20 minutes for full validation

**Difficulty:** Beginner (just follow steps)

**Result:** Confidence the protocol works as documented
