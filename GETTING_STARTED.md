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

Kick off planning with your AI assistant using this prompt:

```
Help me create a .repo/plan.yaml for my project.

My project is: [describe your project]

I want to: [describe your goal]

Let's break this into phases with clear scope and quality gates.
```

**What happens:**
1. The AI proposes phases based on your goal
2. You iterate together
3. The AI generates `plan.yaml`
4. The AI writes phase briefs

**Example conversation:**

> **You:** "Help me plan. I'm building a REST API for a todo app. I want authentication, CRUD endpoints, and tests."

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

### Problem: Plan Validation Failed

**Symptom:** "Plan validation failed" with list of errors before review starts

**What this means:** plan.yaml has schema errors that must be fixed before execution

**Common validation errors:**

1. **Missing required fields:**
   ```
   Missing required field: plan.id
   ```
   Fix: Add `id: "my-project"` under `plan:` section

2. **Invalid gate configuration:**
   ```
   plan.phases[0].gates.tests.must_pass must be a boolean
   ```
   Fix: Change `must_pass: yes` to `must_pass: true`

3. **Duplicate phase IDs:**
   ```
   Duplicate phase ID: P01-scaffold
   ```
   Fix: Ensure each phase has a unique ID

4. **Invalid patterns:**
   ```
   plan.phases[0].scope.include cannot contain empty strings
   ```
   Fix: Remove empty strings from scope patterns

**How to fix:**
```bash
# Edit plan.yaml
nano .repo/plan.yaml

# Validate manually (optional - phasectl does this automatically)
python3 -c "from tools.lib.plan_validator import validate_plan_file; from pathlib import Path; errors = validate_plan_file(Path('.repo/plan.yaml')); print('Valid!' if not errors else '\n'.join(errors))"

# Try review again
./tools/phasectl.py review <phase-id>
```

**Prevention:** Use the schema and examples here when creating plan.yaml; ensure your assistant validates the file.

---

### Problem: Could Not Acquire Judge Lock

**Symptom:** "Could not acquire judge lock: Could not acquire lock on .repo/.judge.lock within 60s"

**What this means:** Another judge process is already running (CI job, concurrent agent, or crashed process)

**Common causes:**
1. **Concurrent CI jobs** - Multiple GitHub Actions running simultaneously
2. **Multi-agent scenario** - Two AI assistants trying to review at once
3. **Stale lock** - Previous judge process crashed without cleanup

**Fix:**

**Option 1 - Wait for other process:**
```bash
# Wait a minute and try again
sleep 60
./tools/phasectl.py review <phase-id>
```

**Option 2 - Check for running processes:**
```bash
# See if judge is running
ps aux | grep judge.py

# If hung process, kill it
kill <PID>

# Try review again
./tools/phasectl.py review <phase-id>
```

**Option 3 - Remove stale lock (last resort):**
```bash
# Only do this if you're CERTAIN no other judge is running
rm .repo/.judge.lock

# Try review again
./tools/phasectl.py review <phase-id>
```

**Prevention:**
- In CI: Use job concurrency limits
- With multiple agents: Coordinate who runs reviews
- File lock auto-expires stale locks after 60 seconds

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

1. **Plan your roadmap** with your AI assistant and write `plan.yaml`
2. **Execute phases** with `PROTOCOL.md`
3. **Monitor progress** with `./orient.sh`
4. **Ship quality code** with confidence

---

## Getting Help

**Documentation:**
- `README.md` - Overview and philosophy
- `PROTOCOL.md` - Execution manual (for AI assistants)

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
