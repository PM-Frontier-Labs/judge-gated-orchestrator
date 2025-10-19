# Gated Phase Protocol - Execution Manual

**Audience:** AI coding assistants (Claude Code, Cursor, Windsurf, etc.) executing phases autonomously

**Purpose:** Precise instructions for working within quality-gated phases

This document is for execution. For planning, collaborate with a human to draft `.repo/plan.yaml` following the examples in `GETTING_STARTED.md`.

---

## Core Loop

```
1. Orient:     ./orient.sh                    # Shows intelligence status
2. Start:      ./tools/phasectl.py start <phase-id>  # Shows mechanism opportunities
3. Implement:  Make changes within scope
4. Review:     ./tools/phasectl.py review <phase-id>
   ├─> Shows intelligence context
   ├─> Auto-applies pending amendments
   ├─> Auto-proposes amendments from patterns
   ├─> Learns from successful amendments
   └─> Writes micro-retrospectives
5. Check:      If .repo/critiques/<phase-id>.OK exists → approved
               If .repo/critiques/<phase-id>.md exists → fix and re-review
6. Advance:    ./tools/phasectl.py next      # Shows intelligence summary
7. Repeat from step 1
```

**All state lives in files.** No memory required. Recover full context anytime via `./orient.sh`.

---

## Quick Command Reference

```bash
# Recover context (run this when lost)
./orient.sh

# Start implementation phase (mandatory brief acknowledgment)
./tools/phasectl.py start <phase-id>

# Reset phase state (for plan transitions)
./tools/phasectl.py reset <phase-id>

# Recover from plan state corruption
./tools/phasectl.py recover

# Check available patterns (required for drift issues)
./tools/phasectl.py patterns list

# Check current phase
cat .repo/briefs/CURRENT.json

# Read current brief
cat .repo/briefs/$(jq -r .phase_id < .repo/briefs/CURRENT.json).md

# Submit for review
./tools/phasectl.py review <phase-id>

# Check if approved
ls .repo/critiques/<phase-id>.OK

# Read critique if failed
cat .repo/critiques/<phase-id>.md

# Advance to next phase (only after approval)
./tools/phasectl.py next

# See test results
cat .repo/traces/last_tests.txt

# Check diff before review
git diff --name-only HEAD
```

**Note:** `tools/phasectl.py` is the only supported CLI. `tools/judge.py` and other tools are internal implementation details.

---

## File Specifications

### `.repo/briefs/CURRENT.json`

Points to the active phase. **Read this first** when recovering context.

**Format:**
```json
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": 1760223767.0468428,
  "baseline_sha": "abc123def456",
  "plan_sha": "789012345678",
  "manifest_sha": "901234567890"
}
```

**Fields:**
- `phase_id` - Phase identifier matching plan.yaml
- `brief_path` - Relative path to phase brief
- `baseline_sha` - Fixed git commit SHA for consistent diffs throughout phase
- `plan_sha` - Hash of plan.yaml at phase start (tamper detection)
- `manifest_sha` - Hash of protocol_manifest.json at phase start (tamper detection)

**Baseline SHA:** Captured at phase start via `git rev-parse HEAD`. All gates use this as the diff anchor instead of dynamic merge-base, preventing false drift positives as the base branch advances.

---

### `.repo/plan.yaml`

Defines roadmap, phases, scope, and quality gates.

**Example:**
```yaml
plan:
  id: PROJECT-ID
  summary: "Project description"
  base_branch: "main"
  test_command: "pytest tests/ -v"  # Optional, defaults to pytest
  lint_command: "ruff check ."      # Optional, defaults to ruff

  # LLM review configuration (optional)
  llm_review_config:
    model: "claude-sonnet-4-20250514"
    max_tokens: 2000
    temperature: 0
    timeout_seconds: 60
    budget_usd: null
    fail_on_transport_error: false
    include_extensions: [".py"]
    exclude_patterns: []

  phases:
    - id: P01-phase-name
      description: "What this phase accomplishes"

      scope:
        include: ["src/module/**", "tests/module/**"]
        exclude: ["src/**/legacy/**"]

      artifacts:
        must_exist: ["src/module/file.py", "tests/test_file.py"]

      gates:
        tests:
          must_pass: true
          test_scope: "scope"  # "scope" | "all" (default: "all")
          quarantine: []       # Tests expected to fail (optional)
        lint:  { must_pass: true }
        docs: { must_update: ["docs/module.md"] }
        drift: { allowed_out_of_scope_changes: 0 }
        llm_review: { enabled: false }

      drift_rules:
        forbid_changes: ["requirements.txt", "pyproject.toml"]
```

