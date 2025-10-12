# JUDGE-GATED ORCHESTRATOR - COMPLETE DOCUMENTATION
# All documentation in one file for easy reading and sharing
# Generated: 2025-01-15

===============================================================================
README - START HERE (ALL AUDIENCES)
===============================================================================

# Gated Phase Protocol

**Autonomous AI execution with quality gates. Works in your terminal with Claude Code, Cursor, or any AI coding assistant.**

## What Is This?

A **protocol** for autonomous execution—not a framework you import, but file conventions you follow.

Like Git tracks code changes through `.git/`, `HEAD`, and commit messages, this protocol tracks autonomous work through:
- **`.repo/briefs/CURRENT.json`** - Points to current phase
- **`.repo/plan.yaml`** - Defines phases and quality gates
- **`.repo/critiques/<phase>.{md,OK}`** - Judge feedback

Any tool that follows these conventions can participate. This repo includes a reference implementation in Python, but you could rewrite it in Bash, Rust, or Make.

## Why It Matters

**The problem:** AI agents drift off-task, skip tests, ignore scope boundaries, and require constant supervision.

**The solution:** Define phases with quality gates. Judge blocks progression until all gates pass. Agent iterates until approved, then advances autonomously.

**Result:** You define a 6-week roadmap, go to sleep, wake up to 2-3 completed phases with tests passing and docs updated.

## Key Features

✅ **Autonomous execution** - Agent works through phases without supervision
✅ **Quality enforcement** - Tests, docs, drift prevention, optional LLM review
✅ **Protocol integrity** - SHA256-based tamper detection prevents agents from modifying judge
✅ **Context-window proof** - All state in files, `./orient.sh` recovers context in <10 seconds
✅ **Terminal-native** - No servers, no APIs, just files and shell commands
✅ **Language-agnostic** - File-based protocol works for any language
✅ **5-minute setup** - Clone, `pip install -r requirements.txt`, run demo

## When to Use

✅ **Multi-phase projects** - Breaking work into 3+ sequential phases
✅ **Overnight autonomous work** - Agent executes while you sleep
✅ **Quality-critical code** - Need tests + docs enforced automatically
✅ **AI-assisted development** - Claude Code, Cursor, Windsurf, etc.
✅ **Scope control** - Prevent drift and "drive-by" changes

## When NOT to Use

❌ **Single tasks** - Just prompt Claude directly
❌ **No quality requirements** - Gates add overhead
❌ **Exploratory coding** - Rigid phases slow down discovery
❌ **Non-git projects** - Drift prevention requires git

## Quick Demo (30 Seconds)

```bash
# Clone
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator

# Install
pip install -r requirements.txt

# See status
./orient.sh

# Try the review flow
./tools/phasectl.py review P02-impl-feature
# → Shows diff summary, runs tests, invokes judge, shows result
```

**What you'll see:** System catches out-of-scope changes, enforces gates, provides clear feedback.

## How It Compares

| Feature | This Protocol | Aider | LangGraph | Manual Prompting |
|---------|---------------|-------|-----------|------------------|
| **Quality gates** | ✅ Enforced | ❌ | ❌ | ❌ |
| **Drift prevention** | ✅ Enforced | ❌ | ❌ | ❌ |
| **Context-window proof** | ✅ File-based | ⚠️ Partial | ❌ | ❌ |
| **Autonomous multi-phase** | ✅ Built-in | ❌ | ⚠️ Complex | ❌ |
| **Language-agnostic** | ✅ Protocol | ✅ | ❌ Python | ✅ |
| **Setup time** | 5 min | 2 min | 30 min | 0 min |
| **Overnight execution** | ✅ Proven | ❌ | ⚠️ Possible | ❌ |

**Unique position:** Only solution that enforces quality gates + prevents drift + works autonomously across context windows.

## What Gets Enforced

**Implemented gates:**

| Gate | What It Checks | Example |
|------|----------------|---------|
| **protocol_lock** | Protocol integrity | SHA256 verify `tools/judge.py` unchanged |
| **tests** | Test suite passes | `pytest` exit code must be 0 |
| **lint** | Static analysis | `ruff check .` exit code must be 0 |
| **docs** | Files updated | `README.md` must be modified |
| **drift** | Scope boundaries | Only `src/mvp/**` can change |
| **llm_review** | Semantic quality | Claude reviews architecture |

**Test scoping (Phase 2.5):**
- `test_scope: "scope"` - Only run tests matching phase scope (fast, focused)
- `quarantine: [...]` - Skip specific tests with documented reasons (flaky APIs, legacy tests)

Gates are configurable per phase. Enforce what matters for your project.

## Core Workflow

```
1. Claude reads brief (.repo/briefs/P01-scaffold.md)
2. Claude implements files within scope
3. Claude runs: ./tools/phasectl.py review P01-scaffold
   ├─> Shows diff summary (in-scope vs out-of-scope)
   ├─> Runs tests
   ├─> Invokes judge
   └─> Judge checks all gates
4. Judge writes:
   ├─> .repo/critiques/P01-scaffold.md (if issues)
   └─> .repo/critiques/P01-scaffold.OK (if approved)
5. If approved: ./tools/phasectl.py next → advance
   If critique: fix issues → re-run review
```

**The key:** Judge blocks until quality standards met. Agent iterates automatically.

## Real-World Usage

**Scenario:** 6-phase backend refactor

**Setup (you):**
- Write `.repo/plan.yaml` with 6 phases
- Write 6 briefs describing what to build
- Define scope + gates for each phase

**Execution (Claude Code):**
- Reads P01 brief
- Implements changes
- Submits review, gets critique, fixes, re-submits, approved
- Advances to P02
- Repeats for all 6 phases

**Result:** Wake up to completed refactor, all tests passing, docs updated, no drift.

