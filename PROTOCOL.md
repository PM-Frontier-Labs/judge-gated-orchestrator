# Gated Phase Protocol - Execution Manual

**Audience:** AI coding assistants (Claude Code, Cursor, Windsurf, etc.) executing phases autonomously

**Purpose:** Precise instructions for working within quality-gated phases

This document is for execution. For planning, collaborate with a human to draft `.repo/plan.yaml` following the examples in `GETTING_STARTED.md`.

---

## Core Loop

```
1. Orient:     ./orient.sh                             # Shows current status (MANDATORY)
2. Start:      ./tools/phasectl.py start <phase-id>    # Capture baseline
3. Implement:  Make changes within scope
4. Review:     ./tools/phasectl.py review <phase-id>   # Run all gates
5. Check:      If .repo/critiques/<phase-id>.OK → approved
               If .repo/critiques/<phase-id>.md → fix and re-review
6. Reflect:    ./tools/phasectl.py reflect <phase-id>  # Record learnings
7. Advance:    ./tools/phasectl.py next                # Requires orient acknowledgment
8. Repeat from step 1
```

### ⚠️ CRITICAL: Phase Start Timing

**ALWAYS run `start` BEFORE making any code changes:**

```bash
# ❌ WRONG ORDER (common mistake):
# 1. Make code changes
# 2. Run: ./tools/phasectl.py start P01  ← Baseline captures your changes!
# 3. Review fails - judge can't detect changes properly

# ✅ CORRECT ORDER:
# 1. Run: ./tools/phasectl.py start P01   ← Baseline captures clean state  
# 2. Make code changes                    ← Changes tracked from baseline
# 3. Run: ./tools/phasectl.py review P01  ← Judge sees changes correctly
```

**Why:** The baseline SHA is captured when you run `start`. All git diffs are calculated from this baseline. If you start after making changes, the baseline will include your work, and the judge won't detect changes properly.

**If you started too late:** Edit `.repo/state/current.json` and set `baseline_sha` to the commit SHA before your changes started.

**All state lives in files.** No memory required. Recover full context anytime via `./orient.sh`.

---

## Quick Command Reference

```bash
# Context recovery
./orient.sh                                # Show current status

# Phase management
./tools/phasectl.py start P01-scaffold     # Start phase
./tools/phasectl.py review P01-scaffold    # Submit for review
./tools/phasectl.py reflect P01-scaffold   # Record learnings
./tools/phasectl.py next                   # Advance to next phase
./tools/phasectl.py acknowledge-orient     # Acknowledge context

# Scope handling
./tools/phasectl.py justify-scope P01-scaffold   # Justify out-of-scope changes

# Status checking
cat .repo/state/current.json               # Current phase
ls -la .repo/critiques/                    # Review status
cat .repo/learnings.md                     # Past learnings
```

---

## File Specifications

### `.repo/state/current.json`

Tracks the active phase:

```json
{
  "phase_id": "P01-scaffold",
  "started_at": "2025-10-28T10:30:00Z",
  "baseline_sha": "abc123def456",
  "plan_sha": "789012345678"
}
```

### `.repo/plan.yaml`

Defines project phases and gates:

```yaml
phases:
  - id: P01-scaffold
    brief: |
      # Objective
      Set up basic project structure
      
      # Scope 🎯
      src/**/*.py
      tests/**/*.py
      requirements.txt
      
      # Deliverables
      - Basic package structure
      - Test framework configured
      - Dependencies documented
    
    gates:
      tests: true
      lint: false
      docs: false
      drift: true
      llm_review: false
    
    test_cmd: "python -m pytest tests/ -v"
    lint_cmd: "ruff check src/"

  - id: P02-implement
    brief: "Implement core feature..."
    gates:
      tests: true
      lint: true
      docs: true
      drift: true
      llm_review: true
```

### Phase Briefs in plan.yaml

All phase briefs are embedded directly in plan.yaml (see example above).

**Format:**
```yaml
phases:
  - id: P01-feature
    description: "Short description"
    brief: |
      # Objective
      Build the user authentication system
      
      ## Scope 🎯
      - src/auth/**
      - tests/test_auth.py
      
      ## Required Artifacts
      - User login/logout functions
      - Password hashing
      - Session management

## Gates
- tests: Required
- docs: Required
- drift: Enforced
```

---

## Modifying plan.yaml During a Phase

**You CAN modify plan.yaml at any time.** It's your configuration file, not a locked governance document.