**Key sections:**
- `scope.include` - Glob patterns defining files you MAY modify
- `scope.exclude` - Patterns within include to exclude
- `artifacts.must_exist` - Files that must exist after implementation
- `gates` - Quality checks enforced by judge
- `drift_rules.forbid_changes` - Files that absolutely cannot change

---

### `.repo/briefs/<phase-id>.md`

Phase-specific implementation instructions.

**Typical structure:**
```markdown
# Phase <ID>: <Name>

## Objective
What to accomplish

## Scope 🎯
✅ YOU MAY TOUCH: [list]
❌ DO NOT TOUCH: [list]
🤔 IF YOU NEED TO TOUCH THESE: Stop and create separate phase

## Required Artifacts
- [ ] file1.py - Description
- [ ] file2.py - Description

## Gates
- Tests: Must pass
- Docs: Must update [file]
- Drift: N out-of-scope changes allowed

## Implementation Steps
1. Step one
2. Step two
...
```

**Read the entire brief before making any changes.**

---

### `.repo/critiques/<phase-id>.md`

Judge feedback when phase needs revision.

**Example:**
```markdown
# Critique: P01-scaffold

## Issues Found

- Out-of-scope changes detected (3 files, 0 allowed):
  - tools/judge.py
  - README.md
  - requirements.txt

Options to fix:
1. Revert: git restore tools/judge.py README.md requirements.txt
2. Update phase scope in .repo/briefs/P01-scaffold.md
3. Split into separate phase

- Tests failed with exit code 1. See .repo/traces/last_tests.txt

## Resolution

Please address the issues above and re-run:
./tools/phasectl.py review P01-scaffold
```

