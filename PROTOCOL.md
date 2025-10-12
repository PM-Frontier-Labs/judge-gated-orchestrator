# Gated Phase Protocol - LLM Operational Manual

**Audience:** AI coding assistants (Claude Code, Cursor, Windsurf, etc.)

**Purpose:** Precise execution instructions for autonomous work under quality gates.

---

## Protocol Overview

This is a **file-based protocol** for autonomous execution with quality gates. You will:

1. Read a phase brief defining scope and objectives
2. Implement changes within that scope
3. Submit for review to a judge
4. Handle feedback and iterate until approved
5. Advance to next phase and repeat

**All state lives in files.** No memory required. You can recover full context anytime via `./orient.sh`.

---

## Core Loop

```
1. Orient:     ./orient.sh
2. Read brief: cat .repo/briefs/<phase-id>.md
3. Implement:  Make changes within scope
4. Review:     ./tools/phasectl.py review <phase-id>
5. Check:      If .repo/critiques/<phase-id>.OK exists → approved
               If .repo/critiques/<phase-id>.md exists → fix and re-review
6. Advance:    ./tools/phasectl.py next
7. Repeat from step 1
```

---

## File Specifications

### `.repo/briefs/CURRENT.json`

Points to the active phase.

**Format:**
```json
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": 1760223767.0468428
}
```

**Fields:**
- `phase_id` (string): Phase identifier matching plan.yaml
- `brief_path` (string): Relative path to phase brief
- `status` (string): Always "active" for current phase
- `started_at` (float): Unix timestamp when phase started

**Read this first** when recovering context.

---

### `.repo/plan.yaml`

Defines roadmap, phases, scope, and quality gates.

**Format:**
```yaml
plan:
  id: PROJECT-ID
  summary: "Short description of overall goal"
  base_branch: "main"
  test_command: "pytest tests/ -v"  # Optional, defaults to pytest

  phases:
    - id: P01-phase-name
      description: "What this phase accomplishes"

      scope:
        include: ["src/module/**", "tests/module/**"]
        exclude: ["src/**/legacy/**"]

      artifacts:
        must_exist: ["src/module/file.py", "tests/test_file.py"]

      gates:
        tests: { must_pass: true }
        docs: { must_update: ["docs/module.md"] }
        drift: { allowed_out_of_scope_changes: 0 }
        llm_review: { enabled: false }

      drift_rules:
        forbid_changes: ["requirements.txt", "pyproject.toml"]
```

**Key sections:**
- **scope.include**: Glob patterns defining files you MAY modify
- **scope.exclude**: Patterns within include to exclude
- **artifacts.must_exist**: Files that must exist after implementation
- **gates**: Quality checks enforced by judge
- **drift_rules.forbid_changes**: Files that absolutely cannot change

**The judge validates all gates before approval.**

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

**Read the entire brief** before making any changes.

---

### `.repo/critiques/<phase-id>.md`

Judge feedback when phase needs revision.

**Format:**
```markdown
# Critique: P01-scaffold

## Issues Found

- Out-of-scope changes detected (3 files, 0 allowed):
  - tools/judge.py
  - README.md
  - requirements.txt

Options to fix:
1. Revert: git checkout HEAD tools/judge.py README.md requirements.txt
2. Update phase scope in .repo/briefs/P01-scaffold.md
3. Split into separate phase

- Tests failed with exit code 1. See .repo/traces/last_test.txt

## Resolution

Please address the issues above and re-run:
```
./tools/phasectl.py review P01-scaffold
```
```

**When this file exists:**
1. Read it completely
2. Fix all issues listed
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

### `.repo/traces/last_test.txt`

Test execution results.

**Format:**
```
Exit code: 0
Timestamp: 1760232719.972681

=== STDOUT ===
[test runner output]

=== STDERR ===
[error output if any]
```

**Read this when tests fail** to understand what broke.

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
- Uses `fnmatch` (shell-style glob patterns)
- `**` matches multiple directory levels
- `*` matches anything in one level
- File must match `include` AND NOT match `exclude`

**Example:**
- `src/mvp/feature.py` → ✅ In scope
- `src/mvp/legacy/old.py` → ❌ Excluded
- `tools/judge.py` → ❌ Not in include patterns

### Drift Detection

Judge runs:
```bash
# Uncommitted changes
git diff --name-only HEAD

# Committed changes from base branch
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

Use this for files that require separate dedicated phases (dependencies, CI config, etc.).

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

### 2. Tests Gate

```yaml
gates:
  tests: { must_pass: true }
