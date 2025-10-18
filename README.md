# Gated Phase Protocol

**Autonomous AI execution with quality gates. Works in your terminal with Claude Code, Cursor, or any AI coding assistant.**

## What Is This?

A **protocol** (not a framework) for autonomous execution. Like Git tracks changes with `.git/` files, this protocol tracks autonomous work with simple file conventions:

- **`.repo/briefs/CURRENT.json`** → Current phase
- **`.repo/plan.yaml`** → Roadmap with phases and quality gates  
- **`.repo/critiques/<phase>.{md,OK}`** → Judge feedback

Any tool following these conventions can participate. This repo provides a Python reference implementation, but you could rewrite it in any language.

## Why It Matters

**Problem:** AI agents drift off-task, skip tests, and require constant supervision.

**Solution:** Define phases with quality gates. The judge blocks progression until all gates pass. The agent iterates until approved, then advances autonomously.

**Result:** Define a 6-week roadmap, let it run overnight, wake up to completed phases with passing tests and updated docs.

## Key Features

| Feature | Benefit |
|---------|----------|
| **Autonomous execution** | Agent works through phases without supervision |
| **Quality gates** | Enforces tests, docs, drift prevention, optional LLM review |
| **Protocol integrity** | SHA256 tamper detection prevents agent self-modification |
| **Context-window proof** | All state in files, `./orient.sh` recovers context in <10 seconds |
| **Concurrent-safe** | File locking prevents race conditions in CI/multi-agent scenarios |
| **Terminal-native** | No servers, no APIs—just files and shell commands |
| **Language-agnostic** | Works with any language |
| **5-minute setup** | Clone, install, run demo |

## When to Use

**Perfect for:**
- ✅ Multi-phase projects (3+ sequential phases)
- ✅ Overnight autonomous work
- ✅ Quality-critical code (tests + docs required)
- ✅ Preventing scope drift

**Not ideal for:**
- ❌ Single tasks (just prompt Claude directly)
- ❌ Exploratory coding (rigid phases slow discovery)
- ❌ Non-git projects (drift prevention requires git)

## Quick Demo (30 Seconds)

```bash
# Clone and install
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt

# Check status
./orient.sh

# Try the review flow
./tools/phasectl.py review P02-impl-feature
```

**You'll see:** Diff summary, test execution, judge verdict, and actionable feedback.

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
1. Agent reads brief      → .repo/briefs/P01-scaffold.md
2. Agent implements       → Changes within scope
3. Agent reviews          → ./tools/phasectl.py review P01-scaffold
   - Validates plan.yaml
   - Shows diff summary  
   - Runs tests
   - Judge checks all gates
4. Judge writes verdict   → .repo/critiques/P01-scaffold.{md|OK}
5. If approved            → ./tools/phasectl.py next
   If critique            → Fix issues, re-review
```

**Key principle:** Judge blocks until quality standards met. Agent iterates automatically.

## Real-World Example

**Scenario:** 6-phase backend refactor

| Your Role | AI Agent's Role |
|-----------|----------------|
| Write `.repo/plan.yaml` (6 phases) | Reads P01 brief |
| Write 6 briefs | Implements changes |
| Define scope + gates | Submits review → gets critique → fixes → approved |
| Go to sleep | Advances to P02, repeats for all phases |

**Result:** Wake up to completed refactor with passing tests, updated docs, zero drift.

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

### For AI Assistants 🤖

**Planning mode** (collaborative roadmap creation):
- **LLM_PLANNING.md** - Complete guide for helping humans design phases, scope, and gates
- Use this when: Human says "help me create a plan.yaml" or "let's break this project into phases"

**Execution mode** (autonomous phase implementation):
- **PROTOCOL.md** - Execution manual with file specs, commands, gates, and error handling
- Use this when: Human says "execute the current phase" or "read PROTOCOL.md and start working"

### For Validation 🧪

- **TESTME.md** - 12 tests to validate protocol implementation (25-30 minutes)

### Quick Navigation

| Audience | Goal | Read This |
|----------|------|-----------|
| Human setting up | Understand what this is | README.md |
| Human using it | Learn how to use | GETTING_STARTED.md |
| AI planning roadmap | Help create plan.yaml | LLM_PLANNING.md |
| AI executing phases | Implement within gates | PROTOCOL.md |
| Anyone validating | Verify it works | TESTME.md |

## Next Steps

| Your Goal | Action |
|-----------|--------|
| **New here?** | Read `GETTING_STARTED.md` |
| **Ready to plan?** | Point Claude at `LLM_PLANNING.md` |
| **Want to validate?** | Follow `TESTME.md` (12 tests, 25-30 min) |

### CI/CD Integration

The protocol is just files + shell commands:
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
