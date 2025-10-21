# Gated Phase Protocol

**Autonomous AI execution with quality gates. Works in your terminal with Claude Code, Cursor, or any AI coding assistant.**

## What Is This?

A **protocol** for autonomous execution—not a framework you import, but file conventions you follow.

Like Git tracks code changes through `.git/`, `HEAD`, and commit messages, this protocol tracks autonomous work through:
- **`.repo/briefs/CURRENT.json`** - Points to current phase
- **`.repo/plan.yaml`** - Defines phases and quality gates
- **`.repo/critiques/<phase>.{md,OK}`** - Judge feedback

Any tool that follows these conventions can participate. This repo includes a reference implementation in Python, but you could rewrite it in Bash, Rust, or Make.

## Purpose

AI agents often drift off-task, skip tests, ignore scope boundaries, and require constant supervision. This protocol defines phases with quality gates. The judge blocks progression until all gates pass. The agent iterates until approved, then advances autonomously.

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
✅ **Intelligent learning** - System automatically learns from successful phases and applies patterns
✅ **Economics-based enforcement** - Choices are priced via budget (scope expansion, pattern opt-out, bounded maintenance burst)

✅ **Experimental features** - Replay gate and budget shaping are opt-in via `experimental_features.replay_budget: true`
✅ **Automatic intelligence extraction** - Patterns captured, amendments suggested, attribution tracked

## Usage

**Multi-phase projects** - Breaking work into 3+ sequential phases
**Quality-critical code** - Need tests + docs enforced automatically
**AI-assisted development** - Claude Code, Cursor, Windsurf, etc.
**Scope control** - Prevent drift and "drive-by" changes

**Not suitable for:**
- Single tasks (just prompt Claude directly)
- No quality requirements (gates add overhead)
- Exploratory coding (rigid phases slow down discovery)
- Non-git projects (drift prevention requires git)

## Setup

### Option 1: GitHub Setup (Recommended)

```bash
# Clone protocol tools repository
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git

# Install protocol tools in your project
cd your-project
../judge-gated-orchestrator/install-protocol.sh

# Create your project plan
touch .repo/plan.yaml

# Discover and generate briefs
./tools/phasectl.py discover
./tools/phasectl.py generate-briefs
```

**For detailed GitHub setup instructions, see [GITHUB_SETUP.md](GITHUB_SETUP.md)**

### Option 2: Use as Example Project

```bash
# Clone and use as example
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator

# Install dependencies
pip install -r requirements.txt

# Optional: Install LLM features for enhanced code review
pip install -r requirements-llm.txt

# See status
./orient.sh

# Try the discovery flow
./tools/phasectl.py discover

# Try the review flow
./tools/phasectl.py review P01-scaffold
```

**Important:** The protocol tools are designed to be shared across projects. Each project should have its own `.repo/plan.yaml` file that defines project-specific phases and scope.

## Comparison

| Feature | This Protocol | Aider | LangGraph | Manual Prompting |
|---------|---------------|-------|-----------|------------------|
| **Quality gates** | Enforced | No | No | No |
| **Drift prevention** | Enforced | No | No | No |
| **Context-window proof** | File-based | Partial | No | No |
| **Autonomous multi-phase** | Built-in | No | Complex | No |
| **Language-agnostic** | Protocol | Yes | Python only | Yes |
| **Setup time** | 5 min | 2 min | 30 min | 0 min |
| **Overnight execution** | Supported | No | Possible | No |

## Implemented Gates

| Gate | What It Checks | Example |
|------|----------------|---------|
| **protocol_lock** | Protocol integrity | SHA256 verify `tools/judge.py` unchanged |
| **tests** | Test suite passes | `pytest` exit code must be 0 |
| **lint** | Static analysis | `ruff check .` exit code must be 0 |
| **docs** | Files updated | `README.md` must be modified |
| **drift** | Scope boundaries | Only `src/mvp/**` can change |
| **llm_review** | Semantic quality | Claude reviews architecture |

**Test scoping:**
- `test_scope: "scope"` - Only run tests matching phase scope
- `quarantine: [...]` - Skip specific tests with documented reasons

Gates are configurable per phase.

## Automatic Intelligence Features

The protocol includes automatic intelligence capabilities:

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

Like Git tracks code changes, this protocol tracks autonomous work execution. The protocol defines file conventions for quality-gated phases.

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