```

**Check:** Test runner exit code == 0

**Test command:** From plan.yaml `test_command`, defaults to `pytest tests/ -v`

**Fails if:** Exit code != 0

**See:** `.repo/traces/last_test.txt` for details

### 3. Docs Gate

```yaml
gates:
  docs: { must_update: ["docs/module.md"] }
```

**Check:** Files exist and are not empty

**Fails if:** Any doc missing or zero bytes

**Note:** Supports section anchors like `docs/module.md#feature` (checks base file)

### 4. Drift Gate

```yaml
gates:
  drift: { allowed_out_of_scope_changes: 0 }
```

**Check:** Out-of-scope file count <= allowed

**Fails if:** More out-of-scope changes than allowed

**See:** "Scope Rules" section above

### 5. LLM Review Gate (Optional)

```yaml
gates:
  llm_review: { enabled: true }
```

**Check:** Claude reviews changed files for architecture issues

**Requires:** `ANTHROPIC_API_KEY` environment variable

**Fails if:** LLM finds issues or API key missing

**Reviews only:** Files changed in `git diff --name-only HEAD`

---

## Commands Reference

### `./orient.sh`

**Purpose:** Recover full context in 10 seconds

**Shows:**
- Current phase ID
- Progress (X/Y phases complete)
- Status (approved/needs-fixes/in-progress)
- Next steps

**Run this:**
- After context window exhaustion
- When starting new session
- When you're confused about state

**Example output:**
```
🎯 Current Phase: P02-impl-feature (2/2)

📊 Progress:
✅ P01-scaffold (approved)
⚠️  P02-impl-feature (needs fixes)

📄 Current Brief:
.repo/briefs/P02-impl-feature.md

🔍 Status:
Critique exists: .repo/critiques/P02-impl-feature.md

⏭️  Next Steps:
1. Read critique: cat .repo/critiques/P02-impl-feature.md
2. Fix issues
3. Re-submit: ./tools/phasectl.py review P02-impl-feature
```

### `./tools/phasectl.py review <phase-id>`

**Purpose:** Submit phase for judge review

**What it does:**
1. Shows diff summary (in-scope vs out-of-scope files)
2. Runs test command from plan.yaml
3. Saves results to `.repo/traces/last_test.txt`
4. Invokes judge to check all gates
5. Produces either `.repo/critiques/<phase-id>.md` or `.repo/critiques/<phase-id>.OK`