## File Structure

```
judge-gated-orchestrator/
├── .repo/
│   ├── briefs/           # Phase instructions
│   │   ├── CURRENT.json  # → Points to active phase
│   │   ├── P01-scaffold.md
│   │   └── P02-impl-feature.md
│   ├── critiques/        # Judge feedback
│   │   ├── P01-scaffold.OK (approved)
│   │   └── P02-impl-feature.md (needs fixes)
│   ├── traces/           # Test output
│   ├── plan.yaml         # Roadmap + gates
│   └── protocol_manifest.json  # SHA256 hashes for integrity
├── tools/
│   ├── phasectl.py       # Controller (review/next)
│   ├── judge.py          # Gate validator
│   ├── llm_judge.py      # Optional LLM review
│   ├── generate_manifest.py  # Update protocol hashes
│   └── lib/              # Shared utilities + protocol guard
├── orient.sh             # Status in 10 seconds
└── README.md             # This file
```

## Documentation Guide

### For Humans 👤

Start here if you're setting up or using the protocol:

1. **README.md** (this file) - Overview, philosophy, and why this exists
2. **GETTING_STARTED.md** - Practical guide from zero to running autonomous execution
   - Installation and demo
   - Setting up your project
   - Planning your roadmap
   - Executing phases with Claude
   - Troubleshooting and tips

### For AI Assistants 🤖

**Planning mode** (collaborative roadmap creation):
- **LLM_PLANNING.md** - Complete guide for helping humans design phases, scope, and gates
- Use this when: Human says "help me create a plan.yaml" or "let's break this project into phases"

**Execution mode** (autonomous phase implementation):
- **PROTOCOL.md** - Execution manual with file specs, commands, gates, and error handling
- Use this when: Human says "execute the current phase" or "read PROTOCOL.md and start working"

### For Validation 🧪

- **TESTME.md** - 12 tests to validate protocol implementation (25-30 minutes)

### Navigation

| Audience | Goal | Read This |
|----------|------|-----------|
| Human setting up | Understand what this is | README.md |
| Human using it | Learn how to use | GETTING_STARTED.md |
| AI planning roadmap | Help create plan.yaml | LLM_PLANNING.md |
| AI executing phases | Implement within gates | PROTOCOL.md |
| Anyone validating | Verify it works | TESTME.md |

## Next Steps

**New here?** Read `GETTING_STARTED.md` for a step-by-step guide.

**Ready to use it?** Point Claude at `LLM_PLANNING.md` to design your roadmap.

**Want to validate?** Follow `TESTME.md` (12 tests, 25-30 minutes).

**Integrating with CI/CD?** The protocol is just files + shell commands:
```bash
./tools/phasectl.py review $PHASE_ID
if [ $? -eq 0 ]; then
  echo "Phase approved"
  ./tools/phasectl.py next
fi
```

## Philosophy

**This is a protocol, not a framework.**

You don't install it, you follow it. You don't import classes, you write files that match the conventions. You don't learn an API, you run shell commands.

Like Git doesn't tell you how to write code—just how to track changes—this protocol doesn't tell you what to build, just how to enforce quality during autonomous execution.

**The protocol is the spec. This repo is one way to implement it.**

## Get Started

```bash
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt
./orient.sh
```

Then read `PROTOCOL.md` to start working.

## License

MIT

===============================================================================
DOCUMENTATION FOR HUMANS 👤
===============================================================================

--- GETTING_STARTED.md ---

# Getting Started Guide

**Audience:** Human developers setting up and using the gated phase protocol

**Goal:** Get you from zero to running autonomous multi-phase development in 30 minutes

---

## Quick Start (5 Minutes)

### 1. Install

```bash
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt
```

**Requirements:**
- Python 3.8+
- Git
- Your preferred AI coding assistant (Claude Code, Cursor, Windsurf, etc.)

### 2. Try the Demo

```bash
# See current status
./orient.sh

# Try review flow with existing phases
./tools/phasectl.py review P02-impl-feature
```

**What you'll see:**
- Diff summary showing in-scope vs out-of-scope changes
- Test execution
- Judge verdict (approval or critique)

This demo runs on the example phases included in `.repo/plan.yaml`.

### 3. Understand the Structure

```bash
# View the roadmap
cat .repo/plan.yaml

# Read a phase brief
cat .repo/briefs/P01-scaffold.md

# Check critique status
ls .repo/critiques/
```

**Key insight:** Everything is files. No hidden state, no databases, just files in `.repo/`.

---

## Setting Up Your Own Project

### Step 1: Initialize Your Repo

**Option A - New project:**
```bash
mkdir my-project
cd my-project
git init
pip install -r /path/to/judge-gated-orchestrator/requirements.txt
```

**Option B - Existing project:**
```bash
cd my-existing-project
pip install -r /path/to/judge-gated-orchestrator/requirements.txt
```

Copy protocol files:
```bash
# Copy tools
cp -r /path/to/judge-gated-orchestrator/tools ./

# Copy orientation script
cp /path/to/judge-gated-orchestrator/orient.sh ./

# Create .repo structure
mkdir -p .repo/briefs .repo/critiques .repo/traces
```

### Step 2: Create Your .gitignore

```bash
cat >> .gitignore <<EOF
# Protocol traces (don't commit test output)
.repo/traces/

# Python
__pycache__/
*.pyc
.pytest_cache/

# Environment
.env
venv/
EOF
```

### Step 3: Copy Protocol Manifest

```bash
cp /path/to/judge-gated-orchestrator/.repo/protocol_manifest.json .repo/
```

This file contains SHA256 hashes that prevent autonomous agents from modifying judge logic.

---

## Planning Your Roadmap

**Key insight:** Planning is collaborative. You work WITH Claude/your AI assistant to break your project into phases.

