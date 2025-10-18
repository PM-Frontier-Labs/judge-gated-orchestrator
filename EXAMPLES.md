# Examples Cookbook

Practical, end-to-end examples showcasing the optimized protocol.

---

## 1) Amendment: Fix test command

Context: Pytest invocation error seen in traces.

```bash
# Submit for review (will fail with usage error)
./tools/phasectl.py review P02-impl-feature

# Propose amendment within budget
./tools/phasectl.py amend propose set_test_cmd "python -m pytest -q" "Fix pytest usage"

# Re-run review (amendment auto-applied before tests)
./tools/phasectl.py review P02-impl-feature
```

What happened:
- Amendment stored under `.repo/amendments/pending/*.yaml`, auto-applied, then archived under `applied/`.
- Runtime context `.repo/state/P02-impl-feature.ctx.json` updated with `test_cmd` and budget usage.
- Pattern learned and stored in `.repo/collective_intelligence/patterns.jsonl` for future auto-proposals.

---

## 2) Amendment: Add scope to include missing tests

Context: Drift gate flags out-of-scope test changes.

```bash
# See changed files and drift limit
./tools/phasectl.py review P02-impl-feature

# Propose adding a tests directory to scope
./tools/phasectl.py amend propose add_scope "tests/mvp/**" "Include MVP tests"

# Re-run review
./tools/phasectl.py review P02-impl-feature
```

---

## 3) Pattern Learning and Listing

```bash
# After a successful phase that used amendments
./tools/phasectl.py patterns list
```

Sample output:
```
Stored patterns:
1. Fix pytest usage error (confidence: 0.9)
   When: {"pytest_error": "usage: python -m pytest"}
   Action: {"amend": "set_test_cmd", "value": "python -m pytest -q"}
```

---

## 4) Enhanced Briefs After Advancing

```bash
./tools/phasectl.py next
```

You will see the next phase brief with:
- Collective Intelligence Hints
- Execution Guardrails

---

## 5) Complete Workflow (Mini Project)

1. Initialize phase
```bash
cat > .repo/briefs/CURRENT.json << 'EOF'
{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": 1760223767
}
EOF
```

2. Implement files within scope, then review
```bash
./tools/phasectl.py review P01-scaffold
```

3. If critique appears, address issues
- Revert out-of-scope files or propose `add_scope` amendment
- Fix failing tests or propose `set_test_cmd`

4. Re-run review until approved
```bash
./tools/phasectl.py review P01-scaffold
```

5. Advance and read enhanced brief
```bash
./tools/phasectl.py next
```
