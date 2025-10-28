# Judge Protocol v2 - Simplified

**Philosophy:** Conversation over enforcement. Simplicity over sophistication.

## Core Value (7 Features)

1. **Planning** - Briefs embedded in plan.yaml
2. **Orient** - Mandatory context recovery between phases
3. **Tests** - Unit and integration test gates
4. **Lint** - Code quality checking
5. **LLM Review** - Semantic code feedback
6. **Scope** - Drift detection with justification workflow
7. **Docs** - Documentation accountability
8. **Learning** - Reflection and knowledge capture

## What Was Removed

- ❌ Replay system (600 lines)
- ❌ Pattern auto-injection (300 lines)
- ❌ Budget shaping (200 lines)
- ❌ Attribution tracking (150 lines)
- ❌ Amendment auto-application (150 lines)
- ❌ Telemetry JSONL (100 lines)
- ❌ Two-tier scope (100 lines)
- ❌ All experimental features

**Total removed: ~2,500 lines of complexity**

## Architecture

```
v2/
  tools/
    judge.py          # 300 lines - Gate coordinator
    phasectl.py       # 500 lines - User commands
    lib/
      gates.py        # Core gate implementations
      scope.py        # Scope with justification
      plan.py         # Plan/brief loading
      state.py        # Simple state management
      learnings.py    # Learning capture
  tests/
    test_*.py         # Clean tests for behavior
```

## Usage

```bash
# Start phase
./v2/tools/phasectl.py start P01-scaffold

# Make changes...

# Review
./v2/tools/phasectl.py review P01-scaffold

# If scope drift detected:
./v2/tools/phasectl.py justify-scope P01-scaffold

# When approved, reflect on learnings:
./v2/tools/phasectl.py reflect P01-scaffold

# Advance
./v2/tools/phasectl.py next
```

## Migration from v1

```bash
./v2/tools/phasectl.py migrate-from-v1
```

This will:
- Convert .md briefs to YAML format in plan.yaml
- Migrate CURRENT.json to new format
- Preserve critique/approval state