### Step 1: Understand What Makes a Good Phase

**Good phases are:**
- ✅ 1-3 days of work
- ✅ Single feature or module
- ✅ Clear, testable deliverable
- ✅ Independent from other phases

**Bad phases are:**
- ❌ "Implement entire backend" (too broad)
- ❌ "Fix typo" (too narrow)
- ❌ "Refactor everything" (unclear scope)

### Step 2: Start a Planning Conversation

Point your AI assistant at this prompt:

```
Read LLM_PLANNING.md and help me create a plan.yaml for my project.

My project is: [describe your project]

I want to: [describe your goal]

Let's break this into phases with proper scope and gates.
```

**What happens:**
1. AI reads LLM_PLANNING.md (planning guide for LLMs)
2. AI proposes phases based on your goal
3. You iterate together
4. AI generates plan.yaml
5. AI writes phase briefs

**Example conversation:**

> **You:** "Read LLM_PLANNING.md and help me plan. I'm building a REST API for a todo app. I want authentication, CRUD endpoints, and tests."

> **AI:** "I'll help break this into phases. Based on best practices, I suggest:
> - P01: Scaffold (project structure, dependencies)
> - P02: Authentication (JWT middleware, login endpoint)
> - P03: Todo CRUD (create, read, update, delete endpoints)
> - P04: Integration tests (end-to-end test suite)
>
> Each phase is 1-2 days. Should I generate the plan.yaml?"

> **You:** "Yes, and make sure tests are required for each phase."

> **AI:** [Generates plan.yaml with tests gate enabled for all phases]

### Step 3: Review Generated Files

AI will create:
- `.repo/plan.yaml` - Roadmap with phases, scopes, gates
- `.repo/briefs/P01-*.md` - Detailed instructions for phase 1
- `.repo/briefs/P02-*.md` - Instructions for phase 2
- etc.

**Review checklist:**
- [ ] Phases are properly scoped (1-3 days each)
- [ ] Scope patterns are specific enough
- [ ] Gates make sense for each phase
- [ ] Briefs have clear objectives and steps

### Step 4: Initialize Phase 1

Create `.repo/briefs/CURRENT.json`:

```json
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": 1760223767.0
}
```

Or use this shortcut:
```bash
echo '{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": '$(date +%s.%N)'
}' > .repo/briefs/CURRENT.json
```

**You're now ready for autonomous execution!**

---

## Executing Phases with Claude

### Handoff to Autonomous Mode

Point your AI assistant at this prompt:

```
Read PROTOCOL.md and execute the current phase.

Start with: ./orient.sh
```

**What happens:**
1. AI reads PROTOCOL.md (execution manual)
2. AI runs `./orient.sh` to see current state
3. AI reads phase brief
4. AI implements changes within scope
5. AI submits for review
6. AI handles critiques and re-submits
7. AI advances to next phase when approved
8. Repeat

### What You Do During Execution

**Minimal supervision mode:**
- Check progress occasionally
- Review critiques if AI gets stuck
- Approve advancement to next phase (optional)

**Active collaboration mode:**
- Review each critique as it's generated
- Provide guidance on ambiguous decisions
- Adjust scope if needed

### Monitoring Progress

```bash
# Quick status check
./orient.sh

# See all critiques
ls .repo/critiques/

# Check current phase
cat .repo/briefs/CURRENT.json

# See latest test results
cat .repo/traces/last_test.txt
```

---

## Common Workflows

### Workflow 1: Overnight Autonomous Execution

**Setup (5pm):**
```bash
# Verify current state
./orient.sh

# Give Claude the handoff prompt
# "Read PROTOCOL.md and execute all remaining phases. Work through critiques autonomously."
```

**Check-in (9am next day):**
```bash
./orient.sh
# See how many phases completed

ls .repo/critiques/
# Check for any stuck critiques
```

**Typical overnight progress:** 2-4 phases completed, all tests passing, docs updated.

---

### Workflow 2: Collaborative Phase-by-Phase

**For each phase:**

1. **Review the brief together:**
   ```bash
   cat .repo/briefs/<phase-id>.md
   ```
   Discuss scope, clarify ambiguities

2. **Let Claude implement:**
   ```
   "Implement this phase following PROTOCOL.md"
   ```

3. **Review together:**
   ```bash
   ./tools/phasectl.py review <phase-id>
   ```
   Check diff summary, read critique if any

4. **Advance when ready:**
   ```bash
   ./tools/phasectl.py next
   ```

**Typical pace:** 1-2 phases per hour

---

### Workflow 3: High-Stakes with LLM Review

Enable LLM review gate for critical phases:

```yaml
gates:
  llm_review: { enabled: true }
```

**Requires:**
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

**What it does:**
- Claude reviews all changed files
- Checks for architecture issues, bugs, anti-patterns
- Blocks approval if issues found
- Adds ~$0.01-0.10 per review

**Use for:**
- Security-sensitive code
- Database migrations
- API contract changes
- Production deployments

---

## Troubleshooting

### Problem: AI Keeps Hitting Drift Errors

**Symptom:** Review fails with "Out-of-scope changes detected"

**Common causes:**
1. Scope patterns too narrow
2. AI misunderstanding scope boundaries
3. Legitimate need for broader scope

**Fix:**

**Option 1 - Clarify scope in brief:**
Edit `.repo/briefs/<phase-id>.md` and make scope crystal clear:
```markdown
## Scope 🎯
✅ YOU MAY TOUCH: src/auth/**, tests/auth/**
❌ DO NOT TOUCH: Everything else
🤔 IF YOU NEED DATABASE CHANGES: Stop and ask
```

**Option 2 - Expand scope in plan.yaml:**
```yaml
scope:
  include: ["src/auth/**", "tests/auth/**", "src/models/user.py"]
```

