# Gated Phase Protocol

**Get autonomous AI execution in 5 minutes. Works in your terminal with Claude Code, Cursor, or any AI coding assistant.**

A file-based protocol for autonomous execution with quality gates. No servers, no APIs, no framework—just clone and run.

## What Is This?

A **protocol**, not a framework. Like Git tracks code changes through file conventions (`.git/`, `HEAD`, etc.), this protocol tracks autonomous work through files:

- **`.repo/briefs/CURRENT.json`** - Points to current phase
- **`.repo/plan.yaml`** - Defines phases and quality gates
- **`.repo/critiques/<phase>.{md,OK}`** - Judge feedback

Any tool that follows these conventions can participate in the protocol.

## Built for AI Coding Assistants

This protocol is designed for **Claude Code, Cursor, Windsurf, Codex**, and similar AI agents that:
- Work in your native terminal/IDE
- Read and write files
- Execute shell commands
- Need to work autonomously (overnight, multi-hour tasks)

**No integration required.** Just give Claude Code this repo and say:
```
Read .repo/briefs/CURRENT.json and start working.
```

Claude reads briefs, writes code, submits for review, handles feedback, and advances—all automatically. Works across context windows because everything is in files.

## How It Works

```
┌─────────────┐
│   Brief     │  What to build (.repo/briefs/<phase>.md)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Implement  │  Build the thing (Claude, human, any agent)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Judge     │  Check quality gates (.repo/critiques/)
└──────┬──────┘
       │
       ├─❌─→ Critique (.md) → Fix → Review again
       │
       └─✅─→ Approved (.OK) → Next phase
```

**The Protocol:**
1. Agent reads `.repo/briefs/CURRENT.json` to find active phase
2. Agent reads brief at specified path
3. Agent implements requirements
4. Agent submits for review: `./tools/phasectl.py review <phase>`
5. Judge validates gates, writes critique or approval
6. If approved: `./tools/phasectl.py next` advances to next phase
7. Repeat until complete

## Quick Start (5 Minutes)

### 1. Clone and Setup (1 min)

```bash
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt
```

### 2. Use with Claude Code (1 min)

Open in Claude Code and say:
```
Read .repo/briefs/CURRENT.json and start working on the current phase.
```

Or from terminal:
```bash
./orient.sh  # See status in 10 seconds
```

### 3. Try the Demo (3 min)

```bash
# See current phase
cat .repo/briefs/CURRENT.json

# Read the brief
cat .repo/briefs/P02-impl-feature.md

# Submit for review
./tools/phasectl.py review P02-impl-feature

# Advance to next phase
./tools/phasectl.py next
```

**That's it.** Claude Code (or any AI agent) can now work autonomously through all phases.

## File Format Reference

### `.repo/briefs/CURRENT.json`

```json
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": 1234567890.0
}
```

### `.repo/plan.yaml`

```yaml
plan:
  id: YOUR-PROJECT
  phases:
    - id: P01-scaffold
      description: "Create initial structure"
      scope:
        include: ["src/**", "tests/**"]
      artifacts:
        must_exist: ["src/__init__.py"]
      gates:
        tests: { must_pass: true }
        docs: { must_update: ["README.md"] }
        drift: { allowed_out_of_scope_changes: 0 }
```

### `.repo/critiques/<phase>.md` (Needs Work)

```markdown
# Critique: P01-scaffold

## Issues Found
- Missing file: src/__init__.py
- Tests failed: 2/5 passing
- Documentation not updated: README.md

## Resolution
Fix the issues above and re-run:
./tools/phasectl.py review P01-scaffold
```

### `.repo/critiques/<phase>.OK` (Approved)

```
Phase approved at 2025-01-10T14:30:00Z
All gates passed.
```

## Protocol Implementations

This repo includes a **reference implementation** in Python:

- **`tools/phasectl.py`** - Controller (review/next commands)
- **`tools/judge.py`** - Quality gate validator
- **`tools/llm_judge.py`** - Optional LLM semantic review

But you could implement the protocol in:
- Bash scripts
- GitHub Actions
- Make targets
- Any language

As long as you follow the file conventions.

## Quality Gates

Define gates in `plan.yaml`:

| Gate | Checks | Example |
|------|--------|---------|
| **tests** | Test suite passes | `pytest` exit code 0 |
| **docs** | Files updated | `README.md` modified |
| **drift** | Scope boundaries | Only `src/` files changed |
| **lint** | Code quality | Max complexity < 12 |
| **llm_review** | Semantic check | Claude reviews architecture |

## Adding LLM Review (Optional)

Enable semantic code review with Claude:

```yaml
gates:
  llm_review: { enabled: true }
```

Set your API key:
```bash
export ANTHROPIC_API_KEY='sk-ant-...'
```

Cost: ~$0.01 per review. LLM catches architecture issues that rules miss.

## Why a Protocol?

**Not a protocol (framework):**
- Install package
- Import classes
- Learn API
- Locked to one language

**Protocol (this):**
- Follow file conventions
- Implement any way you want
- Language agnostic
- Composable with existing tools

**It's like Git for autonomous execution.**

## Use Cases

### 1. Overnight Autonomous Work with Claude Code

Before bed:
```bash
cd my-project
./orient.sh  # Show Claude where we are
```

Tell Claude Code:
```
Work through phases overnight. Read .repo/briefs/CURRENT.json to start.
```

Wake up to 2-3 completed phases with tests, docs, and quality gates passed.

### 2. Other Uses

- **Multi-agent systems** - Each agent implements phases
- **CI/CD integration** - Gates enforce quality in pipelines
- **Human-in-loop** - Human reads brief, judge validates work
- **Eval loops** - Quality gates force improvement iterations

## Context Window Resilience

New Claude instance? No problem:

```bash
./orient.sh        # See status
cat START_HERE.md  # 60-second onboarding
```

All state lives in files. No memory required.

## Permission Automation

See `.claude-code.json` for auto-approval patterns. Enables autonomous execution without permission prompts.

## Learn More

- **START_HERE.md** - Quick orientation for new instances
- **`orient.sh`** - Status dashboard script
- **`.repo/plan.yaml`** - See the demo phases

## License

MIT

---

**The protocol is the spec. This repo is just one way to implement it.**
