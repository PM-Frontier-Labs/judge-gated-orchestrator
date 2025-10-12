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

**For humans:** Read this file
**For LLMs:** Read `PROTOCOL.md`
**To validate:** Read `TESTME.md`

## Next Steps

### For Humans Evaluating This

1. **Try the demo:** Follow "Quick Demo" above (30 seconds)
2. **Read the protocol:** See `PROTOCOL.md` for detailed specs
3. **Test it:** Follow `TESTME.md` validation steps
4. **Implement your own phases:** Replace demo with your roadmap

### For Claude Code / AI Agents

Read `PROTOCOL.md` for execution instructions. That file contains the operational manual for working in this protocol.

### For CI/CD Integration

The protocol is just files + shell commands. Easy to integrate:
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
