# Judge-Gated Orchestration System

A minimal, terminal-native orchestration layer for autonomous Claude Code execution with enforced quality gates.

## 🎯 Goals

- **Autonomous execution**: Execute clearly-defined roadmap chunks without constant supervision
- **Quality control**: Automatic validation of tests, docs, and plan adherence at each phase
- **Plan drift prevention**: Enforce scope boundaries and detect out-of-scope changes
- **Transparent traces**: Emit evaluation data for each phase (pass/fail, timing, drift metrics)
- **Drop-in ready**: Works entirely via files and git—no external APIs or plugin dependencies

## 📁 Structure

```
.
├── .repo/
│   ├── briefs/           # Phase instructions (what to build)
│   │   ├── P01-scaffold.md
│   │   ├── P02-impl-feature.md
│   │   └── CURRENT.json  # Points to active phase
│   ├── critiques/        # Judge feedback (pass/fail)
│   ├── status/           # Phase status tracking
│   ├── traces/           # Test output and metrics
│   └── plan.yaml         # Full roadmap definition
├── tools/
│   ├── phasectl.py       # Controller (review/next commands)
│   ├── run_tests.sh      # Test runner
│   ├── run_judge.sh      # Judge trigger
│   └── judge.py          # Judge logic (gates enforcement)
├── src/mvp/              # Implementation code
├── tests/mvp/            # Test suite
└── docs/                 # Documentation
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Review Current Phase

```bash
cat .repo/briefs/CURRENT.json
```

This shows which phase is active (initially `P01-scaffold`).

### 3. Read the Brief

```bash
cat .repo/briefs/P01-scaffold.md
```

### 4. Execute Phase Work

Follow the brief instructions to implement required artifacts.

### 5. Submit for Review

```bash
./tools/phasectl.py review P01-scaffold
```

This will:
- Run tests (`pytest tests/`)
- Invoke the judge to check gates
- Output either a critique or approval

### 6. Handle Feedback

**If critique appears:**
```bash
cat .repo/critiques/P01-scaffold.md
```

Fix issues and re-run review.

**If approved:**
```bash
./tools/phasectl.py next
```

Advances to the next phase.

## ⚙️ How It Works

### Phase Workflow

```
1. Claude reads brief (.repo/briefs/<PHASE>.md)
2. Claude implements artifacts within scope
3. Claude runs: ./tools/phasectl.py review <PHASE>
   ├─> Runs tests (pytest)
   ├─> Triggers judge
   └─> Judge checks:
       ├─ Artifacts exist
       ├─ Tests pass
       ├─ Docs updated
       ├─ No plan drift
       └─ Lint rules (if any)
4. Judge writes:
   ├─ .repo/critiques/<PHASE>.md (if issues found)
   └─ .repo/critiques/<PHASE>.OK (if approved)
5. If approved: ./tools/phasectl.py next → advance to next phase
   If critique: fix issues → re-run review
```

### Quality Gates

Each phase defines gates in `.repo/plan.yaml`:

- **tests**: Must pass (`must_pass: true`)
- **docs**: Must update specified files (`must_update: [...]`)
- **drift**: Allowed out-of-scope changes (`allowed_out_of_scope_changes: 0`)
- **lint**: Code quality rules (e.g., `max_cyclomatic_complexity: 12`)

### Judge Logic

The judge (`tools/judge.py`):
1. Loads phase config from `plan.yaml`
2. Validates all gates
3. Produces critique if any gate fails
4. Writes `.OK` marker if all gates pass

### Controller

The controller (`tools/phasectl.py`) orchestrates:
- `review <PHASE>`: Submit phase for evaluation (blocking)
- `next`: Advance to next phase after approval

## 📋 Demo Phases

### Phase P01: Scaffold
- Create `src/mvp/__init__.py` with `hello_world()` function
- Add golden test in `tests/mvp/test_golden.py`
- Document in `docs/mvp.md`
- Gates: tests pass, docs updated, zero drift

### Phase P02: Implement Feature
- Add `src/mvp/feature.py` with `calculate_score()` function
- Add tests in `tests/mvp/test_feature.py`
- Update docs with feature section
- Gates: tests pass, docs updated, complexity < 12, zero drift

## 🧪 Testing

Run all tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/mvp/test_golden.py -v
```

## 📊 Traces

Test output is saved to `.repo/traces/last_pytest.txt` for judge evaluation.

## 🔮 Future Extensions

- **File-event triggers**: Use `inotifywait` for instant feedback
- **Metrics tracking**: Record TCR, coverage, drift in `.repo/traces/*.jsonl`
- **MCP integration**: Connect to Model Context Protocol for observability
- **Multi-judge types**: Add performance, style, security reviewers
- **One-K integration**: Send traces to governance platform

## 🎓 Usage for Claude Code

When working with this system:

1. **Read** `.repo/briefs/CURRENT.json` to identify active phase
2. **Study** the brief at the path specified
3. **Implement** only files within the phase scope
4. **Review** via `./tools/phasectl.py review <PHASE_ID>`
5. **Iterate** on critique feedback until approved
6. **Advance** via `./tools/phasectl.py next`

The system ensures you stay on track, maintain quality, and never drift from the plan.

## 📄 License

MIT
