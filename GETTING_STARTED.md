# Getting Started Guide

**Get from zero to autonomous multi-phase development in 30 minutes**

**Audience:** Human developers  
**Prerequisites:** Python 3.8+, Git, AI coding assistant (Claude Code, Cursor, etc.)

---

## Quick Start (5 Minutes)

### 1. Install

```bash
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt
```

### 2. Try the Demo

```bash
./orient.sh                                  # See current status
./tools/phasectl.py review P02-impl-feature  # Try review flow
```

**You'll see:** Diff summary, test execution, and judge verdict (approval or critique).

### 3. Understand the Structure

```bash
cat .repo/plan.yaml                  # View roadmap
cat .repo/briefs/P01-scaffold.md     # Read phase brief  
ls .repo/critiques/                  # Check critique status
```

**Key insight:** Everything is files—no hidden state, no databases.

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

**Key insight:** Planning is collaborative—work with your AI assistant to break projects into phases.

### Step 1: Understand What Makes a Good Phase

| Good Phases ✅ | Bad Phases ❌ |
|----------------|---------------|
| 1-3 days of work | "Implement entire backend" (too broad) |
| Single feature/module | "Fix typo" (too narrow) |
| Clear, testable deliverable | "Refactor everything" (unclear) |
| Independent from others | Multiple unrelated features |

### Step 2: Start a Planning Conversation

**Prompt your AI assistant:**

```
Read LLM_PLANNING.md and help me create a plan.yaml.

Project: [describe your project]
Goal: [describe your goal]

Let's break this into phases with proper scope and gates.
```

**What happens:** AI reads planning guide → proposes phases → you iterate together → generates plan.yaml + briefs

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

**Symptom:** "Out-of-scope changes detected"

**Fix options:**

1. **Clarify scope in brief** → Edit `.repo/briefs/<phase-id>.md`:
   ```markdown
   ## Scope 🎯
   ✅ YOU MAY TOUCH: src/auth/**, tests/auth/**
   ❌ DO NOT TOUCH: Everything else
   ```

2. **Expand scope** → Update `.repo/plan.yaml`:
   ```yaml
   scope:
     include: ["src/auth/**", "tests/auth/**", "src/models/user.py"]
   ```

3. **Split phase** → Create separate phases for out-of-scope work

---

### Problem: Tests Keep Failing

**Symptom:** "Tests failed with exit code 1"

**Debug steps:**
```bash
cat .repo/traces/last_test.txt              # Full output
pytest tests/ -v                             # Run manually
pytest tests/test_auth.py::test_login -v    # Specific test
```

**Common fixes:**
- Missing dependencies → Check `requirements.txt`
- Too many tests → Use `test_scope: "scope"` in plan.yaml
- Flaky tests → Use `quarantine` to skip temporarily:
  ```yaml
  quarantine:
    - path: "tests/test_external_api.py::test_timeout"
      reason: "External API timeout, non-blocking"
  ```

---

### Problem: AI Lost Track (Context Window Exhausted)

**Symptom:** AI says "I don't remember where we are"

**Fix:** Run `./orient.sh` → shows current phase, status, and next steps.

**Why it works:** All state is in files. The protocol is context-window proof.

---

### Problem: Plan Validation Failed

**Symptom:** "Plan validation failed" with error list

**Common errors and fixes:**

| Error | Fix |
|-------|-----|
| Missing required field: plan.id | Add `id: "my-project"` under `plan:` |
| must_pass must be a boolean | Change `must_pass: yes` to `must_pass: true` |
| Duplicate phase ID | Ensure unique phase IDs |
| Empty strings in scope | Remove empty patterns |

**Steps:**
```bash
nano .repo/plan.yaml                       # Edit
./tools/phasectl.py review <phase-id>      # Re-validate
```

**Prevention:** Use `LLM_PLANNING.md` when creating plan.yaml—AI assistants generate valid schemas.

---

### Problem: Could Not Acquire Judge Lock

**Symptom:** "Could not acquire judge lock"

**Cause:** Another judge process running (CI job, concurrent agent, or stale lock)

**Fix options:**

1. **Wait** → `sleep 60 && ./tools/phasectl.py review <phase-id>`
2. **Kill hung process** → `ps aux | grep judge.py`, then `kill <PID>`
3. **Remove stale lock** (last resort) → `rm .repo/.judge.lock`

**Prevention:** 
- CI: Use job concurrency limits
- Multi-agent: Coordinate reviews
- Auto-expires: Locks expire after 60 seconds

---

### Problem: Need to Modify Protocol Files

**Symptom:** "Protocol file modified: tools/judge.py"

**Why:** Can't modify protocol during normal phases (prevents AI from disabling gates)

**To make protocol changes:**
1. Complete current phase
2. Create protocol maintenance phase in plan.yaml:
   ```yaml
   - id: P00-protocol-maintenance
     scope: ["tools/**", ".repo/protocol_manifest.json"]
   ```
3. Make changes + update hashes: `./tools/generate_manifest.py`
4. Resume normal phases

---

### Problem: Judge Itself Has a Bug

**Steps:**
1. Report: https://github.com/PM-Frontier-Labs/judge-gated-orchestrator/issues
2. Fork and fix (if urgent)
3. Apply via protocol maintenance phase
4. Regenerate: `./tools/generate_manifest.py`

**Note:** The protocol is a spec, not a framework\u2014fork and rewrite in any language!

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