**Option 3 - Split into more phases:**
Create separate phases for related work.

---

### Problem: Tests Keep Failing

**Symptom:** Review blocked on "Tests failed with exit code 1"

**Debug:**
```bash
# Read full test output
cat .repo/traces/last_test.txt

# Run tests manually
pytest tests/ -v

# Run specific failing test
pytest tests/test_auth.py::test_login -v
```

**Common issues:**
1. **Missing dependencies** - Check requirements.txt
2. **Wrong test scope** - Use `test_scope: "scope"` to run only relevant tests
3. **Flaky external tests** - Use `quarantine` to skip temporarily

**Quarantine example:**
```yaml
gates:
  tests:
    must_pass: true
    quarantine:
      - path: "tests/test_external_api.py::test_timeout"
        reason: "External API occasionally times out, unrelated to this phase"
```

---

### Problem: AI Lost Track (Context Window Exhausted)

**Symptom:** AI says "I don't remember where we are"

**Fix:**
```
Run: ./orient.sh

This will show you current phase, status, and next steps.
All state is in files - you can always recover.
```

**The protocol is context-window proof.** Everything needed is in `.repo/` files.

---

### Problem: Need to Modify Protocol Files

**Symptom:** "Protocol file modified: tools/judge.py"

**Fix:**

**You can't modify protocol files during normal phases.** This is intentional (prevents AI from disabling gates).

**To make protocol changes:**

1. Complete current phase
2. Create protocol maintenance phase:
   ```yaml
   phases:
     - id: P00-protocol-maintenance
       description: "Update judge to add custom gate"
       scope:
         include: ["tools/**", ".repo/protocol_manifest.json"]
       gates:
         tests: { must_pass: true }
   ```
3. Make changes within that phase
4. Update hashes: `./tools/generate_manifest.py`
5. Complete maintenance phase
6. Resume normal phases

---

### Problem: Judge Itself Has a Bug

**If you find a bug in judge.py, phasectl.py, or lib/:**

1. Report it: https://github.com/PM-Frontier-Labs/judge-gated-orchestrator/issues
2. Fork and fix if urgent
3. Use protocol maintenance phase to apply fix
4. Regenerate manifest: `./tools/generate_manifest.py`

**The protocol encourages forking.** It's a spec, not a framework - rewrite it in Bash if you want!

---

## Advanced Configuration

### Custom Test/Lint Commands

```yaml
plan:
  test_command: "python -m pytest tests/ -v --tb=short"
  lint_command: "pylint src/"
```

### Per-Phase Test Scoping

Only run tests matching phase scope (faster):
```yaml
gates:
  tests:
    must_pass: true
    test_scope: "scope"  # Only run tests/mvp/** if scope includes that
```

### Forbidden Files

Block changes to critical files:
```yaml
drift_rules:
  forbid_changes:
    - "requirements.txt"
    - "pyproject.toml"
    - ".github/workflows/**"
```

### Artifacts Validation

Ensure files exist after phase:
```yaml
artifacts:
  must_exist:
    - "src/auth/middleware.py"
    - "tests/test_auth.py"
    - "docs/authentication.md"
```

---

## Tips for Success

### 1. Start with Small Phases

**First project?** Use 1-day phases maximum. Better to have 10 small phases than 3 large ones.

### 2. Write Clear Briefs

**Good brief:**
```markdown
## Objective
Implement JWT-based authentication middleware.

## Scope 🎯
✅ YOU MAY TOUCH: src/auth/**, tests/auth/**
❌ DO NOT TOUCH: src/api/** (endpoints come in next phase)

## Implementation Steps
1. Create src/auth/jwt.py with encode/decode functions
2. Create src/auth/middleware.py with @require_auth decorator
3. Add tests in tests/auth/test_jwt.py
4. Update docs/authentication.md
```

**Bad brief:**
```markdown
## Objective
Add auth

## Scope
Auth files
```

### 3. Test the Gates Early

Before starting a long roadmap, test that gates work:
```bash
# Make a small change
touch test_file.py

# Try review (should fail - out of scope)
./tools/phasectl.py review P01-scaffold

# Verify judge catches it
```

### 4. Use LLM Review Strategically

Don't enable for every phase (expensive). Use it for:
- First phase of new module (validate architecture)
- Last phase before production (final check)
- High-risk changes (auth, payments, migrations)

### 5. Commit After Each Phase

```bash
# After phase approved and advanced
git add .
git commit -m "Complete P01-scaffold

- Created project structure
- Added initial tests
- Updated documentation

Phase approved by judge at 2025-01-15T10:30:00"
```

Gives you clean rollback points.

---

## Next Steps

### You're Ready When:

- [ ] You've tried the demo
- [ ] You understand phases, scope, and gates
- [ ] You've created (or plan to create) your plan.yaml
- [ ] You know how to handoff to Claude

### Now Go Build:

1. **Plan your roadmap** with Claude using `LLM_PLANNING.md`
2. **Execute phases** with Claude using `PROTOCOL.md`
3. **Monitor progress** with `./orient.sh`
4. **Ship quality code** with confidence

---

## Getting Help

**Documentation:**
- `README.md` - Overview and philosophy
- `LLM_PLANNING.md` - Planning guide (for Claude)
- `PROTOCOL.md` - Execution manual (for Claude)
- `TESTME.md` - Validation guide (12 tests)

**Quick commands:**
```bash
./orient.sh              # Current status
./tools/phasectl.py -h   # Command help
cat .repo/plan.yaml      # View roadmap
```

**Issues and feedback:**
https://github.com/PM-Frontier-Labs/judge-gated-orchestrator/issues

**Philosophy:**
This is a protocol, not a framework. Fork it, rewrite it, extend it. The spec is in the files, the implementation is just one way to follow that spec.

---

