# LLM Planning (Essential)

Read this when asked to create or update `.repo/plan.yaml` and phase briefs.

## Outcome
- A valid `plan.yaml` with 3–10 clear phases
- A brief for the first phase
- `CURRENT.json` pointing to that phase

## Workflow (one pass)
```text
1) Understand the project goal and constraints
2) Propose phases (1–3 days each)
3) Define scope + gates for each phase
4) Write plan.yaml
5) Write brief for phase 1
6) Initialize CURRENT.json
7) Handoff to PROTOCOL.md for execution
```

## Phase rules
- Size: 1–3 days of focused work
- Single concern: one feature/module
- Testable: artifacts + tests must demonstrate success
- Sequential: order phases to minimize dependencies

## plan.yaml template (minimal)
```yaml
plan:
  id: PROJECT
  summary: "One‑sentence description"
  base_branch: "main"

  phases:
    - id: P01-name
      description: "What this phase accomplishes"
      scope:
        include: ["src/module/**", "tests/module/**"]
        exclude: []
      artifacts:
        must_exist: ["src/module/file.py", "tests/test_file.py"]
      gates:
        tests: { must_pass: true, test_scope: "scope", quarantine: [] }
        docs:  { must_update: [] }
        drift: { allowed_out_of_scope_changes: 0 }
        lint:  { must_pass: false }
        llm_review: { enabled: false }

  protocol_lock:
    protected_globs: ["tools/**", ".repo/plan.yaml", ".repo/protocol_manifest.json"]
    allow_in_phases: ["P00-protocol-maintenance"]
```

## Good scope patterns
```yaml
include: [
  "src/auth/**",      # code
  "tests/auth/**",    # tests
  "docs/auth.md"      # docs touched this phase (optional)
]
```
Avoid overly broad (`"src/**"`) and vague (`"*.py"`) patterns. Always include tests.

## Gate selection
- tests: always true; use `test_scope: "scope"` for large repos
- docs: require updates only when public/API changes occur
- drift: start with 0; raise to 1–2 if nearby edits expected
- lint: enable when a linter already exists
- llm_review: enable for security‑critical or high‑risk phases

## Brief template (phase 1)
```markdown
# Phase P01: <Name>

## Objective
Clear, testable outcome in 2–3 sentences.

## Scope 🎯
✅ YOU MAY TOUCH: src/module/**, tests/module/**
❌ DO NOT TOUCH: tools/**, .repo/**

## Required Artifacts
- [ ] src/module/file.py — implementation
- [ ] tests/module/test_file.py — covers the new behavior

## Gates
- Tests must pass
- Drift: 0 out‑of‑scope files

## Steps
1) Build the simplest working version
2) Add tests and make them pass
3) Update docs if listed
```

## Initialize CURRENT.json
```json
{
  "phase_id": "P01-name",
  "brief_path": ".repo/briefs/P01-name.md",
  "status": "active",
  "started_at": 1760223767
}
```

## Conversation starter
```
Create a plan.yaml for <project>. Use 5–7 phases, each 1–3 days.
For each phase, provide id, description, scope.include (code+tests), artifacts, and gates (tests+drift, optionally docs/lint/llm_review).
Then draft a brief for P01 and CURRENT.json.
```

## Quick checks (before handoff)
- [ ] Phases are focused and testable
- [ ] Each phase includes tests in scope
- [ ] Drift defaults to 0 unless justified
- [ ] No protected files in scope
- [ ] P01 brief exists and is actionable

Handoff: tell the user to read `PROTOCOL.md` and run `./tools/phasectl.py review P01-...`.