**Common modifications:**
- Adjust scope patterns (discovered you need additional files)
- Change gate configuration (skip integration tests, disable lint temporarily)
- Update test/lint commands
- Add exclusion patterns
- Modify briefs for clarity

**How to modify:**

```bash
# 1. Edit the file
vim .repo/plan.yaml

# 2. Commit the change
git add .repo/plan.yaml
git commit -m "Update test configuration to skip integration tests"

# 3. Continue working
./tools/phasectl.py review <phase-id>
```

**Examples of common modifications:**

**Skip integration tests:**
```yaml
gates:
  tests:
    unit:
      must_pass: true
    integration:
      allow_skip: true  # Don't block on integration failures
```

**Exclude files from scope:**
```yaml
scope:
  include: ["src/**", "tests/**"]
  exclude: ["tests/integration/**"]  # Don't check integration tests
```

**Override test command for specific phase** (useful in monorepos):
```yaml
phases:
  - id: P01-backend
    test_command: "pytest tests/unit/ -v"  # Override plan-level command
    lint_command: "ruff check src/"        # Skip frontend lint
    
    gates:
      tests: {must_pass: true}
      lint: {must_pass: true}
```

**Phase-level overrides take precedence** over plan-level commands. This is useful when:
- Backend-only phases in a monorepo (skip frontend lint)
- Different test strategies per phase
- Phase-specific tool configuration

**No special commands or permissions needed. Just edit, commit, and continue.**

---

### `.repo/critiques/<phase-id>.md`

Judge feedback when issues are found:

```markdown
# Issues Found

## ❌ Tests Gate Failed
Test suite returned exit code 1

**Failures:**
- test_login failed: AssertionError

## ❌ Docs Gate Failed
Required documentation not updated:
- README.md not modified

## Resolution
1. Fix failing test in tests/test_auth.py
2. Update README.md with usage examples
3. Re-run: ./tools/phasectl.py review P02-implement
```

### `.repo/critiques/<phase-id>.OK`

Created when all gates pass:

```
Phase P01-scaffold approved
Timestamp: 2025-10-28T10:45:00Z
All gates passed
```

### `.repo/learnings.md`

Accumulated insights from reflections:

```markdown
# Project Learnings

## P01-scaffold (2025-10-28)
- Writing tests first helped catch integration issues early
- Keeping dependencies minimal reduced complexity
- Clear documentation improved onboarding

## P02-implement (2025-10-28)
- Edge case testing was crucial
- Refactoring early saved time later
```

### `.repo/scope_audit/<phase-id>.md`

Justifications for out-of-scope changes:

```markdown
# Scope Justification: P01-scaffold

## Out-of-Scope Changes
- Modified utils/helpers.py (not in scope)

## Justification
Discovered that the helper function had a bug that blocked 
implementation. Fixed it while working on the phase to maintain
momentum. The change is minimal and well-tested.

## Decision
Human review recommended. Changes preserved.
```

---

## Quality Gates

### 1. Tests Gate

Runs test suite and checks for success.

#### Simple Mode

```yaml
gates:
  tests:
    must_pass: true

test_command: "python -m pytest tests/ -v"
```

**Pass criteria:**
- Test command exits with code 0
- No test failures

**Failure handling:**
- Review `.repo/traces/last_tests.txt` for details
- Fix failing tests
- Re-run review

#### Split Unit and Integration Tests

For projects with integration tests that may fail for environmental reasons:

```yaml
gates:
  tests:
    unit:
      must_pass: true
    integration:
      allow_skip: true  # Don't block phase if integration tests fail
```

**Smart Auto-Skip (NEW):**

Integration tests are **automatically skipped** if no integration files in your phase scope:

```yaml
# Phase scope:
scope:
  include:
    - "src/backend/**"
    - "tests/unit/**"
  # No tests/integration/** in scope

gates:
  tests:
    unit:
      must_pass: true
    integration: {}  # Auto-skipped (no integration files in scope)
```

**Output:**
```
🧪 Running tests...
   - Unit tests... ✅ Pass
   - Integration tests... ⏭️ Auto-skipped (no integration files in scope)
```

**When auto-skip happens:**
- Phase scope doesn't include integration test files
- Integration tests wouldn't be relevant
- Eliminates need for `allow_skip: true` on most phases

**Force integration tests to run:**
```yaml
gates:
  tests:
    integration:
      force_run: true  # Run even if not in scope
```

**When to use split mode:**
- Integration tests depend on external services (databases, APIs)
- Integration tests are slow or flaky
- You want different enforcement for unit vs integration