**Welcome to autonomous multi-phase development with quality guarantees.**

**Happy building!** 🚀

--- TESTME.md ---

# Gated Phase Protocol - Testing Guide

**Audience:** Evaluators, contributors, QA engineers

**Purpose:** Validate the protocol implementation works correctly

**Time:** 25-30 minutes for full validation (includes Phase 1 + Phase 2.5 enhancements)

**Note:** Tests 10-12 validate Phase 1 (baseline SHA, globstar patterns) and Phase 2.5 (test scoping, quarantine)

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
- [ ] Baseline SHA provides stable diffs throughout phase
- [ ] Tests gate catches test failures
- [ ] Test scoping filters tests to phase scope (Phase 2.5)
- [ ] Test quarantine skips specific tests with reasons (Phase 2.5)
- [ ] Docs gate catches missing documentation AND verifies actual changes
- [ ] Drift gate catches out-of-scope changes
- [ ] Drift gate respects include/exclude patterns with proper globstar support
- [ ] Forbidden files are blocked
- [ ] LLM review works when enabled (optional) and reviews all changes

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

1. ✅ All 12 tests pass without modification (including Phase 1+2.5 enhancements)
2. ✅ Full system test completes successfully
3. ✅ Validation checklist 100% checked
4. ✅ Error handling graceful for all error conditions
5. ✅ Context recovery works from any state
6. ✅ Protocol integrity prevents agent self-modification
7. ✅ Baseline SHA provides stable diffs (Test 10)
8. ✅ Globstar pattern matching works correctly (Test 11)
9. ✅ Test scoping and quarantine work correctly (Test 12)

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

**Time to complete:** 25-30 minutes for full validation (includes Phase 1 + Phase 2.5 tests)

**Difficulty:** Beginner (just follow steps)

**Result:** Confidence the protocol works as documented, including Phase 1 + Phase 2.5 enhancements

===============================================================================
DOCUMENTATION FOR AI ASSISTANTS 🤖
===============================================================================

--- LLM_PLANNING.md (Planning Mode - Collaborative Roadmap Design) ---

# LLM Planning Guide - Judge-Gated Protocol

**READ THIS WHEN:** Helping a human plan a multi-phase roadmap
**DON'T READ WHEN:** Executing work within an already-planned project (read PROTOCOL.md instead)

**Purpose:** This guide teaches you how to create effective `plan.yaml` files and phase briefs for autonomous execution.

---

## Quick Start

You're helping a human break their project into phases with quality gates. Here's the flow:

1. **Understand their goal** - What are they building?
2. **Propose phases** - Break work into 1-3 day increments
3. **Define scope** - What files can change in each phase?
4. **Choose gates** - What quality checks make sense?
5. **Write plan.yaml** - Formalize the roadmap
6. **Write briefs** - Detailed instructions for each phase
7. **Initialize** - Create CURRENT.json for phase 1
8. **Handoff** - Tell them to point you at PROTOCOL.md for execution

**After planning is done, you'll switch modes and read PROTOCOL.md for execution.**

---

## Phase Design Principles

### Size: 1-3 Days of Work

**Good phases:**
- ✅ Single feature or module
- ✅ Clear deliverable
- ✅ Independently testable
- ✅ 100-300 lines of code typically

**Bad phases:**
- ❌ "Implement entire backend" (too broad)
- ❌ "Add semicolon to line 42" (too narrow)
- ❌ Multiple unrelated features
- ❌ Work spanning 1+ weeks

### Testability: Every Phase Must Be Verifiable

**Each phase should:**
- Have tests that prove it works
- Create artifacts that can be checked
- Produce docs that can be reviewed

**If you can't test it, split it:**
- "Design auth system" → Not testable (too vague)
- "Implement JWT login endpoint" → Testable ✅

### Scope: Clear Boundaries

**Good scope patterns:**
```yaml
# Focused on one module
include: ["src/auth/**", "tests/auth/**", "docs/auth.md"]

# Multiple related files
include: ["migrations/001_*.sql", "src/models/user.py"]

# Wildcard for new features
include: ["src/features/payments/**"]
```

**Bad scope patterns:**
```yaml
# Too broad
include: ["src/**"]  # Everything!

# Too vague
include: ["*.py"]  # Which Python files?

# No tests
include: ["src/auth/**"]  # Where are tests?
```

### Dependencies: Sequential Phases

**Phases run sequentially, so order matters:**

```yaml
phases:
  - id: P01-database-schema
    # Must come first

  - id: P02-api-endpoints
    # Depends on P01 being done

  - id: P03-frontend
    # Depends on P02 being done
```

**Can't parallelize** - If human needs parallel work, they should use separate branches.

---

## plan.yaml Schema

### Complete Template