**Exit codes:**
- `0` - Approved (`.OK` file created)
- `1` - Needs revision (`.md` critique created)
- `2` - Error (judge couldn't run)

**Example:**
```bash
./tools/phasectl.py review P02-impl-feature
```

### `./tools/phasectl.py next`

**Purpose:** Advance to next phase

**What it does:**
1. Checks current phase is approved (`.OK` file exists)
2. Finds next phase in plan.yaml
3. Updates `.repo/briefs/CURRENT.json` to point to next phase
4. Shows path to next brief

**Exit codes:**
- `0` - Advanced successfully or all phases complete
- `1` - Error (current phase not approved, next brief missing, etc.)

**Example:**
```bash
./tools/phasectl.py next
# Output:
# ➡️  Advanced to phase P03-refactor
# 📄 Brief: .repo/briefs/P03-refactor.md
```

**Only run this after** `.repo/critiques/<phase-id>.OK` exists.

---

## Error Handling and Recovery

### Tests Failing

**Symptom:** Review fails with "Tests failed with exit code 1"

**Recovery:**
1. Read `.repo/traces/last_test.txt`
2. Find failing test in STDOUT/STDERR
3. Fix the code or test
4. Re-run `./tools/phasectl.py review <phase-id>`

### Out-of-Scope Changes

**Symptom:** Review fails with "Out-of-scope changes detected"

**Recovery options:**

**Option 1 - Revert:**
```bash
git checkout HEAD file1.py file2.py
./tools/phasectl.py review <phase-id>
```

**Option 2 - Update scope:**
Edit `.repo/briefs/<phase-id>.md` and plan.yaml to include the files, then re-review.

**Option 3 - Split phase:**
Create a new phase for the out-of-scope work after current phase completes.

### Forbidden Files Changed

**Symptom:** "Forbidden files changed"

**Recovery:**
```bash
git checkout HEAD requirements.txt pyproject.toml
./tools/phasectl.py review <phase-id>
```

**Never change forbidden files** without creating a dedicated phase.

### LLM Review Failures

**Symptom:** "LLM review enabled but ANTHROPIC_API_KEY not set"

**Recovery:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
./tools/phasectl.py review <phase-id>
```

Or disable LLM review in plan.yaml if not needed.

### Missing Artifacts

**Symptom:** "Missing required artifact: src/module/file.py"

**Recovery:**
1. Create the missing file
2. Ensure it's not empty
3. Re-run review

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

## Execution Best Practices

### 1. Always Read the Brief First

```bash
cat .repo/briefs/<phase-id>.md
```

Understand scope boundaries before writing any code.

### 2. Check Scope Explicitly

From the brief, identify:
- ✅ Files you MAY touch
- ❌ Files you must NOT touch
- 🤔 Files that need separate phase

**If you need something out of scope:** Stop. Create a follow-up phase.

### 3. Run Review Early

Don't wait until "done" to run review. Run it when you think you're close:

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

## Multi-Phase Workflow Example

**Scenario:** 3-phase refactor

**Setup:**
- P01: Scaffold new module
- P02: Implement core feature
- P03: Refactor + optimize

**Execution:**

```bash
# Start
./orient.sh
# → Shows P01-scaffold is current phase

# Read brief
cat .repo/briefs/P01-scaffold.md
# → Scope: src/mvp/**, tests/mvp/**, docs/mvp.md

# Implement
# ... create src/mvp/__init__.py
# ... create tests/mvp/test_golden.py
# ... create docs/mvp.md

# Review
./tools/phasectl.py review P01-scaffold
# → Shows diff summary
# → Runs tests
# → Judge checks gates
# → Creates .repo/critiques/P01-scaffold.OK ✅

# Advance
./tools/phasectl.py next
# → Updates CURRENT.json to P02-impl-feature

# Read next brief
cat .repo/briefs/P02-impl-feature.md
# → Scope: src/mvp/feature.py, tests/mvp/test_feature.py

# Implement
# ... create src/mvp/feature.py
# ... create tests/mvp/test_feature.py
# ... accidentally edit tools/judge.py (drift!)

# Review
./tools/phasectl.py review P02-impl-feature
# → Diff summary: ❌ Out of scope (1 file)
# → Judge creates critique

# Read critique
cat .repo/critiques/P02-impl-feature.md
# → "Out-of-scope changes: tools/judge.py"
# → "Fix: git checkout HEAD tools/judge.py"

# Fix
git checkout HEAD tools/judge.py

# Re-review
./tools/phasectl.py review P02-impl-feature
# → All gates pass ✅

# Advance
./tools/phasectl.py next
# → Updates to P03-refactor

# ... continue for P03
```

**Result:** 3 phases completed, each validated, no drift.

---

## What Happens During Review

Detailed breakdown of `./tools/phasectl.py review <phase-id>`:

**Step 1: Diff Summary**
- Runs `git diff --name-only HEAD` (uncommitted)
- Runs `git diff --name-only <merge-base>...HEAD` (committed)
- Combines both lists
- Classifies each file as in-scope or out-of-scope
- Shows:
  ```
  📊 Change Summary:
  ✅ In scope (3 files):
    - src/mvp/feature.py
    - tests/mvp/test_feature.py
    - docs/mvp.md

  ❌ Out of scope (1 file):
    - tools/judge.py

  ⚠️  Drift limit: 0 files allowed, 1 found
  ```

**Step 2: Run Tests**
- Gets test command from plan.yaml (defaults to `pytest tests/ -v`)
- Checks if test runner installed
- Runs tests
- Saves stdout/stderr to `.repo/traces/last_test.txt`
- Continues even if tests fail (judge will catch it)

**Step 3: Invoke Judge**
- Runs `./tools/judge.py <phase-id>`
- Judge performs 5 checks (artifacts, tests, docs, drift, LLM)
- Each check returns list of issues
- If any issues found → writes `.repo/critiques/<phase-id>.md`
- If zero issues → writes `.repo/critiques/<phase-id>.OK`

**Step 4: Show Verdict**
- If `.OK` exists: "✅ Phase approved!"
- If `.md` exists: "❌ Phase needs revision:" + shows critique
- Exit with appropriate code (0=approved, 1=critique, 2=error)

---

## File-Based State Management

**Why files?**
- **Context-window proof:** All state recoverable from disk
- **No memory needed:** New instance can resume work instantly
- **Debuggable:** `ls .repo/critiques/` shows status
- **Version controlled:** Git tracks all state changes
- **Tool-agnostic:** Any tool can read/write these files

**What's NOT in files:**
- Nothing. Everything is on disk.

**Recovery from any state:**
1. `./orient.sh` → See current phase and status
2. `cat .repo/briefs/CURRENT.json` → Get phase ID
3. `cat .repo/briefs/<phase-id>.md` → Read instructions
4. `ls .repo/critiques/` → Check if approved or needs fixes
5. Resume work

**No exceptions. No hidden state. No surprises.**

---

## When to Create New Phases

**Create a new phase when:**

1. **Out-of-scope changes needed**
   - Current scope doesn't allow the files you need to change
   - Judge will block you with drift errors
   - Solution: Create a phase after current one with correct scope

2. **Forbidden files need changes**
   - `requirements.txt`, `pyproject.toml`, CI configs
   - These typically require dedicated phases
   - Keeps dependency changes isolated and reviewable

3. **Work crosses multiple modules**
   - Each phase should have cohesive scope
   - If refactoring 3 modules, consider 3 phases
   - Easier to review, easier to rollback

4. **Testing strategy changes**
   - Phase 1: Implement feature
   - Phase 2: Add integration tests
   - Separate concerns, separate gates

5. **High-risk changes**
   - Database migrations
   - API contract changes
   - Give these dedicated phases with strict gates

**Don't create phases for:**
- Minor tweaks within current scope
- Documentation updates in-scope
- Test fixes for current feature

**When in doubt:** Can this be reviewed as one cohesive change? If yes → same phase. If no → new phase.

---

## LLM Review Details

**When enabled:**
```yaml
gates:
  llm_review: { enabled: true }
```

**What it does:**
1. Runs `git diff --name-only HEAD` to find changed files
2. Reads each changed file's content
3. Sends to Claude with this prompt:
   ```
   Review this code for architecture issues, bugs, or anti-patterns.
   Focus on: correctness, maintainability, performance, security.
   If you find issues, list them clearly.
   If code looks good, respond "LGTM".
   ```
4. Parses response
5. If issues found → adds to critique
6. If "LGTM" → gate passes

**Requirements:**
- `ANTHROPIC_API_KEY` environment variable
- `anthropic` Python package installed

**Costs:**
- ~$0.01-0.10 per review depending on file count/size
- Only reviews changed files (not all in-scope files)

**When to use:**
- High-stakes code (security, payments, data migrations)
- Autonomous overnight execution (extra validation)
- Learning projects (get feedback on approach)

**When to skip:**
- Low-risk changes
- Cost-sensitive projects
- You prefer manual review

---

## This Protocol vs Frameworks

**This is a protocol, not a framework.**

You don't install it, you follow it.

**What that means:**

**Frameworks:**
- Import classes: `from framework import Agent`
- Learn API: `agent.run(task)`
- Dependency: `pip install framework`

**This protocol:**
- Follow conventions: `.repo/briefs/CURRENT.json`
- Run commands: `./tools/phasectl.py review P01`
- No imports: Just files and shell scripts

**Like Git:**
- Git doesn't dictate your code
- Git defines conventions (`.git/`, `HEAD`, commits)
- Tools follow those conventions
- This protocol is the same

**You could:**
- Rewrite `phasectl.py` in Bash
- Rewrite `judge.py` in Rust
- Use Make instead of Python

**As long as:**
- You write `.repo/briefs/CURRENT.json` correctly
- You read `plan.yaml` correctly
- You create `.repo/critiques/<phase-id>.OK` on approval

**The protocol is the spec. This repo is one implementation.**

---

## Quick Command Cheat Sheet

```bash
# Recover context
./orient.sh

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

# Advance to next phase
./tools/phasectl.py next

# See test results
cat .repo/traces/last_test.txt

# Check diff before review
git diff --name-only HEAD
```

---

## Summary

**The protocol in one sentence:**

Read brief → Implement within scope → Review with judge → Fix issues → Advance → Repeat until roadmap complete.

**Key principles:**
1. All state in files (context-window proof)
2. Judge enforces gates (quality guaranteed)
3. Scope boundaries prevent drift (focus maintained)
4. Autonomous execution (overnight work possible)
5. Protocol, not framework (simple, replaceable)

**Your job as an LLM agent:**
1. Follow the brief exactly
2. Respect scope boundaries
3. Submit for review when done
4. Fix critiques completely
5. Advance only when approved

**The judge's job:**
1. Enforce quality gates
2. Prevent scope drift
3. Block progression until all gates pass
4. Provide actionable feedback

**Together:** You get autonomous multi-phase execution with quality guarantees.

**Start here:** `./orient.sh`
