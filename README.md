# Gated Phase Protocol

A file-based protocol for autonomous execution with quality gates. No framework to install—just conventions to follow.

## What Is This?

A **protocol**, not a framework. Like Git tracks code changes through file conventions (`.git/`, `HEAD`, etc.), this protocol tracks autonomous work through files:

- **`.repo/briefs/CURRENT.json`** - Points to current phase
- **`.repo/plan.yaml`** - Defines phases and quality gates
- **`.repo/critiques/<phase>.{md,OK}`** - Judge feedback

Any tool that follows these conventions can participate in the protocol.

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

## Quick Start

### New Instance? Orient First

```bash
./orient.sh
```

Shows current phase, progress, next steps in <10 seconds.

### Try the Demo

```bash
# Install dependencies
pip install -r requirements.txt

# See where we are
cat .repo/briefs/CURRENT.json

# Read the current brief
cat .repo/briefs/P02-impl-feature.md

# Submit for review (demo phases already complete)
./tools/phasectl.py review P02-impl-feature
```

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

- **Overnight autonomous work** - Claude builds while you sleep
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