```yaml
plan:
  # Required fields
  id: PROJECT-ID                           # Uppercase, hyphens (e.g., MY-API)
  summary: "What you're building"          # 1 sentence

  # Optional configuration
  base_branch: "main"                      # Branch to diff against (default: "main")
  test_command: "pytest tests/ -v"         # How to run tests (default: "pytest tests/ -v")
  lint_command: "ruff check ."             # How to run linter (default: "ruff check .")

  # LLM review configuration (optional)
  llm_review_config:
    model: "claude-sonnet-4-20250514"      # Model to use
    max_tokens: 2000                       # Response length
    temperature: 0                         # Randomness (0 = deterministic)
    timeout_seconds: 60                    # API timeout
    budget_usd: null                       # Cost limit (null = unlimited)
    fail_on_transport_error: false         # Block on API errors?
    include_extensions: [".py"]            # File types to review
    exclude_patterns: []                   # Skip patterns

  # Protocol integrity (rarely modified)
  protocol_lock:
    protected_globs:
      - "tools/**"
      - ".repo/plan.yaml"
      - ".repo/protocol_manifest.json"
    allow_in_phases:
      - "P00-protocol-maintenance"

  # Phase definitions
  phases:
    - id: P01-phase-name                   # Must be unique
      description: "What this accomplishes" # 1 sentence, actionable

      # Scope: What files can change
      scope:
        include: ["src/module/**", "tests/module/**"]  # Glob patterns
        exclude: ["src/**/legacy/**"]                  # Optional exclusions

      # Artifacts: Files that must exist after phase
      artifacts:
        must_exist: ["src/module/file.py", "tests/test_file.py"]

      # Gates: Quality checks
      gates:
        tests:
          must_pass: true                  # Required
          test_scope: "scope"              # "scope" | "all" (default: "all")
          quarantine: []                   # Optional: skip specific tests

        lint:
          must_pass: true                  # Optional gate

        docs:
          must_update: ["docs/module.md"]  # Files that must change

        drift:
          allowed_out_of_scope_changes: 0  # How many files can be out of scope

        llm_review:
          enabled: false                   # Optional LLM code review

      # Drift rules: Absolute restrictions
      drift_rules:
        forbid_changes: ["requirements.txt", "package.json"]  # Never touch these
```

### Field Reference

**plan.id** - Project identifier (uppercase, hyphens)

**plan.summary** - One sentence describing the project

**plan.base_branch** - Branch for git diffs (default: "main")

**plan.test_command** - Command to run tests
- Python: `"pytest tests/ -v"`
- Node: `"npm test"`
- Rust: `"cargo test"`
- Go: `"go test ./..."`

**plan.lint_command** - Command to run linter
- Python: `"ruff check ."` or `"flake8 ."`
- Node: `"eslint ."` or `"npm run lint"`
- Rust: `"cargo clippy"`

**phases[].id** - Unique phase identifier (e.g., P01-setup, P02-feature)

**phases[].scope.include** - Glob patterns for allowed files
- Use `**` for recursive: `"src/**/*.py"` matches nested files
- Multiple patterns: `["src/auth/**", "tests/auth/**"]`

**phases[].scope.exclude** - Patterns to exclude from include
- Example: `["src/**/test_*.py"]` excludes test files from src

**phases[].gates.tests.test_scope**
- `"scope"` - Run only tests matching scope.include (fast, focused)
- `"all"` - Run entire test suite (comprehensive)

**phases[].gates.tests.quarantine** - Skip specific tests
```yaml
quarantine:
  - path: "tests/test_flaky.py::test_timeout"
    reason: "External API timeout, tracked in issue #123"
```

**phases[].drift_rules.forbid_changes** - Files requiring dedicated phases
- Dependencies: `["requirements.txt", "package.json", "Cargo.toml"]`
- CI: `[".github/**", ".circleci/**"]`
- Migrations: `["migrations/**"]` (if you want separate migration phases)

---

## Gate Selection Guide

### When to Use Each Gate

#### tests: { must_pass: true }
**Always use** - Every phase should have tests

**test_scope: "scope"** when:
- Large codebase (100+ tests)
- Isolated module work
- Fast feedback loop desired
- Legacy tests exist elsewhere

**test_scope: "all"** when:
- Small codebase (<50 tests)
- Integration phase
- Breaking changes possible
- Final validation before release

**quarantine** when:
- Flaky external API tests
- Deliberately breaking tests (fixing next phase)
- Legacy tests unrelated to work
- Infrastructure not yet built

#### lint: { must_pass: true }
**Use when:**
- Team has style standards
- Want consistent code formatting
- Linter already configured

**Skip when:**
- Exploratory/prototype phase
- No linter configured yet
- Would slow down too much

#### docs: { must_update: ["file.md"] }
**Use when:**
- Public API changes
- New features need documentation
- Architecture decisions made

**Specify section anchors:**
```yaml
docs:
  must_update: ["docs/api.md#authentication"]
```

**Skip when:**
- Internal refactoring
- Bug fixes with no API changes
- Docs will be batch-updated later

#### drift: { allowed_out_of_scope_changes: N }
**Start with 0** - Be strict by default

**Allow 1-2 when:**
- Small config tweaks expected
- README updates likely
- Minor refactors of nearby code

**Allow 5+ when:**
- Exploratory refactor phase
- Touch files discovered during work

**Skip entirely** (omit gate) when:
- No scope defined
- Prototyping phase

#### llm_review: { enabled: true }
**Enable for:**
- Security-critical code (auth, encryption)
- Complex algorithms
- Public APIs
- Money/payment handling
- Untrusted input processing

**Skip for:**
- Boilerplate code
- Configuration files
- Test files
- Simple CRUD operations
- Cost-sensitive projects

---

## Scope Patterns Cookbook

### Common Patterns

#### Pattern: New Feature Module
```yaml
scope:
  include:
    - "src/features/payments/**"
    - "tests/features/payments/**"
    - "docs/features/payments.md"
```

#### Pattern: Database Schema
```yaml
scope:
  include:
    - "migrations/001_*.sql"
    - "src/models/user.py"
    - "tests/models/test_user.py"
```

#### Pattern: API Endpoints
```yaml
scope:
  include:
    - "src/api/routes/auth.py"
    - "tests/api/test_auth.py"
    - "docs/api.md#authentication"
```

#### Pattern: Refactoring
```yaml
scope:
  include:
    - "src/legacy/module/**"
    - "src/new/module/**"
    - "tests/module/**"
  exclude:
    - "src/legacy/module/deprecated/**"
```

#### Pattern: Configuration
```yaml
scope:
  include:
    - "config/**"
    - ".env.example"
    - "docs/configuration.md"
```

#### Pattern: Integration Tests
```yaml
scope:
  include:
    - "tests/integration/**"
gates:
  tests:
    test_scope: "all"  # Run everything for integration
```

