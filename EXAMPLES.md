# Examples (Copy–Paste)

Keep these handy. They cover the most common tasks.

## 1) Minimal plan.yaml (3 phases)
```yaml
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

    - id: P02-feature
      description: "Implement feature X"
      scope:
        include: ["src/feature/**", "tests/feature/**"]
      artifacts:
        must_exist: ["src/feature/core.py", "tests/feature/test_core.py"]
      gates:
        tests: { must_pass: true, test_scope: "scope" }
        drift: { allowed_out_of_scope_changes: 0 }

    - id: P03-docs
      description: "Update docs for feature X"
      scope:
        include: ["docs/**"]
      gates:
        tests: { must_pass: true }
        docs:  { must_update: ["docs/feature.md"] }
        drift: { allowed_out_of_scope_changes: 1 }
```

## 2) Amendment: set test command
```bash
./tools/phasectl.py amend propose set_test_cmd "python -m pytest -q" "Fix test runner"
```

## 3) Test scope and quarantine
```yaml
gates:
  tests:
    must_pass: true
    test_scope: "scope"
    quarantine:
      - path: "tests/integration/test_external.py::test_timeout"
        reason: "Occasional network timeouts"
```

## 4) Drift rules: forbid changes
```yaml
drift_rules:
  forbid_changes: ["requirements.txt", ".github/**"]
```

## 5) LLM review gate (optional)
```yaml
gates:
  llm_review: { enabled: true }
```
Export `ANTHROPIC_API_KEY` before review.

## 6) Brief for a feature phase
```markdown
# Phase P02: Feature X

## Objective
Add core algorithm for feature X and unit tests.

## Scope 🎯
✅ YOU MAY TOUCH: src/feature/**, tests/feature/**
❌ DO NOT TOUCH: tools/**, .repo/**

## Required Artifacts
- [ ] src/feature/core.py — implementation
- [ ] tests/feature/test_core.py — passing tests

## Gates
- Tests must pass
- Drift: 0 out‑of‑scope files

## Steps
1) Implement smallest useful version
2) Add tests and make them pass
3) Clean up and commit
```

## 7) CURRENT.json
```json
{
  "phase_id": "P02-feature",
  "brief_path": ".repo/briefs/P02-feature.md",
  "status": "active",
  "started_at": 1760223767
}
```
