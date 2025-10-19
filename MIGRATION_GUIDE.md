# Migration Guide: Legacy Protocol → Optimized Judge-Gated Protocol

Audience: Existing users upgrading from the previous (pre-optimization) protocol.

---

## What Changed (High-Level)

- Collective Intelligence added:
  - Amendment system with budgets (bounded mutability)
  - Pattern learning via JSONL + auto-proposals
  - Enhanced briefs with hints and guardrails (micro-retrospectives)
- Governance ≠ Runtime split:
  - `plan.yaml` stays human-locked (governance)
  - `.repo/state/Pxx.ctx.json` is AI-writable runtime state
  - Mode management: EXPLORE → LOCK
- LLM pipeline (Critic → Verifier → Arbiter) integrated for evidence-based amendment proposals
- Phase baseline pinning for stable diffs across long-running work
- Expanded command surface via `./tools/phasectl.py`

---

## Feature Comparison

| Area | Legacy | Optimized |
|------|--------|-----------|
| Protocol integrity | Basic checks | Manifest + per-phase binding |
| Drift prevention | Include/exclude only | Forbidden files + scoped summaries + hints |
| Tests | Global | Phase-scoped with `test_scope` + quarantine |
| Collective intelligence | None | Amendments, patterns, micro-retros |
| LLM review | Optional, limited | Optional gate + dedicated pipeline |
| State | Mixed in various files | Clean split: `.repo/state/*.ctx.json` |

---

## Upgrade Steps (Safe Path)

1) Update repo to latest implementation
```bash
# In your project root
cp -r /path/to/judge-gated-orchestrator/tools ./
cp /path/to/judge-gated-orchestrator/orient.sh ./
mkdir -p .repo/briefs .repo/critiques .repo/traces .repo/state .repo/collective_intelligence
pip install -r /path/to/judge-gated-orchestrator/requirements.txt
```

2) Keep your existing `plan.yaml`, but validate
```bash
python3 -c "from tools.lib.plan_validator import validate_plan_file; from pathlib import Path; errs = validate_plan_file(Path('.repo/plan.yaml')); print('Valid' if not errs else '\n'.join(errs))"
```

3) Pin protocol manifest (integrity)
```bash
./tools/generate_manifest.py
```

4) Initialize current phase context
```bash
# If you haven't been using CURRENT.json, create it for the active phase
cat > .repo/briefs/CURRENT.json << 'EOF'
{
  "phase_id": "P01-your-phase",
  "brief_path": ".repo/briefs/P01-your-phase.md",
  "status": "active",
  "started_at": $(date +%s)
}
EOF
```

5) Adopt runtime state (optional but recommended)
- After first `./tools/phasectl.py next`, runtime context will be created as `.repo/state/Pxx.ctx.json`.
- Budgets default to:
  - `add_scope`: 2
  - `set_test_cmd`: 1
  - `note_baseline_shift`: 1

6) Use the new commands
```bash
./orient.sh
./tools/phasectl.py review <phase-id>
./tools/phasectl.py next
./tools/phasectl.py amend propose <type> <value> <reason>
./tools/phasectl.py patterns list
```

---

## Breaking Changes

- Judge now enforces protocol integrity via manifest; modifying files in `tools/**` or `.repo/plan.yaml` during a phase will fail review.
- Test traces standardized at `.repo/traces/last_tests.txt`.
- Phase baseline pinning: diffs use `baseline_sha` when available.

---

## Migration Tips and Best Practices

- Start with a small phase to validate the new gates.
- Keep `drift.allowed_out_of_scope_changes: 0` and rely on amendments for small expansions.
- Use `test_scope: "scope"` to speed up large repos.
- Quarantine only for documented flakes.

---

## Rollback Procedures

- If a migration step causes friction:
  - Revert copied `tools/**` and `orient.sh` from your VCS.
  - Remove `.repo/protocol_manifest.json` if you need to temporarily bypass integrity (not recommended).
  - Restore to previous working commit and re-attempt upgrade incrementally.

---

## FAQ

- How do I change budgets?
  - Edit `.repo/state/Pxx.ctx.json` for the active phase; be conservative.
- Can the LLM edit files directly?
  - No. The LLM proposes amendments; judge and controller apply them within budgets.
- Where are patterns stored?
  - `.repo/collective_intelligence/patterns.jsonl`
