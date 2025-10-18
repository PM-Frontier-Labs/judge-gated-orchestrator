# Getting Started (Essential)

Audience: human developer. Time: ~5 minutes.

## Prerequisites
- Python 3.10+
- Git

## Install
```bash
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator
pip install -r requirements.txt
```

## First run
```bash
./orient.sh                       # Show current state
./tools/phasectl.py review P01-scaffold  # Run gates for a sample phase
```

You’ll see: diff summary, tests running, judge verdict (.OK or critique .md).

## What the protocol uses
- `.repo/plan.yaml` — phases, scope, and gates
- `.repo/briefs/` — per‑phase briefs and `CURRENT.json`
- `.repo/critiques/` — judge results
- `.repo/traces/` — last run outputs (tests, lint)

## Add to your project (minimal)
```bash
# From your repo root
cp -r tools ./
cp orient.sh ./
mkdir -p .repo/briefs .repo/critiques .repo/traces
```

Create `.repo/briefs/CURRENT.json`:
```json
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": 1760223767
}
```

## Write a tiny plan
```yaml
# .repo/plan.yaml
plan:
  id: DEMO
  summary: "Demo project"
  phases:
    - id: P01-scaffold
      description: "Create structure + one test"
      scope:
        include: ["src/**", "tests/**"]
      artifacts:
        must_exist: ["src/__init__.py", "tests/test_demo.py"]
      gates:
        tests: { must_pass: true }
        drift: { allowed_out_of_scope_changes: 0 }
```

## Minimal brief
```markdown
# Phase P01: Scaffold

## Objective
Create project skeleton with one passing test.

## Scope 🎯
✅ YOU MAY TOUCH: src/**, tests/**
❌ DO NOT TOUCH: tools/**

## Required Artifacts
- [ ] src/__init__.py
- [ ] tests/test_demo.py

## Gates
- Tests must pass
- No out‑of‑scope changes
```

## Core workflow
```text
Read brief → Implement within scope → ./tools/phasectl.py review → Fix critique or next
```

## Top 3 issues (and fixes)
- Tests missing or failing → read `.repo/traces/last_test.txt`
- Out‑of‑scope changes → tighten scope or revert files
- Protocol files changed → do it in a dedicated maintenance phase

## Next
- `PROTOCOL.md` — command loop + file formats
- `LLM_PLANNING.md` — have an LLM draft your plan and briefs
- `EXAMPLES.md` — short, copy‑pasteable examples