### Anti-Patterns to Avoid

#### ❌ Too Broad
```yaml
# BAD - Everything can change
scope:
  include: ["**"]
```

#### ❌ No Tests
```yaml
# BAD - Where are the tests?
scope:
  include: ["src/auth/**"]
```

#### ❌ Vague Wildcards
```yaml
# BAD - Which files exactly?
scope:
  include: ["*.py", "*.js"]
```

#### ❌ Cross-Module
```yaml
# BAD - Too many unrelated things
scope:
  include: ["src/auth/**", "src/payments/**", "src/notifications/**"]
```

#### ❌ Incorrect Globstar
```yaml
# BAD - Single * doesn't match nested paths
scope:
  include: ["src/*/auth.py"]  # Won't match src/module/submodule/auth.py
# GOOD - Use ** for recursive
  include: ["src/**/auth.py"]
```

---

## Phase Templates

### Template 1: Setup/Scaffold Phase

**Use when:** Starting a new module from scratch

```yaml
- id: P01-scaffold-auth
  description: "Create authentication module skeleton"

  scope:
    include:
      - "src/auth/**"
      - "tests/auth/**"
      - "docs/auth.md"

  artifacts:
    must_exist:
      - "src/auth/__init__.py"
      - "tests/auth/test_login.py"
      - "docs/auth.md"

  gates:
    tests:
      must_pass: true
      test_scope: "scope"
    docs:
      must_update: ["docs/auth.md"]
    drift:
      allowed_out_of_scope_changes: 0
```

**Brief template:**
```markdown
# Phase P01: Scaffold Auth Module

## Objective
Create basic structure for authentication module with placeholder tests

## Scope 🎯
✅ YOU MAY CREATE:
- src/auth/__init__.py
- src/auth/models.py (placeholder)
- tests/auth/test_login.py (one golden test)
- docs/auth.md (architecture plan)

❌ DO NOT TOUCH:
- Existing auth code (if any)
- API routes (separate phase)

## Required Artifacts
- [ ] src/auth/__init__.py - Module initialization
- [ ] tests/auth/test_login.py - At least one passing test
- [ ] docs/auth.md - Architecture overview

## Gates
- Tests: Must pass (even if minimal)
- Docs: auth.md must be created
- Drift: No out-of-scope changes

## Implementation Steps
1. Create directory structure
2. Add __init__.py with placeholder
3. Write one golden test (assert True or similar)
4. Document planned architecture in auth.md
```

### Template 2: Feature Implementation

**Use when:** Building actual functionality

```yaml
- id: P02-implement-jwt-login
  description: "Implement JWT-based login endpoint"

  scope:
    include:
      - "src/auth/jwt.py"
      - "src/auth/login.py"
      - "src/api/routes/auth.py"
      - "tests/auth/test_jwt.py"
      - "tests/api/test_auth_routes.py"
      - "docs/auth.md"

  artifacts:
    must_exist:
      - "src/auth/jwt.py"
      - "src/auth/login.py"
      - "tests/auth/test_jwt.py"

  gates:
    tests:
      must_pass: true
      test_scope: "scope"
    lint:
      must_pass: true
    docs:
      must_update: ["docs/auth.md#jwt-implementation"]
    llm_review:
      enabled: true  # Security-critical code
    drift:
      allowed_out_of_scope_changes: 0

  drift_rules:
    forbid_changes: ["requirements.txt"]  # No new dependencies yet
```

### Template 3: Refactoring Phase

**Use when:** Improving existing code without changing behavior

```yaml
- id: P03-refactor-auth-separation
  description: "Separate auth logic from API routes"

  scope:
    include:
      - "src/auth/**"
      - "src/api/routes/auth.py"
      - "tests/auth/**"
      - "tests/api/test_auth_routes.py"

  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Run everything - refactors can break things
    lint:
      must_pass: true
    drift:
      allowed_out_of_scope_changes: 2  # Might touch nearby files
```

### Template 4: Integration Phase

**Use when:** Connecting multiple modules

```yaml
- id: P04-integrate-auth-api
  description: "Wire auth module to API endpoints"

  scope:
    include:
      - "src/api/middleware/auth.py"
      - "src/api/routes/**"
      - "tests/integration/test_auth_flow.py"
      - "docs/api.md"

  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Integration needs full suite
    docs:
      must_update: ["docs/api.md#authentication"]
    drift:
      allowed_out_of_scope_changes: 1
```

### Template 5: Dependencies Phase

**Use when:** Adding/updating external dependencies

```yaml
- id: P05-add-auth-dependencies
  description: "Add PyJWT and cryptography libraries"

  scope:
    include:
      - "requirements.txt"
      - "docs/dependencies.md"

  artifacts:
    must_exist:
      - "requirements.txt"

  gates:
    tests:
      must_pass: true
      test_scope: "all"  # Make sure nothing breaks
    docs:
      must_update: ["docs/dependencies.md"]
    drift:
      allowed_out_of_scope_changes: 0

  drift_rules:
    forbid_changes: []  # This phase CAN touch requirements.txt
```

### Template 6: Documentation Phase

**Use when:** Batch-updating docs after multiple features

```yaml
- id: P06-document-auth-system
  description: "Comprehensive auth documentation"

  scope:
    include:
      - "docs/auth/**"
      - "README.md"
      - "docs/api.md"

  artifacts:
    must_exist:
      - "docs/auth/overview.md"
      - "docs/auth/api-reference.md"

  gates:
    docs:
      must_update: ["docs/auth/overview.md", "README.md"]
    drift:
      allowed_out_of_scope_changes: 0
```

---

## Planning Conversation Flow

### Step 1: Understand the Project

**Ask the human:**
- What are you building?
- What's the end goal?
- What's already built vs new?
- Any constraints (timeline, dependencies, tech stack)?

