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
✅ **Schema validation** - Comprehensive plan.yaml validation catches configuration errors before execution
✅ **Concurrent safety** - File locking prevents race conditions in CI/multi-agent scenarios
✅ **Context-window proof** - All state in files, `./orient.sh` recovers context in <10 seconds
✅ **Terminal-native** - No servers, no APIs, just files and shell commands
✅ **Language-agnostic** - File-based protocol works for any language
✅ **5-minute setup** - Clone, `pip install -r requirements.txt`, run demo
✅ **Collective Intelligence** - Learn from execution patterns and provide intelligent guidance
✅ **Amendment System** - Bounded mutability for runtime adjustments
✅ **Enhanced Briefs** - Hints and guardrails for intelligent execution
✅ **Outer Loop Learning** - Micro-retrospectives and continuous improvement

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

# Optional: Install LLM features for enhanced code review
pip install -r requirements-llm.txt

# See status
./orient.sh

# Try the review flow
./tools/phasectl.py review P02-impl-feature
# → Shows diff summary, runs tests, invokes judge, shows result
```

**Note:** `tools/phasectl.py` is the only supported CLI. Other tools in `tools/` are internal implementation details.

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

## Collective Intelligence Features

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
- **Context Files**: `Pxx.ctx.json` stores runtime state (baseline_sha, test_cmd, mode)
- **Mode Management**: EXPLORE → LOCK modes with automatic transitions

## Core Workflow

```
1. Claude reads brief (.repo/briefs/P01-scaffold.md)
2. Claude implements files within scope
3. Claude runs: ./tools/phasectl.py review P01-scaffold
   ├─> Validates plan.yaml schema
   ├─> Shows diff summary (in-scope vs out-of-scope)
   ├─> Runs tests (with optional scope filtering)
   ├─> Invokes judge (with file locking)
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
│   └── lib/              # Shared utilities
│       ├── protocol_guard.py  # SHA256 integrity verification
│       ├── plan_validator.py  # Schema validation
│       ├── file_lock.py       # Concurrent execution prevention
│       ├── git_ops.py         # Git utilities
│       ├── scope.py           # Scope matching
│       └── traces.py          # Test output capture
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

### For Automation 🤖

**Execution mode** (autonomous phase implementation):
- **PROTOCOL.md** - Execution manual with file specs, commands, gates, and error handling
- Use this when: Human says "execute the current phase" or "read PROTOCOL.md and start working"

### Navigation

| Audience | Goal | Read This |
|----------|------|-----------|
| Human setting up | Understand what this is | README.md |
| Human using it | Learn how to use | GETTING_STARTED.md |
| AI executing phases | Implement within gates | PROTOCOL.md |

## Next Steps

**New here?** Read `GETTING_STARTED.md` for a step-by-step guide.

**Ready to use it?** Read `PROTOCOL.md` to execute phases.

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