**How it works:**
- **Unit tests:** Must pass (hard requirement)
- **Integration tests:** Auto-skipped if not in scope, or run with `allow_skip: true`
- Judge runs only relevant tests

**Alternative:** Exclude integration tests from scope entirely (same effect):
```yaml
scope:
  include: ["src/**", "tests/unit/**"]
  exclude: ["tests/integration/**"]
```

### 2. Lint Gate (Optional)

Runs static analysis:

```yaml
gates:
  lint: true
lint_cmd: "ruff check src/"
```

**Pass criteria:**
- Lint command exits with code 0
- No linting errors

### 3. Docs Gate

Checks that documentation is updated:

```yaml
gates:
  docs: true
```

**Pass criteria:**
- At least one documentation file modified
- Common docs: README.md, CHANGELOG.md, docs/*.md

### 4. Drift Gate

Prevents out-of-scope changes:

```yaml
gates:
  drift: true
```

**Pass criteria:**
- All changed files match phase scope patterns
- No modifications outside scope

**Scope drift handling:**
```bash
# If drift detected:
./tools/phasectl.py justify-scope P01-scaffold
# Provide justification
# Gates pass with warning
```

### 5. LLM Review Gate (Optional)

Semantic code review:

```yaml
gates:
  llm_review:
    enabled: true
    model: "claude-sonnet-4-20250514"
    max_tokens: 2000
    goals:
      - "Check for security vulnerabilities"
      - "Verify proper error handling"
```

**Pass criteria:**
- No critical issues found by LLM
- Code meets specified goals

---

## Scope Rules

### Include Patterns

```yaml
phases:
  - id: P01
    scope:
      - "src/auth/**"
      - "tests/test_auth.py"
      - "README.md"
```

**Matching:**
- Uses gitignore-style patterns
- `**` matches any depth
- `*` matches within directory
- Exact paths are literal matches

### Drift Detection

Changes outside scope trigger drift gate:

```bash
# Changed files in scope: ✅ Pass
src/auth/login.py       # In scope
tests/test_auth.py      # In scope

# Changed files out of scope: ❌ Fail
src/utils/helpers.py    # Out of scope
config/settings.py      # Out of scope
```

**Resolution:**
1. Revert out-of-scope changes, OR
2. Justify the drift:
   ```bash
   ./tools/phasectl.py justify-scope P01
   ```

---

## Commands

### `./orient.sh`

**Purpose:** Recover context and show current state

**Output:**
- Current phase
- Recent learnings
- Next steps
- File changes

**Usage:**
```bash
./orient.sh
```

**Always run this first** when resuming work.

### `./tools/phasectl.py start <phase-id>`

**Purpose:** Start a new phase

**Actions:**
1. Validates phase exists in plan.yaml
2. Captures git baseline (current commit)
3. Updates CURRENT.json
4. Shows brief

**Usage:**
```bash
./tools/phasectl.py start P01-scaffold
```

**Requirements:**
- Working directory must be clean (git)
- Phase must exist in plan.yaml
- No phase currently in progress

### `./tools/phasectl.py review <phase-id>`

**Purpose:** Submit phase for review

**Actions:**
1. Shows git diff summary
2. Runs test command (if tests gate enabled)
3. Runs lint command (if lint gate enabled)
4. Invokes judge with all gates
5. Writes critique or approval

**Usage:**
```bash
./tools/phasectl.py review P01-scaffold
```

**Output:**
- `.repo/critiques/P01-scaffold.md` (if issues found)
- `.repo/critiques/P01-scaffold.OK` (if approved)

### `./tools/phasectl.py justify-scope <phase-id>`

**Purpose:** Justify out-of-scope changes

**Actions:**
1. Shows out-of-scope files
2. Prompts for justification
3. Saves to `.repo/scope_audit/<phase-id>.md`
4. Allows gates to pass with warning

**Usage:**
```bash
./tools/phasectl.py justify-scope P01-scaffold
# Enter justification when prompted
```

**When to use:**
- Drift gate detected out-of-scope changes
- Changes are necessary and justified
- Want to preserve work and continue

### `./tools/phasectl.py reflect <phase-id>`

**Purpose:** Record learnings after phase completion

**Actions:**
1. Prompts for insights and learnings
2. Appends to `.repo/learnings.md`
3. Visible in future `orient.sh` output

**Usage:**
```bash
# After phase approval
./tools/phasectl.py reflect P01-scaffold
# Enter learnings when prompted
```

**Benefits:**
- Builds institutional knowledge
- Prevents repeated mistakes
- Shares insights across phases

### `./tools/phasectl.py next`

**Purpose:** Advance to next phase

**Actions:**
1. Checks current phase is approved
2. Requires orient acknowledgment
3. Updates CURRENT.json to next phase
4. Shows next brief

**Usage:**
```bash
./tools/phasectl.py next
# If orient not acknowledged:
./orient.sh
./tools/phasectl.py acknowledge-orient
./tools/phasectl.py next
```

**Requirements:**
- Current phase must be approved (.OK file exists)
- Must have acknowledged orient
- Next phase must exist in plan.yaml

### `./tools/phasectl.py acknowledge-orient`

**Purpose:** Confirm understanding of current state

**Actions:**
1. Prompts for current state summary
2. Records acknowledgment
3. Allows `next` command to proceed

**Usage:**
```bash
./orient.sh                              # Review state
./tools/phasectl.py acknowledge-orient   # Acknowledge
# Prompted: "Describe current state and next steps"
```

**Prevents:**
- Context loss between phases
- Starting work without understanding
- Advancing without reviewing state

---

## Error Handling

### Common Errors

**"Phase not found"**
```
Solution: Check .repo/plan.yaml for correct phase_id
```

**"Drift detected"**
```
Solution: ./tools/phasectl.py justify-scope <phase-id>
Or: git restore <out-of-scope-files>
```

**"Tests failed"**
```
Solution: Check .repo/traces/last_tests.txt
Fix failing tests
Re-run review
```

**"Must acknowledge orient"**
```
Solution: ./orient.sh
./tools/phasectl.py acknowledge-orient
```

**"Phase not approved"**
```
Solution: Review .repo/critiques/<phase-id>.md
Fix issues
Re-run review
```

---

## Best Practices

### 1. Always Orient First
```bash
./orient.sh  # ALWAYS run this first
```

### 2. Keep Changes in Scope
- Review scope patterns in brief
- Only modify files matching scope
- If drift needed, justify it

### 3. Write Tests
- Tests are your safety net
- Write tests before implementation
- Run tests frequently

### 4. Document Changes
- Update README.md or relevant docs
- Explain non-obvious decisions
- Keep documentation current

### 5. Reflect on Learnings
```bash
./tools/phasectl.py reflect P01
# Record what worked, what didn't
```

### 6. Review Gate Failures Carefully
- Read critique file completely
- Understand each issue
- Fix thoroughly, don't patch

---

## Workflow Example

Complete workflow for a typical phase:

```bash
# 1. Recover context
./orient.sh

# 2. Start phase
./tools/phasectl.py start P01-scaffold

# 3. Implement (write code, tests, docs)
# - Edit files within scope
# - Write tests
# - Update documentation

# 4. Submit for review
./tools/phasectl.py review P01-scaffold

# 5a. If approved:
./tools/phasectl.py reflect P01-scaffold
./tools/phasectl.py next
./tools/phasectl.py acknowledge-orient

# 5b. If critique:
cat .repo/critiques/P01-scaffold.md
# Fix issues
./tools/phasectl.py review P01-scaffold
# Repeat until approved

# 5c. If drift detected:
./tools/phasectl.py justify-scope P01-scaffold
# Provide justification
./tools/phasectl.py review P01-scaffold
```

---

## State Files Summary

All protocol state lives in these files:

```
.repo/
├── plan.yaml                    # Phase definitions with embedded briefs
├── state/
│   ├── current.json            # Current phase state
│   └── acknowledged.json       # Orient acknowledgment
├── critiques/
│   ├── <phase-id>.md           # Issues found
│   └── <phase-id>.OK           # Approval marker
├── learnings.md                # Accumulated insights
├── scope_audit/
│   └── <phase-id>.md           # Drift justifications
├── traces/
│   └── last_tests.txt          # Test output
└── protocol_manifest.json      # SHA256 hashes for integrity
```

---

## Philosophy

**Conversation over enforcement.**

When issues arise, the protocol prefers dialog over blocking:
- Scope drift → Justify instead of revert
- Context loss → Acknowledge instead of repeat
- Failed learning → Reflect instead of forget

**The goal:** Keep work moving while maintaining quality and context.

---

## Next Steps

- Read `GETTING_STARTED.md` for setup instructions
- Review `ARCHITECTURE.md` for technical details
- Start with `./orient.sh` to see current state
- Execute your first phase following this workflow

---

## Support

**Issues?**
- Check `.repo/critiques/` for feedback
- Review `.repo/traces/` for command output
- Read error messages carefully (they're actionable)
- Consult `GETTING_STARTED.md` for troubleshooting

**The protocol is file-based.** All state is visible and recoverable.