### Step 2: Propose High-Level Phases

**Break work into logical chunks:**

```
Example: "Build a REST API with auth"

Phases:
1. Database schema (users, sessions)
2. Auth module (JWT, login/logout)
3. API endpoints (CRUD)
4. Integration tests
5. Documentation
```

**Validate with human before proceeding.**

### Step 3: Define Each Phase in Detail

For each phase, discuss:
- **Scope:** Which files?
- **Artifacts:** What must exist?
- **Gates:** Which checks?
- **Dependencies:** What must be done first?

### Step 4: Write plan.yaml

Create the formal roadmap with all phases.

### Step 5: Write Briefs

For each phase, create `.repo/briefs/PXX-name.md` with:
- Objective (what to accomplish)
- Scope (files you may/may not touch)
- Required artifacts
- Gates
- Implementation steps

### Step 6: Initialize

Create `.repo/briefs/CURRENT.json`:
```json
{
  "phase_id": "P01-first-phase",
  "brief_path": ".repo/briefs/P01-first-phase.md",
  "status": "active",
  "started_at": 1234567890
}
```

### Step 7: Handoff to Execution

Tell the human:
```
"Planning complete! Now point me at PROTOCOL.md and I'll execute
autonomously. Run ./orient.sh to see the current phase, then tell
me to read PROTOCOL.md and start working."
```

---

## Example Planning Session

**Human:** "Help me plan a REST API for a blog"

**You (LLM):** "Great! Let me understand the scope:
- What features? (posts, comments, auth, etc.)
- What's your tech stack? (Python/Flask, Node/Express, etc.)
- Starting from scratch or adding to existing code?
- Any existing database or schema?"

**Human:** "Python/FastAPI, from scratch. Features: users, posts, comments. No auth yet."

**You:** "Perfect. I'd break this into 5 phases:

1. **P01-database-schema**: SQLAlchemy models (users, posts, comments)
2. **P02-api-users**: User CRUD endpoints
3. **P03-api-posts**: Post CRUD endpoints + user relationship
4. **P04-api-comments**: Comment endpoints + post relationship
5. **P05-integration-tests**: End-to-end API tests

Does this order make sense? Any constraints?"

**Human:** "Looks good, let's do it."

**You:** "I'll create plan.yaml now..."

*(Create plan.yaml with all 5 phases, then briefs for each)*

**You:** "Done! Created:
- `.repo/plan.yaml` with all 5 phases
- `.repo/briefs/P01-database-schema.md` through P05
- `.repo/briefs/CURRENT.json` pointing to P01

Next: Tell me to read PROTOCOL.md and I'll start executing P01 autonomously."

---

## Quick Reference

### Good Phase Checklist
- [ ] 1-3 days of work
- [ ] Single focus (one feature/module)
- [ ] Clear scope (specific files)
- [ ] Testable (can verify it works)
- [ ] Artifacts defined (must_exist files)
- [ ] Appropriate gates (tests at minimum)

### Common Mistakes
- ❌ Phases too large (>1 week)
- ❌ Scope too broad (src/**/*)
- ❌ No tests included
- ❌ Vague descriptions
- ❌ Missing dependencies between phases
- ❌ Forbidden files not specified

### File Naming
- **plan.yaml**: Always this name
- **Briefs**: `.repo/briefs/P01-descriptive-name.md`
- **Phase IDs**: P01, P02... (zero-padded numbers)

---

**END OF PLANNING GUIDE**

**Next step:** After plan created, read **PROTOCOL.md** for execution mode.

--- PROTOCOL.md (Execution Mode - Autonomous Phase Implementation) ---

# Gated Phase Protocol - Execution Manual

**Audience:** AI coding assistants (Claude Code, Cursor, Windsurf, etc.) executing phases autonomously

**Purpose:** Precise instructions for working within quality-gated phases

**If you're helping plan a roadmap:** Read `LLM_PLANNING.md` instead. This document is for execution only.

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

**All state lives in files.** No memory required. Recover full context anytime via `./orient.sh`.

---

## Quick Command Reference

```bash
# Recover context (run this when lost)
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

# Advance to next phase (only after approval)
./tools/phasectl.py next

# See test results
cat .repo/traces/last_test.txt

# Check diff before review
git diff --name-only HEAD
```

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
1. Revert: git checkout HEAD tools/judge.py README.md requirements.txt
2. Update phase scope in .repo/briefs/P01-scaffold.md
3. Split into separate phase

- Tests failed with exit code 1. See .repo/traces/last_test.txt

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
      "messages": ["Tests failed with exit code 1. See .repo/traces/last_test.txt"]
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

### `.repo/traces/last_test.txt`

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

**See:** `.repo/traces/last_test.txt` for details

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

---

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

---

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

**Only run this after** `.repo/critiques/<phase-id>.OK` exists.

---

## Error Handling

### Tests Failing

**Symptom:** Review fails with "Tests failed with exit code 1"

**Recovery:**
1. Read `.repo/traces/last_test.txt`
2. Find failing test in STDOUT/STDERR
3. Fix the code or test
4. Re-run `./tools/phasectl.py review <phase-id>`

---

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

---

### Forbidden Files Changed

**Symptom:** "Forbidden files changed"

**Recovery:**
```bash
git checkout HEAD requirements.txt pyproject.toml
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

===============================================================================
END OF COMPLETE DOCUMENTATION
===============================================================================

Total documentation sections:
1. README.md - Overview for all audiences
2. GETTING_STARTED.md - Human setup and usage guide
3. TESTME.md - Validation guide (12 tests)
4. LLM_PLANNING.md - AI planning mode guide
5. PROTOCOL.md - AI execution mode manual

Navigate to specific sections using search/find in your editor.
