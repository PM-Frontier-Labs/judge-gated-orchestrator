# Architecture Evolution

**Visual guide to the proposed refactoring**

---

## Current Architecture (Before)

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  judge.py    │  │ phasectl.py  │  │llm_judge.py  │     │
│  │              │  │              │  │              │     │
│  │ • 547 lines  │  │ • 472 lines  │  │ • 223 lines  │     │
│  │ • argparse   │  │ • argparse   │  │ • standalone │     │
│  │ • gates      │  │ • test run   │  │ • LLM call   │     │
│  │ • I/O        │  │ • diff show  │  │              │     │
│  │ • formatting │  │ • I/O        │  │              │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                  Shared Utilities (lib/)                    │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ git_ops  │ │  scope   │ │  traces  │ │  guard   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
│         Git  •  Pytest  •  Ruff  •  Anthropic API          │
└─────────────────────────────────────────────────────────────┘

Issues:
❌ CLI + business logic mixed (judge.py, phasectl.py)
❌ No reusable API (can't use programmatically)
❌ Gate logic hardcoded in judge.py
❌ Scattered I/O (judge writes files, phasectl writes files)
❌ Dict passing (no type safety)
```

---

## Proposed Architecture (After)

```
┌─────────────────────────────────────────────────────────────┐
│                  CLI Layer (tools/cli/)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │judge_cli.py  │  │ phase_cli.py │  │ llm_cli.py   │     │
│  │              │  │              │  │              │     │
│  │ • ~100 lines │  │ • ~100 lines │  │ • ~50 lines  │     │
│  │ • argparse   │  │ • argparse   │  │ • argparse   │     │
│  │ • formatting │  │ • formatting │  │ • formatting │     │
│  │ • exit codes │  │ • exit codes │  │ • exit codes │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                  ↓                  ↓             │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Business Logic (tools/core/)                  │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                    judge.py                          │  │
│  │  • ~150 lines                                        │  │
│  │  • Pure logic (no print, no sys.exit)               │  │
│  │  • Returns Verdict objects                          │  │
│  │  • Gate registry pattern                            │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              phase_controller.py                     │  │
│  │  • ~200 lines                                        │  │
│  │  • review_phase() / advance_phase()                 │  │
│  │  • Orchestrates test runner, judge                  │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │test_     │  │ llm_     │  │ state.py │  │gates/    │  │
│  │runner.py │  │reviewer  │  │          │  │          │  │
│  │~100 lines│  │~150 lines│  │~200 lines│  │base.py   │  │
│  │          │  │          │  │All I/O   │  │tests.py  │  │
│  │          │  │          │  │here      │  │docs.py   │  │
│  └──────────┘  └──────────┘  └──────────┘  │drift.py  │  │
│                                             └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│               Domain Models (tools/models/)                 │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ phase.py │ │ plan.py  │ │verdict.py│ │gate_     │      │
│  │          │ │          │ │          │ │result.py │      │
│  │@dataclass│ │@dataclass│ │@dataclass│ │@dataclass│      │
│  │Type-safe │ │Validates │ │Serialize │ │Serialize │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 Utilities (tools/lib/)                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐      │
│  │ git_ops  │ │  scope   │ │  traces  │ │  guard   │      │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    External Systems                         │
│         Git  •  Pytest  •  Ruff  •  Anthropic API          │
└─────────────────────────────────────────────────────────────┘

Benefits:
✅ Clear separation: CLI → Core → Models → Utils
✅ Reusable API (can import Judge, PhaseController)
✅ Type safety (domain models enforce contracts)
✅ Testability (core logic has zero I/O)
✅ Extensibility (gate pattern, plugin architecture ready)
```

---

## Data Flow: Review Phase

### Before (Current)

```
User runs: ./tools/phasectl.py review P01-scaffold
           ↓
    phasectl.py:review_phase(phase_id)
           ↓
    ├─ Load plan.yaml (dict)
    ├─ Show diff (print to console)
    ├─ Run tests (subprocess + print)
    │     └─ Write .repo/traces/last_test.txt
    ├─ Run lint (subprocess + print)
    │     └─ Write .repo/traces/last_lint.txt
    ├─ Invoke judge.py (subprocess)
    │     ↓
    │  judge.py:judge_phase(phase_id)
    │     ↓
    │  ├─ Load plan.yaml (dict, again)
    │  ├─ Check artifacts (dict) → issues list
    │  ├─ Check tests (read trace) → issues list
    │  ├─ Check docs (dict) → issues list
    │  ├─ Check drift (dict) → issues list
    │  ├─ Check LLM (if enabled) → issues list
    │  └─ Write verdict
    │        ├─ .repo/critiques/P01.md
    │        ├─ .repo/critiques/P01.json
    │        └─ .repo/critiques/P01.OK (if approved)
    │
    └─ Read .repo/critiques/P01.OK or .repo/critiques/P01.md
           └─ Print result and exit

Issues:
• Plan loaded twice (inefficient)
• State passed as dicts (error-prone)
• I/O scattered across 2 files
• print() mixed with logic
• Hard to test (requires subprocess)
```

### After (Proposed)

```
User runs: ./tools/cli/phase_cli.py review P01-scaffold
           ↓
    PhaseController.review_phase(phase_id) → ReviewResult
           ↓
    ├─ Load Phase (typed object from state.get_phase())
    ├─ DiffSummary = git_ops.get_diff_summary(phase)
    ├─ TestResult = test_runner.run(phase)
    ├─ LintResult = linter.run(phase) [if enabled]
    ├─ Verdict = judge.evaluate_phase(phase)
    │     ↓
    │  Judge.evaluate_phase(phase: Phase) → Verdict
    │     ↓
    │  for gate in self.gates:
    │     if gate.applies_to(phase):
    │        result = gate.check(phase, context)
    │        results.append(result)
    │        if not result.passed and result.blocking:
    │           break
    │  return Verdict(phase_id, results, approved)
    │
    └─ state.write_verdict(verdict)
           └─ .repo/critiques/P01.json (single source of truth)

CLI formats ReviewResult and prints to console

Benefits:
• Plan loaded once, passed as typed object
• Pure functions (testable without I/O)
• Single source of truth for verdict
• Clear data flow (no hidden state)
• Easy to use programmatically
```

---

## Gate Extension Example

### Before (Current)

**To add a new gate, you must:**
1. Edit `judge.py` (547 lines)
2. Add check logic inline (~30 lines)
3. Add to `all_issues` list
4. Update documentation
5. Risk breaking existing gates

**Example: Adding security gate**
```python
# Edit judge.py at line ~500
def judge_phase(phase_id: str):
    # ... existing gates ...
    
    # New gate (inserted manually)
    print("  🔍 Checking security...")
    security_issues = check_security(phase)  # Where do we define this?
    gate_results["security"] = security_issues
    all_issues.extend(security_issues)
    
    # ... rest of function ...
```

### After (Proposed)

**To add a new gate:**
1. Create `tools/core/gates/security_gate.py`
2. Implement `Gate` interface
3. Register in `Judge.__init__`
4. Done! (No changes to judge.py logic)

**Example: Adding security gate**
```python
# tools/core/gates/security_gate.py
class SecurityGate(Gate):
    """Runs bandit security scanner on Python files."""
    
    @property
    def name(self) -> str:
        return "security"
    
    def applies_to(self, phase: Phase) -> bool:
        """Only run if security gate configured."""
        return "security" in phase.gates
    
    def check(self, phase: Phase, context: Context) -> GateResult:
        """Run bandit and return result."""
        cmd = ["bandit", "-r", str(context.repo_root)]
        result = subprocess.run(cmd, capture_output=True)
        
        passed = result.returncode == 0
        messages = [] if passed else ["Security issues found"]
        
        return GateResult(
            gate_name="security",
            passed=passed,
            messages=messages,
            blocking=True
        )

# Register in judge.py (only change needed)
class Judge:
    def __init__(self, repo_root: Path):
        self.gates = [
            ProtocolIntegrityGate(),
            ArtifactsGate(),
            TestsGate(),
            DocsGate(),
            DriftGate(),
            LLMReviewGate(),
            SecurityGate(),  # ← One line added
        ]
```

**Benefits:**
- ✅ Gate logic isolated (testable independently)
- ✅ No risk of breaking existing gates
- ✅ Clear interface contract
- ✅ Self-documenting (Gate ABC defines requirements)

---

## File Organization

### Before (Current)

```
tools/
├── judge.py              (547 lines: CLI + gates + I/O)
├── phasectl.py           (472 lines: CLI + orchestration + I/O)
├── llm_judge.py          (223 lines: LLM review)
├── generate_manifest.py  (utility)
├── lib/
│   ├── file_lock.py      ✅ Well-scoped
│   ├── git_ops.py        ✅ Well-scoped
│   ├── plan_validator.py ✅ Well-scoped
│   ├── protocol_guard.py ✅ Well-scoped
│   ├── scope.py          ✅ Well-scoped
│   └── traces.py         ✅ Well-scoped
```

### After (Proposed)

```
tools/
├── cli/                  # Presentation layer
│   ├── judge_cli.py      (~100 lines: argparse + formatting)
│   ├── phase_cli.py      (~100 lines: argparse + formatting)
│   └── llm_cli.py        (~50 lines: argparse + formatting)
│
├── core/                 # Business logic
│   ├── judge.py          (~150 lines: gate orchestration)
│   ├── phase_controller.py  (~200 lines: review/advance)
│   ├── test_runner.py    (~100 lines: pytest execution)
│   ├── llm_reviewer.py   (~150 lines: LLM review)
│   ├── state.py          (~200 lines: all .repo/ I/O)
│   └── gates/            # Gate implementations
│       ├── base.py       (Gate ABC + Context)
│       ├── artifacts_gate.py
│       ├── tests_gate.py
│       ├── docs_gate.py
│       ├── drift_gate.py
│       └── llm_gate.py
│
├── models/               # Domain models
│   ├── phase.py          (@dataclass Phase)
│   ├── plan.py           (@dataclass Plan)
│   ├── verdict.py        (@dataclass Verdict)
│   └── gate_result.py    (@dataclass GateResult)
│
├── lib/                  # Utilities (unchanged)
│   ├── file_lock.py
│   ├── git_ops.py
│   ├── plan_validator.py
│   ├── protocol_guard.py
│   ├── scope.py
│   └── traces.py
│
└── generate_manifest.py  (unchanged)
```

**Benefits:**
- Clear responsibility boundaries
- Easy to navigate (find what you need)
- Logical grouping (CLI, core, models, utils)
- Testable (can import core without CLI)

---

## Testing Strategy

### Before (Current)

```
tests/
├── conftest.py           (empty)
├── mvp/
│   ├── test_golden.py    (demo)
│   └── test_feature.py   (demo)
├── test_scope_matching.py    ✅ Good coverage
└── test_test_scoping.py      ✅ Good coverage

Issues:
❌ No tests for judge.py (547 lines untested!)
❌ No tests for phasectl.py (472 lines untested!)
❌ No integration tests
❌ No property-based tests
```

### After (Proposed)

```
tests/
├── conftest.py           (shared fixtures)
│
├── unit/                 # Isolated component tests
│   ├── models/
│   │   ├── test_phase.py
│   │   ├── test_verdict.py
│   │   └── test_gate_result.py
│   ├── gates/
│   │   ├── test_artifacts_gate.py
│   │   ├── test_tests_gate.py
│   │   ├── test_docs_gate.py
│   │   └── test_drift_gate.py
│   ├── core/
│   │   ├── test_judge.py
│   │   ├── test_phase_controller.py
│   │   ├── test_test_runner.py
│   │   └── test_state.py
│   ├── cli/
│   │   ├── test_judge_cli.py
│   │   └── test_phase_cli.py
│   └── lib/
│       ├── test_scope.py (existing)
│       ├── test_git_ops.py
│       └── test_protocol_guard.py
│
├── integration/          # End-to-end workflows
│   ├── test_review_cycle.py
│   ├── test_phase_advancement.py
│   ├── test_protocol_integrity.py
│   └── test_llm_review.py
│
├── property/             # Invariant testing
│   ├── test_scope_invariants.py
│   ├── test_serialization.py
│   └── test_git_invariants.py
│
└── fixtures/             # Test data
    ├── sample_repo/
    └── sample_plan.yaml

Target coverage: >80%
```

---

## Key Metrics

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| **judge.py lines** | 547 | ~150 | ↓ 73% |
| **phasectl.py lines** | 472 | ~200 (core) + ~100 (CLI) | Separated |
| **Total LoC** | 2,751 | ~2,500 | ↓ 9% |
| **Avg function length** | ~45 | <30 | ↓ 33% |
| **Cyclomatic complexity** | ~12 | <8 | ↓ 33% |
| **Test coverage** | ~40% | >80% | ↑ 100% |
| **Time to add gate** | 2 hours | 30 min | ↓ 75% |
| **Gate testability** | Hard | Easy | ✅ |
| **Programmatic use** | No | Yes | ✅ |

---

## Migration Path

### Week 1: Models (Non-breaking)
```
✅ Add tools/models/
✅ Coexist with dicts initially
✅ Gradually replace dict passing
✅ No user-facing changes
```

### Week 2: Gates (Non-breaking)
```
✅ Add tools/core/gates/
✅ Refactor judge.py to use gates
✅ Keep same behavior
✅ No user-facing changes
```

### Week 3: Tests (Additive)
```
✅ Add tests/integration/
✅ No changes to existing code
✅ No user-facing changes
```

### Week 4-6: CLI/Core (Careful)
```
⚠️ Split CLI from core
⚠️ Keep old entry points as shims
⚠️ Deprecation warnings for 6 months
```

### Week 7-9: Polish (Low-risk)
```
✅ Documentation
✅ Type hints
✅ Property tests
✅ No breaking changes
```

---

## Summary

**Core transformation:**
- From: Monolithic tools with mixed concerns
- To: Layered architecture with clear boundaries

**Key benefits:**
1. **Simplicity**: Smaller, focused modules
2. **Clarity**: Explicit interfaces and types
3. **Structure**: Clean layering (CLI → Core → Models → Utils)
4. **Testability**: Pure functions, mockable dependencies
5. **Extensibility**: Plugin pattern for gates

**Risk level: LOW**
- Incremental changes
- Backwards compatible during transition
- Comprehensive tests prevent regressions

**Timeline: 9 weeks**
- Phase 1 (Weeks 1-3): Foundation
- Phase 2 (Weeks 4-6): Simplification  
- Phase 3 (Weeks 7-9): Quality

**Next step:** Review STRATEGIC_AUDIT.md and REFACTORING_ROADMAP.md, then begin Week 1 (Domain Models).