**When this file exists:**
1. Read it completely
2. Fix ALL issues listed (don't iterate issue-by-issue)
3. Re-run `./tools/phasectl.py review <phase-id>`
4. Repeat until `.repo/critiques/<phase-id>.OK` appears

---

### `.repo/critiques/<phase-id>.OK`

Approval marker. Phase passed all gates.

**Format:**
```
Phase P01-scaffold approved at 1760223767.123
```

**When this file exists:**
- Phase is approved
- You may run `./tools/phasectl.py next` to advance

---

### `.repo/critiques/<phase-id>.json` and `.repo/critiques/<phase-id>.OK.json`

Machine-readable critique/approval formats for CI/tooling integration.

**Critique format:**
```json
{
  "phase": "P01-scaffold",
  "timestamp": 1760234567.0,
  "passed": false,
  "issues": [
    {
      "gate": "tests",
      "messages": ["Tests failed with exit code 1. See .repo/traces/last_tests.txt"]
    },
    {
      "gate": "drift",
      "messages": ["Out-of-scope changes detected (3 files, 0 allowed):", "  - README.md"]
    }
  ],
  "total_issue_count": 2
}
```

**Approval format:**
```json
{
  "phase": "P01-scaffold",
  "timestamp": 1760223767.123,
  "passed": true,
  "approved_at": 1760223767.123
}
```

---

### `.repo/traces/last_tests.txt`

Test execution results. **Read this when tests fail.**

**Format:**
```
Exit code: 0
Timestamp: 1760232719.972681

=== STDOUT ===
[test runner output]

=== STDERR ===
[error output if any]
```

---

## Quality Gates

Judge checks these in order:

### 1. Artifacts Gate

```yaml
artifacts:
  must_exist: ["src/module/file.py", "tests/test_file.py"]
```

**Check:** Files exist and are not empty

**Fails if:** Any file missing or zero bytes

---

### 2. Tests Gate

```yaml
gates:
  tests:
    must_pass: true
    test_scope: "scope"  # "scope" | "all" (default: "all")
    quarantine: []       # Tests expected to fail (optional)
```

**Check:** Test runner exit code == 0

**Test command:** From plan.yaml `test_command`, defaults to `pytest tests/ -v`

**Fails if:** Exit code != 0

**See:** `.repo/traces/last_tests.txt` for details

#### Test Scoping (Phase 2.5)

Control which tests run based on phase scope:

**`test_scope: "scope"`** - Only run tests matching `scope.include` patterns
```yaml
scope:
  include: ["src/mvp/**", "tests/mvp/**"]
gates:
  tests:
    must_pass: true
    test_scope: "scope"  # Runs only tests/mvp/** tests
```

**Benefits:**
- Fast: Doesn't run 1000 unrelated legacy tests
- Focused: Only tests what you're changing
- Prevents irrelevant failures from blocking progress

**`test_scope: "all"`** - Run entire test suite (default)

#### Test Quarantine (Phase 2.5)

Skip specific tests that are expected to fail:

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

**Use cases:**
- Breaking API deliberately, fixing tests in next phase
- Flaky external service tests (timeouts, rate limits)
- Tests dependent on infrastructure not yet built
- Legacy tests unrelated to current work

**Best practices:**
- Use `test_scope: "scope"` as primary mechanism
- Use `quarantine` sparingly for specific exceptions
- Document reason clearly
- Remove from quarantine list once fixed

---

### 3. Lint Gate (Optional)

```yaml
gates:
  lint: { must_pass: true }
```

**Check:** Linter exit code == 0

**Lint command:** From plan.yaml `lint_command`, defaults to `ruff check .`

**Fails if:** Exit code != 0

**See:** `.repo/traces/last_lint.txt` for details

---

### 4. Docs Gate

```yaml
gates:
  docs: { must_update: ["docs/module.md"] }
```

**Check:** Files exist and are not empty

**Fails if:** Any doc missing or zero bytes

**Note:** Supports section anchors like `docs/module.md#feature` (checks base file)

---

### 5. Drift Gate

```yaml
gates:
  drift: { allowed_out_of_scope_changes: 0 }
```

**Check:** Out-of-scope file count <= allowed

**Fails if:** More out-of-scope changes than allowed

**NEW: Intelligent Drift Classification:**
- **Legitimate changes** are auto-approved (protocol tools, tests, docs, Python files in src/)
- **Rogue changes** are blocked (new files, frontend, scripts)
- **Git diff analysis** distinguishes modifications from new file additions
- **Only rogue changes** count against the allowed limit

**See:** "Scope Rules" section below

---

### 6. LLM Review Gate (Optional)

```yaml
gates:
  llm_review: { enabled: true }
```

**Check:** Claude reviews changed files for architecture issues

**Requires:** `ANTHROPIC_API_KEY` environment variable

**Fails if:** LLM finds issues or API key missing

**Reviews only:** Files changed in `git diff --name-only HEAD`

**When to use:**
- High-stakes code (security, payments, data migrations)
- Autonomous overnight execution (extra validation)

**When to skip:**
- Low-risk changes
- Cost-sensitive projects

---

## Scope Rules and Drift Prevention

**The judge enforces scope boundaries using git diff.**

### Include/Exclude Patterns

From plan.yaml:
```yaml
scope:
  include: ["src/mvp/**", "tests/mvp/**"]
  exclude: ["src/**/legacy/**"]
```

**Matching rules:**
- Uses `pathspec` library (.gitignore-style glob patterns)
- `**` matches multiple directory levels recursively
- `*` matches anything in one level
- File must match `include` AND NOT match `exclude`

**Example:**
- `src/mvp/feature.py` → ✅ In scope
- `src/mvp/sub/deep.py` → ✅ In scope
- `src/mvp/legacy/old.py` → ❌ Excluded
- `tools/judge.py` → ❌ Not in include patterns

### Drift Detection

Judge runs:
```bash
# Uncommitted changes
git diff --name-only HEAD

# Committed changes from baseline (preferred)
git diff --name-only <baseline_sha>...HEAD

# OR fallback to merge-base (if no baseline_sha)
git merge-base HEAD main
git diff --name-only <merge-base>...HEAD
```

**Then classifies each file:**
- If matches scope.include AND NOT scope.exclude → in-scope
- Otherwise → out-of-scope

**Drift gate:**
```yaml
drift:
  allowed_out_of_scope_changes: 0
```

If `out_of_scope_count > allowed`, review fails.

### Forbidden Changes

From plan.yaml:
```yaml
drift_rules:
  forbid_changes: ["requirements.txt", "pyproject.toml"]
```

**If ANY forbidden file changes, review fails immediately.**

Use this for files that require separate dedicated phases.

---

## Commands

### `./tools/phasectl.py start <phase-id>`

**Purpose:** Start implementation phase with mandatory brief acknowledgment

**What it does:**
1. Displays the complete brief content with intelligence context
2. Shows mechanism opportunities and available patterns
3. Extracts and shows scope boundaries (✅/❌)
4. Requires explicit confirmation of understanding
5. Updates `.repo/briefs/CURRENT.json` with implementation status
6. Captures baseline SHA for consistent diffs

**Exit codes:**
- `0` - Phase started successfully
- `1` - Brief not found or acknowledgment declined

**Example:**
```bash
./tools/phasectl.py start P01-scaffold
```

**This command is MANDATORY** before any implementation work.

---

### `./tools/phasectl.py reset <phase-id>`

**Purpose:** Reset phase state to match current plan (for plan transitions)

**When to use:**
- After creating a new plan with different phases
- When getting "Plan changed mid-phase" errors
- When CURRENT.json points to old baseline/plan

**What it does:**
1. Validates phase exists in current plan
2. Captures current baseline SHA
3. Computes current plan/manifest hashes
4. Updates CURRENT.json with fresh state
5. Provides next steps

**Exit codes:**
- `0` - Phase state reset successfully
- `1` - Phase not found or git error

**Example:**
```bash
./tools/phasectl.py reset P01-scaffold
```

**Use this when transitioning between different plans.**

---

### `./tools/phasectl.py recover`

**Purpose:** Detect and recover from plan state corruption

**When to use:**
- When getting "Plan changed mid-phase" errors
- When protocol state seems inconsistent
- After external plan modifications (git checkout, etc.)
- When CURRENT.json doesn't match current plan

**What it does:**
1. Detects plan state corruption (SHA mismatches)
2. Provides recovery guidance
3. Shows current vs expected state
4. Guides user to appropriate recovery commands

**Exit codes:**
- `0` - No corruption detected
- `1` - Corruption detected, recovery needed

**Example:**
```bash
./tools/phasectl.py recover
```

**Use this when protocol state seems corrupted.**

---

### `./tools/phasectl.py patterns list`

**Purpose:** Show available patterns for collective intelligence

**When to use:**
- **REQUIRED** when drift issues occur
- Before proposing amendments
- To learn from successful patterns
- To understand collective intelligence

**What it does:**
1. Shows stored patterns from successful amendments
2. Displays pattern usage statistics
3. Provides guidance for current situation
4. Enables learning from collective intelligence

**Exit codes:**
- `0` - Patterns displayed successfully
- `1` - No patterns available or error

**Example:**
```bash
./tools/phasectl.py patterns list
```

**This is now REQUIRED for drift issues - agents must check patterns before proposing amendments.**

---

### `./orient.sh`

**Purpose:** Recover full context in 10 seconds

**Shows:**
- Intelligence status (patterns, amendments, mechanisms)
- Current phase ID
- Progress (X/Y phases complete)
- Status (approved/needs-fixes/in-progress)
- Next steps

**Run this:**
- After context window exhaustion
- When starting new session
- When you're confused about state

---

### `./tools/phasectl.py review <phase-id>`

**Purpose:** Submit phase for judge review

**What it does:**
1. Shows intelligence context and mechanism opportunities
2. Shows diff summary (in-scope vs out-of-scope files)
3. Runs test command from plan.yaml
4. Saves results to `.repo/traces/last_tests.txt`
5. Invokes judge to check all gates
6. Produces either `.repo/critiques/<phase-id>.md` or `.repo/critiques/<phase-id>.OK`

**Exit codes:**
- `0` - Approved (`.OK` file created)
- `1` - Needs revision (`.md` critique created)
- `2` - Error (judge couldn't run)

**Example:**
```bash
./tools/phasectl.py review P02-impl-feature
```

---

### `./tools/phasectl.py next`

**Purpose:** Advance to next phase

**What it does:**
1. Checks current phase is approved (`.OK` file exists)
2. Finds next phase in plan.yaml
3. Shows intelligence summary and learning opportunities
4. Updates `.repo/briefs/CURRENT.json` to point to next phase
5. Shows path to next brief

**Exit codes:**
- `0` - Advanced successfully or all phases complete
- `1` - Error (current phase not approved, next brief missing, etc.)

**Only run this after** `.repo/critiques/<phase-id>.OK` exists.

---

## Error Handling

### Tests Failing

**Symptom:** Review fails with "Tests failed with exit code 1"

**Recovery:**
1. Read `.repo/traces/last_tests.txt`
2. Find failing test in STDOUT/STDERR
3. Fix the code or test
4. Re-run `./tools/phasectl.py review <phase-id>`

---

### Out-of-Scope Changes

**Symptom:** Review fails with "Out-of-scope changes detected"

**Recovery options:**

**Option 1 - Revert:**
```bash
git restore file1.py file2.py
./tools/phasectl.py review <phase-id>
```

**Option 2 - Update scope:**
Edit `.repo/briefs/<phase-id>.md` and plan.yaml to include the files, then re-review.

**Option 3 - Split phase:**
Create a new phase for the out-of-scope work after current phase completes.

---

### Forbidden Files Changed

**Symptom:** "Forbidden files changed"

**Recovery:**
```bash
git restore requirements.txt pyproject.toml
./tools/phasectl.py review <phase-id>
```

**Never change forbidden files** without creating a dedicated phase.

---

### LLM Review Failures

**Symptom:** "LLM review enabled but ANTHROPIC_API_KEY not set"

**Recovery:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
./tools/phasectl.py review <phase-id>
```

Or disable LLM review in plan.yaml if not needed.

---

### Missing Artifacts

**Symptom:** "Missing required artifact: src/module/file.py"

**Recovery:**
1. Create the missing file
2. Ensure it's not empty
3. Re-run review

---

### Context Window Exhausted

**Symptom:** You lost track of what you were doing

**Recovery:**
```bash
./orient.sh  # Shows current state
cat .repo/briefs/CURRENT.json  # Current phase
cat .repo/briefs/<phase-id>.md  # What to do
```

**All state is in files.** You can always recover.

---

### Plan Changed Mid-Phase

**Symptom:** "Plan changed mid-phase: .repo/plan.yaml" error

**Root cause:** CURRENT.json points to old plan baseline, but current plan is different

**Recovery:**
```bash
# Reset phase state to match current plan
./tools/phasectl.py reset <phase-id>

# Then start implementation
./tools/phasectl.py start <phase-id>
```

**This happens when:**
- Creating new plan with different phases
- Switching between different project plans
- CURRENT.json wasn't updated after plan changes

**Prevention:** Always run `reset` after creating new plans.

---

## Execution Best Practices

### 1. Always Start with Brief Acknowledgment

```bash
./tools/phasectl.py start <phase-id>
```

This command is **mandatory** and ensures you:
- Read the complete brief
- Understand scope boundaries
- Confirm your understanding before implementing

### 2. Check Scope Explicitly

From the brief acknowledgment, identify:
- ✅ Files you MAY touch
- ❌ Files you must NOT touch
- 🤔 Files that need separate phase

**If you need something out of scope:** Stop. Note it for a follow-up phase.

### 3. Run Review Early

Don't wait until "done" to run review:

```bash
./tools/phasectl.py review <phase-id>
```

**Diff summary shows:** In-scope vs out-of-scope changes before judge runs.

**Early feedback helps:** Catch drift before writing more code.

### 4. Read Critiques Completely

When `.repo/critiques/<phase-id>.md` appears:
1. Read ALL issues (don't just fix the first one)
2. Fix them all
3. Re-review once

**Don't iterate issue-by-issue.** Fix everything in one pass.

### 5. Commit Often (If Needed)

The judge uses git diff to detect changes. You can:
- Work with uncommitted changes (judge sees them)
- Commit incrementally (judge sees diff from base branch)

**Either works.** Judge combines both.

### 6. Trust the Gates

If review passes, **all gates passed:**
- Tests ran and passed
- Docs were updated
- Scope was respected
- LLM approved (if enabled)

**No manual double-checking needed.** Judge is authoritative.

### 7. Use Orient When Lost

```bash
./orient.sh
```

Shows exactly what to do next.

---

## Protocol Integrity

The protocol protects critical files from modification:
- Judge logic (`tools/judge.py`)
- Controller logic (`tools/phasectl.py`)
- Shared utilities (`tools/lib/**`)
- Plan configuration (`.repo/plan.yaml`)
- Protocol manifest (`.repo/protocol_manifest.json`)

**How it works:**
1. `.repo/protocol_manifest.json` contains SHA256 hashes of all protocol files
2. At judge startup, before any gates: verify all hashes match
3. At phase start: store hashes of plan.yaml and manifest for mid-phase tamper detection
4. If ANY mismatch → immediate failure with clear error message

**For autonomous agents:**

**DO NOT:**
- Modify files in `tools/**`
- Edit `.repo/plan.yaml` gates or phases
- Change `.repo/protocol_manifest.json`

**If you need to fix protocol bugs:**
1. Complete current phase
2. Ask human to create protocol maintenance phase
3. Make fixes in that dedicated phase
4. Run `./tools/generate_manifest.py`
5. Complete maintenance phase

---

## Intelligence Features

The protocol includes intelligence features that help agents learn and improve:

### Pattern System
- **Check patterns**: `./tools/phasectl.py patterns list` shows stored patterns from previous phases
- **Learn from patterns**: Patterns may suggest exact solutions for common problems
- **Required for drift issues**: Must check patterns before proposing amendments

### Amendment System
- **Propose amendments**: `./tools/phasectl.py amend propose` for runtime adjustments
- **Budget limits**: Each amendment type has usage limits to prevent abuse
- **Auto-application**: Amendments are applied automatically during review

### Intelligence Dashboard
- **Status overview**: `./orient.sh` shows intelligence status (patterns, amendments, mechanisms)
- **Mechanism opportunities**: Commands surface available mechanisms during normal operation
- **Learning guidance**: Continuous guidance on available intelligence features

### Intelligence Rewards
- **Pattern usage**: Using patterns provides amendment budget bonuses
- **Learning behavior**: Learning unlocks enhanced capabilities
- **Collective intelligence**: Contributing improves future phases

---

## Collective Intelligence System

The protocol includes powerful collective intelligence capabilities that learn from execution patterns:

### Amendment System
- **Bounded Mutability**: Propose runtime adjustments within budget limits
- **Auto-Application**: Amendments applied automatically during review
- **Budget Enforcement**: Hard limits prevent amendment creep

```bash
# Propose amendments
./tools/phasectl.py amend propose set_test_cmd "python -m pytest -q" "Fix test command"

# View stored patterns
./tools/phasectl.py patterns list
 
# Important: LLMs do not edit files directly.
# They propose amendments that are filtered by budgets and auto-applied.
```

### Pattern Learning
- **JSONL Storage**: Patterns stored in `.repo/collective_intelligence/patterns.jsonl`
- **Auto-Proposal**: Patterns automatically propose amendments before review
- **Learning**: System learns from successful amendments and stores patterns

### Enhanced Briefs
- **Hints**: Briefs enhanced with hints from recent successful executions
- **Guardrails**: Execution guardrails based on current state and mode
- **Outer Loop**: Micro-retrospectives after each phase for continuous learning

### State Management
- **Governance ≠ Runtime Split**: `plan.yaml` (human-locked) vs `.repo/state/` (AI-writable)
- **Context Files**: `Pxx.ctx.json` store runtime state (baseline_sha, test_cmd, mode, budgets, usage)
- **Mode Management**: EXPLORE → LOCK transitions govern if amendments are encouraged or closed

---

## Summary

**The protocol in one sentence:**

Read brief → Implement within scope → Review with judge → Fix issues → Advance → Repeat.

**Your job:**
1. Follow the brief exactly
2. Respect scope boundaries
3. Submit for review when done
4. Fix critiques completely
5. Advance only when approved

**Start here:** `./orient.sh`
