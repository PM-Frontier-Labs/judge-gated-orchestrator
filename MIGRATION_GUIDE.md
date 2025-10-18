# Migration Guide (Essential)

Audience: teams moving from framework‑style agents to the Judge‑Gated Protocol.

## What changed
- From: agents free‑roam, ad‑hoc prompts, hidden state
- To: phases with briefs, judge‑gated progress, file‑based state
- Interface: files + shell commands instead of libraries/servers

## Why migrate
- Deterministic progress (no drift)
- Verifiable quality (tests/docs enforced)
- Context‑window resilience (state is in files)

## Migration steps
1) Keep your code; add protocol files
```bash
cp -r tools ./
cp orient.sh ./
mkdir -p .repo/briefs .repo/critiques .repo/traces
```

2) Create a minimal plan
```yaml
# .repo/plan.yaml
plan:
  id: MIGRATION
  summary: "Adopt the judge‑gated protocol"
  phases:
    - id: P01-adopt-protocol
      description: "Introduce protocol files + one golden test"
      scope:
        include: ["src/**", "tests/**", "README.md"]
      artifacts:
        must_exist: ["tests/test_golden.py"]
      gates:
        tests: { must_pass: true }
        drift: { allowed_out_of_scope_changes: 0 }
```

3) Write P01 brief
```markdown
# Phase P01: Adopt Protocol

## Objective
Add protocol files and a golden test.

## Scope 🎯
✅ YOU MAY TOUCH: tools/**, .repo/**, tests/**
❌ DO NOT TOUCH: business logic beyond the golden test

## Required Artifacts
- [ ] tests/test_golden.py

## Gates
- Tests must pass
- Drift: 0 out‑of‑scope files
```

4) Initialize CURRENT.json and run
```bash
cat > .repo/briefs/CURRENT.json <<'JSON'
{
  "phase_id": "P01-adopt-protocol",
  "brief_path": ".repo/briefs/P01-adopt-protocol.md",
  "status": "active",
  "started_at": 1760223767
}
JSON

./tools/phasectl.py review P01-adopt-protocol
```

## Breaking changes to watch
- Protocol files are protected by a manifest; modify them only in a dedicated maintenance phase
- Gates may block until tests/docs are updated — plan phases accordingly

## Tips
- Start strict (drift=0), relax intentionally
- Use `test_scope: "scope"` for speed on large repos
- Keep phases small and testable; split broad goals

Done. Your agents now work via a small, deterministic protocol.
