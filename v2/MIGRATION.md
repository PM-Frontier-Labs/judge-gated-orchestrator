# Migration from v1 to v2

## Quick Migration

If you're currently using v1 and want to switch to v2:

```bash
# 1. Your v1 still works, no rush
cd /workspace

# 2. Try v2 on a new phase
./v2/tools/phasectl.py start P01-your-phase

# 3. When ready, deprecate v1
mv tools tools-v1-backup
mv v2/tools tools
mv v2/orient.sh orient.sh
```

## What Changed

### Removed (2,500 lines)
- ❌ Replay system
- ❌ Pattern auto-injection  
- ❌ Budget shaping
- ❌ Attribution tracking
- ❌ Amendment auto-application
- ❌ Telemetry JSONL
- ❌ Two-tier scope
- ❌ All experimental features

### Added/Enhanced
- ✅ Briefs in plan.yaml (no more separate .md files)
- ✅ Scope justification workflow (conversation over enforcement)
- ✅ Mandatory orient.sh acknowledgment
- ✅ Learning capture and reflection
- ✅ Split unit/integration tests
- ✅ Cleaner error messages

## State Migration

v2 uses simpler state files:

**v1 state:**
```
.repo/
  state/
    P01.ctx.json                    # Complex context
    next_budget.json                # Budget shaping
    generalization.json             # Replay scores
    telemetry.jsonl                 # Telemetry
    attribution.jsonl               # Attribution
    pattern_opt_outs.jsonl          # Opt-outs
  collective_intelligence/
    patterns.jsonl                  # Auto-patterns
  amendments/
    pending/*.yaml                  # Amendments
```

**v2 state:**
```
.repo/
  state/
    current.json                    # Current phase only
    acknowledged.json               # Orient acks
  learnings.md                      # Human-readable
  scope_audit/
    P01.md                          # Justifications
```

### Manual Migration Steps

If you want to preserve some v1 state:

1. **Current phase:**
```bash
# v1
cat .repo/briefs/CURRENT.json

# v2 (will be created when you start a phase)
./v2/tools/phasectl.py start <phase-id>
```

2. **Briefs:**
```bash
# Convert .md briefs to YAML format in plan.yaml
# Example:

# Before (.repo/briefs/P01.md):
# Objective
# Create scaffolding

# After (in .repo/plan.yaml):
phases:
  - id: P01
    brief: |
      # Objective
      Create scaffolding
```

3. **Critiques/Approvals:**
These are compatible! v2 reads the same files:
```
.repo/critiques/P01.OK      # Same format
.repo/critiques/P01.md      # Same format
```

4. **Test/Lint traces:**
Also compatible:
```
.repo/traces/last_tests.txt  # Same format
.repo/traces/last_lint.txt   # Same format
```

## Plan Format

### v1 Format (still works):
```yaml
plan:
  id: my-project
  phases:
    - id: P01-scaffold
      description: "Setup"
      # Brief in separate file: .repo/briefs/P01-scaffold.md
```

### v2 Format (recommended):
```yaml
plan:
  id: my-project
  phases:
    - id: P01-scaffold
      description: "Setup"
      brief: |
        # Objective
        Create project scaffolding
        
        # Required Artifacts
        - src/__init__.py
        - tests/test_main.py
      
      scope:
        include: ["src/**", "tests/**"]
      gates:
        tests: {must_pass: true}
```

## Breaking Changes

1. **No more experimental features**
   - `replay_budget` flag removed
   - Pattern auto-injection removed
   - Budget shaping removed

2. **Scope enforcement changed**
   - v1: Hard block on out-of-scope changes
   - v2: Ask for justification, record for audit

3. **State files simplified**
   - v1: 10+ JSON/JSONL files
   - v2: 3 files (current.json, acknowledged.json, learnings.md)

4. **Commands moved**
   - v1: `./tools/phasectl.py`
   - v2: `./v2/tools/phasectl.py` (until you migrate fully)

## Testing v2

To test v2 without affecting v1:

```bash
# 1. Create a test phase
./v2/tools/phasectl.py start P99-v2-test

# 2. Make some changes
echo "test" > test.txt

# 3. Review
./v2/tools/phasectl.py review P99-v2-test

# 4. If it works, migrate fully
```

## Rollback

If v2 doesn't work for you:

```bash
# Just use v1 tools again
./tools/phasectl.py start <phase>

# v2 doesn't modify v1 state
```

## Questions?

- Check v2/README.md for architecture
- Run `./v2/orient.sh` for current state
- Compare file counts: `wc -l tools/*.py` vs `wc -l v2/tools/*.py`
