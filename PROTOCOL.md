# Protocol (Execution Loop)

Audience: AI coding assistants executing phases. Keep this open while you work.

## One‑page loop
```text
1) ./orient.sh                      # Recover context
2) Read .repo/briefs/<PHASE>.md     # Objective, scope, gates
3) Implement within scope           # Code + tests + docs
4) ./tools/phasectl.py review <PHASE>
   - Applies pending amendments
   - Runs tests (scoped or all)
   - Saves traces
   - Invokes judge
5) If approved → ./tools/phasectl.py next; else fix critique and repeat
```

All state is file‑based. You can always recover by reading files under `.repo/`.

## Command reference
```bash
./orient.sh
./tools/phasectl.py review <PHASE>
./tools/phasectl.py next
```

## Files
- `.repo/briefs/CURRENT.json` — points to the active phase
- `.repo/briefs/<PHASE>.md` — objective, scope, artifacts, gates, steps
- `.repo/plan.yaml` — roadmap + scopes + gates
- `.repo/critiques/<PHASE>.{md,OK}` — judge result
- `.repo/traces/last_tests.txt` — last test run output

### CURRENT.json (minimal)
```json
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "baseline_sha": "<git-sha>",
  "plan_sha": "<sha256>",
  "manifest_sha": "<sha256>"
}
```

### plan.yaml (essentials)
```yaml
plan:
  id: PROJECT
  summary: "What this project does"
  base_branch: "main"
  test_command: "pytest tests/ -v"      # optional
  lint_command: "ruff check ."          # optional

  phases:
    - id: P01-scaffold
      description: "Create structure + one test"
      scope:
        include: ["src/**", "tests/**"]
        exclude: []
      artifacts:
        must_exist: ["src/__init__.py", "tests/test_demo.py"]
      gates:
        tests: { must_pass: true, test_scope: "all", quarantine: [] }
        docs:  { must_update: [] }
        drift: { allowed_out_of_scope_changes: 0 }
        lint:  { must_pass: false }
        llm_review: { enabled: false }

  protocol_lock:
    protected_globs: ["tools/**", ".repo/plan.yaml", ".repo/protocol_manifest.json"]
    allow_in_phases: ["P00-protocol-maintenance"]
```

### Brief format
```markdown
# Phase <ID>: <Name>

## Objective
What to accomplish in one paragraph.

## Scope 🎯
✅ YOU MAY TOUCH: [globs]
❌ DO NOT TOUCH: [globs]

## Required Artifacts
- [ ] file1 — purpose
- [ ] file2 — purpose

## Gates
- Tests must pass
- Docs updated (if listed)
- Drift within allowance

## Steps
1. ...
2. ...
```

## Gates (what judge checks)
- **Artifacts**: listed files exist and are non‑empty
- **Tests**: `test_command` exits 0 (supports `test_scope: scope|all`, `quarantine`)
- **Lint (optional)**: `lint_command` exits 0
- **Docs**: `must_update` files were changed in this phase
- **Drift**: only in‑scope files changed (or within allowed count)
- **LLM review (optional)**: enabled phases require LLM approval
- **Protocol lock**: protected files match manifest; plan/manifest unchanged mid‑phase

## Scope rules (git + glob)
- Includes: `.repo/plan.yaml` → `phases[].scope.include`
- Excludes override includes
- Matching uses `pathspec` (gitignore‑style); `**` is recursive

## Common recoveries
- Tests failing → read `.repo/traces/last_tests.txt`, fix, re‑review
- Out‑of‑scope → revert or adjust scope/brief, re‑review
- Forbidden file changed → move change to protocol maintenance phase

## Best practice
- Read the brief fully before coding
- Run review early for drift feedback
- Fix all critique items in one pass
- Advance only when the `.OK` file exists

That’s the whole protocol. Keep it tight; let the files drive the work.
