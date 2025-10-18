# Judge‑Gated Protocol

A tiny, file‑first protocol that lets an AI agent execute real software work safely, phase by phase, with quality gates. No servers. No framework. Files are the API. You run shell commands.

## Why this exists
- **Agents drift.** This protocol keeps them inside scope.
- **Quality matters.** A judge enforces tests, docs, and drift rules.
- **Resilience.** All state lives in files, so context loss is never fatal.

## Quick start (3 commands)
```bash
pip install -r requirements.txt
./orient.sh
./tools/phasectl.py review P01-scaffold
```

## Core ideas
- **Protocol, not framework**: You follow file conventions; any language works.
- **Files are the API**: `.repo/plan.yaml`, `.repo/briefs/`, `.repo/critiques/`, `.repo/traces/`.
- **One command surface**: `./tools/phasectl.py` handles review and next.
- **Judge-gated**: Progress only when gates pass; otherwise clear critique.

## What you get
- **Autonomous execution** (phase by phase)
- **Scope control** (drift prevention)
- **Tests/docs enforcement** (configurable per phase)
- **Optional LLM review** (for high‑stakes phases)
- **Collective intelligence** (learns patterns, proposes fixes)

## Minimal workflow
```text
1) Write a roadmap in .repo/plan.yaml (phases, scope, gates)
2) Create briefs in .repo/briefs/ (what to build per phase)
3) Run: ./tools/phasectl.py review <PHASE>
4) Fix critique or advance with: ./tools/phasectl.py next
```

## Key commands
```bash
./orient.sh                     # Show current state in ~10s
./tools/phasectl.py review Pxx  # Submit current phase for judge review
./tools/phasectl.py next        # Advance after approval
```

## The gates (at a glance)
- **protocol_lock**: Protected files match SHA256 manifest
- **tests**: Test command exits 0 (supports scoped runs, quarantine)
- **docs**: Required docs updated in this phase
- **drift**: Only in‑scope files changed (or within allowance)
- **lint (optional)**: Linter must pass
- **llm_review (optional)**: LLM finds no issues

## Files you’ll touch
- `.repo/plan.yaml` – roadmap, gates, scope
- `.repo/briefs/` – per‑phase briefs and `CURRENT.json`
- `.repo/critiques/` – judge verdicts (`.md`, `.OK`)
- `.repo/traces/` – last run outputs (tests, lint)

## Example: propose an amendment
```bash
./tools/phasectl.py amend propose set_test_cmd "python -m pytest -q" "Fix test command"
```

## Read next
- `GETTING_STARTED.md` – install + first run (5 minutes)
- `PROTOCOL.md` – execution loop and file formats
- `LLM_PLANNING.md` – how to create plan.yaml + briefs
- `EXAMPLES.md` – short, copy‑pasteable examples
- `MIGRATION_GUIDE.md` – moving from framework‑style setups

## Philosophy
- **Simple protocol** over complex framework
- **Obvious code** over clever abstractions
- **One screen** per doc; link, don’t repeat

MIT License
