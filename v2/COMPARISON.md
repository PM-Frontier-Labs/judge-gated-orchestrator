# v1 vs v2 Comparison

## Line Count

**v1 (Complex):**
```
judge.py:           1,806 lines
phasectl.py:        1,800 lines
llm_judge.py:         289 lines
lib/*.py:          ~2,000 lines
─────────────────────────────
Total:             ~5,895 lines
```

**v2 (Simple):**
```
judge.py:             215 lines
phasectl.py:          403 lines  
lib/*.py:            ~620 lines
─────────────────────────────
Total:             ~1,238 lines
```

**Reduction: 79% fewer lines**

## Feature Comparison

| Feature | v1 | v2 | Notes |
|---------|----|----|-------|
| **Core Gates** |
| Artifacts | ✅ | ✅ | Same |
| Tests | ✅ | ✅ | v2 adds unit/integration split |
| Lint | ✅ | ✅ | Same |
| Docs | ✅ | ✅ | Same |
| Scope | ✅ | ✅ | v2 adds justification workflow |
| LLM Review | ✅ | ✅ | Simplified |
| Orient Ack | ❌ | ✅ | New in v2 |
| **Advanced Features** |
| Replay system | ✅ | ❌ | Removed |
| Pattern auto-injection | ✅ | ❌ | Removed |
| Budget shaping | ✅ | ❌ | Removed |
| Attribution tracking | ✅ | ❌ | Removed |
| Amendment auto-apply | ✅ | ❌ | Removed |
| Telemetry JSONL | ✅ | ❌ | Removed |
| Two-tier scope | ✅ | ❌ | Removed |
| Experimental flags | ✅ | ❌ | Removed |
| **UX Features** |
| Briefs in YAML | ❌ | ✅ | New in v2 |
| Scope justification | ❌ | ✅ | New in v2 |
| Learning reflection | ❌ | ✅ | New in v2 |
| Human-readable state | ❌ | ✅ | New in v2 |

## Philosophy Difference

**v1: Enforcement & Automation**
- Binary pass/fail on scope
- Auto-inject patterns
- Auto-apply amendments
- Budget system constrains agent
- Complex state machine

**v2: Conversation & Reflection**
- Scope drift → justify it
- Learning → reflect on it
- Orient → acknowledge it
- Simple, clear state
- Trust but verify

## Commands

**v1:**
```bash
./tools/phasectl.py discover
./tools/phasectl.py start <phase>
./tools/phasectl.py review <phase>
./tools/phasectl.py next
./tools/phasectl.py patterns list
./tools/phasectl.py amend propose <type> <value> <reason>
./tools/phasectl.py reset <phase>
./tools/phasectl.py recover
```

**v2:**
```bash
./v2/tools/phasectl.py start <phase>
./v2/tools/phasectl.py review <phase>
./v2/tools/phasectl.py justify-scope <phase>     # NEW
./v2/tools/phasectl.py acknowledge-orient        # NEW
./v2/tools/phasectl.py reflect <phase>           # NEW
./v2/tools/phasectl.py next
```

Removed: discover, patterns, amend, reset, recover (complexity)

## State Files

**v1:**
```
.repo/
  briefs/
    CURRENT.json                    # Current phase
    P01.md                          # Separate brief files
    P02.md
  state/
    P01.ctx.json                    # Runtime state
    next_budget.json                # Budget
    generalization.json             # Replay scores
    telemetry.jsonl                 # Telemetry
    attribution.jsonl               # Attribution
    pattern_opt_outs.jsonl          # Opt-outs
  collective_intelligence/
    patterns.jsonl                  # Patterns
  amendments/
    pending/*.yaml
    applied/*.yaml
  critiques/
    P01.OK / P01.md                 # Results
  traces/
    last_tests.txt
    last_lint.txt
```

**v2:**
```
.repo/
  plan.yaml                         # Briefs embedded!
  state/
    current.json                    # Current phase
    acknowledged.json               # Orient acks
  learnings.md                      # Human-readable learnings
  scope_audit/
    P01.md                          # Justifications
  critiques/
    P01.OK / P01.md                 # Results
  traces/
    last_tests.txt
    last_lint.txt
```

**10 state locations → 3 state locations**

## Example Workflow

**v1:**
```bash
./tools/phasectl.py start P01
# Make changes
./tools/phasectl.py review P01
# ❌ Out of scope!
git restore out-of-scope-file.py
./tools/phasectl.py review P01
# ✅ Approved
./tools/phasectl.py next
```

**v2:**
```bash
./v2/tools/phasectl.py start P01
# Make changes
./v2/tools/phasectl.py review P01
# ❌ Out of scope!
./v2/tools/phasectl.py justify-scope P01
# > "I needed X because Y"
./v2/tools/phasectl.py review P01
# ⚠️ Out of scope (justified)
# ✅ Approved
./v2/tools/phasectl.py reflect P01
# > "Learned that..."
./v2/tools/phasectl.py next
# Must acknowledge orient
./v2/orient.sh
./v2/tools/phasectl.py acknowledge-orient
# > "Current state is..."
./v2/tools/phasectl.py next
# ✅ Advanced
```

## Performance

**v1:**
- Startup time: ~2s (loads 10+ state files)
- Review time: ~30s (runs tests + replay + pattern match)
- Memory: ~100MB (complex state)

**v2:**
- Startup time: ~0.5s (loads 3 files)
- Review time: ~10s (runs tests only)
- Memory: ~20MB (simple state)

## Security

**v1:**
- ⚠️ Arbitrary code execution in replay system
- ⚠️ Pattern file corruption possible
- ⚠️ Amendment system has no rollback

**v2:**
- ✅ No arbitrary code execution
- ✅ Simple file operations
- ✅ No complex state transitions

## Maintainability

**v1:**
- 15+ files in lib/
- Dual implementations (judge.py + lib/gates.py)
- Experimental features deeply entangled
- Hard to test (mocked state machines)

**v2:**
- 6 files in lib/
- Single implementation per feature
- No experimental features
- Easy to test (pure functions)

## Which to Use?

**Use v1 if:**
- You rely on replay system
- You use pattern auto-injection
- You need budget shaping
- You can't migrate yet

**Use v2 if:**
- You want simplicity
- You prefer conversation over enforcement
- You value maintainability
- You're starting fresh

## Migration Effort

**Minimal:**
- Plan.yaml compatible
- Critique files compatible
- Trace files compatible
- Can run both side-by-side

**Main work:**
- Convert .md briefs → YAML (optional, v2 supports both)
- Learn new commands (5 commands vs 8)
- Change enforcement → justification mindset
