# Refactoring Roadmap: Gated Phase Protocol

**Goal:** Improve simplicity, clarity, and structure while preserving protocol integrity  
**Timeline:** 9 weeks (3 phases)  
**Based on:** STRATEGIC_AUDIT.md

---

## Quick Start

### What to focus on first:
1. **Domain models** - Get data structures right (Week 1)
2. **Gate abstraction** - Make judge.py extensible (Week 2)
3. **Integration tests** - Protect against regressions (Week 3)

### What NOT to change yet:
- ❌ File format (.repo/ structure) - Wait until Phase 2
- ❌ plan.yaml schema - Breaking change, needs careful migration
- ❌ CLI commands - Keep stable API during refactor

---

## Phase 1: Foundation (Weeks 1-3)

### Week 1: Domain Models

**Create:** `tools/models/` package

```python
# tools/models/phase.py
@dataclass
class Phase:
    id: str
    description: str
    scope: Scope
    artifacts: Artifacts
    gates: Dict[str, Gate]
    drift_rules: DriftRules

# tools/models/verdict.py
@dataclass
class Verdict:
    phase_id: str
    timestamp: float
    approved: bool
    gate_results: List[GateResult]
    
    def to_json(self) -> dict:
        """Serialize to JSON format."""
    
    def to_markdown(self) -> str:
        """Generate human-readable critique."""

# tools/models/gate_result.py
@dataclass
class GateResult:
    gate_name: str
    passed: bool
    messages: List[str]
    blocking: bool = True
```

**Refactor:**
- Replace dict passing in judge.py with Phase objects
- Replace dict returns with Verdict objects
- Add validation in model constructors

**Tests:**
```python
tests/unit/models/test_phase.py
tests/unit/models/test_verdict.py
```

**Success criteria:**
- ✅ No dicts passed between judge.py and gates
- ✅ All models have type hints
- ✅ 100% test coverage on models

---

### Week 2: Gate Abstraction

**Create:** `tools/core/gates/` package

```python
# tools/core/gates/base.py
class Gate(ABC):
    """Base class for all quality gates."""
    
    @abstractmethod
    def applies_to(self, phase: Phase) -> bool:
        """Return True if this gate should run for this phase."""
    
    @abstractmethod
    def check(self, phase: Phase, context: Context) -> GateResult:
        """Execute gate check. Never raises, always returns GateResult."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Gate identifier (e.g., 'tests', 'drift')."""

# tools/core/gates/artifacts_gate.py
class ArtifactsGate(Gate):
    def applies_to(self, phase: Phase) -> bool:
        return bool(phase.artifacts.must_exist)
    
    def check(self, phase: Phase, context: Context) -> GateResult:
        issues = []
        for artifact in phase.artifacts.must_exist:
            path = context.repo_root / artifact
            if not path.exists():
                issues.append(f"Missing: {artifact}")
        return GateResult("artifacts", len(issues) == 0, issues)

# Similar for: TestsGate, DocsGate, DriftGate, LLMReviewGate
```

**Refactor judge.py:**
```python
# Before (143 lines, complexity ~15)
def judge_phase(phase_id: str):
    # Load plan (40 lines)
    # Check artifacts (10 lines)
    # Check tests (15 lines)
    # Check docs (15 lines)
    # Check drift (15 lines)
    # Check LLM (15 lines)
    # Write verdict (20 lines)

# After (~50 lines, complexity ~5)
class Judge:
    def __init__(self, repo_root: Path):
        self.context = Context(repo_root)
        self.gates = [
            ProtocolIntegrityGate(),  # Must run first
            ArtifactsGate(),
            TestsGate(),
            DocsGate(),
            DriftGate(),
            LLMReviewGate(),
        ]
    
    def evaluate_phase(self, phase_id: str) -> Verdict:
        phase = self._load_phase(phase_id)
        results = []
        
        for gate in self.gates:
            if gate.applies_to(phase):
                result = gate.check(phase, self.context)
                results.append(result)
                if not result.passed and result.blocking:
                    break  # Early exit on blocking failure
        
        approved = all(r.passed for r in results)
        return Verdict(phase_id, time.time(), approved, results)
```

**Tests:**
```python
tests/unit/gates/test_artifacts_gate.py
tests/unit/gates/test_tests_gate.py
tests/unit/gates/test_drift_gate.py
tests/unit/core/test_judge.py
```

**Success criteria:**
- ✅ judge.py < 100 lines
- ✅ All gates independently testable
- ✅ Adding new gate requires NO changes to judge.py

---

### Week 3: Integration Tests

**Create:** `tests/integration/` package

```python
# tests/integration/test_review_cycle.py
def test_happy_path_review_and_advance(tmp_git_repo):
    """Test: review passes → advance to next phase."""
    # Setup
    create_phase("P01-test", passing_tests=True)
    
    # Execute
    result = controller.review_phase("P01-test")
    
    # Assert
    assert result.approved == True
    assert critique_file_exists("P01-test.OK")
    
    # Advance
    controller.advance_phase()
    assert get_current_phase() == "P02-next"

def test_review_fails_then_succeeds(tmp_git_repo):
    """Test: review fails → fix → review passes."""
    # Setup
    create_phase("P01-test", failing_tests=True)
    
    # First review: fails
    result = controller.review_phase("P01-test")
    assert result.approved == False
    assert "Tests failed" in result.verdict.messages
    
    # Fix
    fix_tests()
    
    # Second review: passes
    result = controller.review_phase("P01-test")
    assert result.approved == True

def test_protocol_integrity_violation(tmp_git_repo):
    """Test: modifying judge.py blocks approval."""
    # Setup
    create_phase("P01-test", passing_tests=True)
    
    # Tamper with judge
    modify_file("tools/judge.py", "# malicious change")
    
    # Review fails immediately
    result = controller.review_phase("P01-test")
    assert result.approved == False
    assert "JUDGE TAMPER DETECTED" in result.verdict.messages

def test_drift_detection(tmp_git_repo):
    """Test: out-of-scope changes trigger drift gate."""
    # Setup
    create_phase("P01-test", scope=["src/foo/**"])
    modify_file("src/foo/allowed.py")  # In scope
    modify_file("src/bar/forbidden.py")  # Out of scope
    
    # Review
    result = controller.review_phase("P01-test")
    assert result.approved == False
    assert "Out-of-scope changes" in result.verdict.messages
    assert "src/bar/forbidden.py" in result.verdict.messages
```

**Test utilities:**
```python
# tests/integration/conftest.py
@pytest.fixture
def tmp_git_repo(tmp_path):
    """Create temporary git repo with protocol structure."""
    repo = tmp_path / "test_repo"
    setup_git_repo(repo)
    setup_protocol_files(repo)
    return repo

def setup_protocol_files(repo: Path):
    """Initialize .repo/ structure."""
    (repo / ".repo/briefs").mkdir(parents=True)
    (repo / ".repo/critiques").mkdir(parents=True)
    # ... etc
```

**Success criteria:**
- ✅ All critical paths covered (review, advance, tamper detection)
- ✅ Tests run in <10 seconds
- ✅ Tests are deterministic (no flakiness)

---

## Phase 2: Simplification (Weeks 4-6)

### Week 4: CLI/Core Separation

**Goal:** Separate presentation logic from business logic

**Before:**
```
tools/
├── judge.py (547 lines: CLI + business logic)
├── phasectl.py (472 lines: CLI + business logic)
```

**After:**
```
tools/
├── cli/
│   ├── judge_cli.py (100 lines: argparse + output formatting)
│   ├── phase_cli.py (100 lines: argparse + output formatting)
├── core/
│   ├── judge.py (150 lines: pure business logic)
│   ├── phase_controller.py (200 lines: pure business logic)
│   ├── test_runner.py (100 lines: test execution logic)
```

**Implementation:**

```python
# tools/core/judge.py
class Judge:
    """Business logic for phase evaluation."""
    
    def evaluate_phase(self, phase_id: str) -> Verdict:
        """
        Evaluate phase against all gates.
        
        Returns Verdict object. Never prints. Never exits.
        Raises JudgeError on unrecoverable errors.
        """
        # Pure logic, no print() calls
        return verdict

# tools/cli/judge_cli.py  
def main():
    """CLI entry point."""
    try:
        judge = Judge(REPO_ROOT)
        verdict = judge.evaluate_phase(phase_id)
        
        # Format output
        print(f"⚖️  Judging phase {verdict.phase_id}...")
        for result in verdict.gate_results:
            icon = "✅" if result.passed else "❌"
            print(f"{icon} {result.gate_name}")
        
        # Exit with appropriate code
        sys.exit(0 if verdict.approved else 1)
    
    except JudgeError as e:
        print(f"❌ Error: {e}")
        sys.exit(2)
```

**Migration:**
- Keep `tools/judge.py` as shim calling `cli/judge_cli.py` (backwards compat)
- Update documentation to reference new structure
- Deprecation notice for 6 months, then remove shim

**Tests:**
```python
tests/unit/cli/test_judge_cli.py  # Test output formatting
tests/unit/core/test_judge.py     # Test business logic
```

**Success criteria:**
- ✅ Zero print() calls in core/
- ✅ All business logic testable without subprocess
- ✅ CLI tests use capsys to verify output

---

### Week 5: State Management

**Goal:** Centralize all .repo/ file I/O

**Create:**
```python
# tools/core/state.py
class ProtocolState:
    """
    Manages all .repo/ file I/O operations.
    
    Ensures:
    - Atomic writes (temp file + rename)
    - Consistent error handling
    - Single source of truth for file paths
    """
    
    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.repo_dir = repo_root / ".repo"
    
    def write_verdict(self, verdict: Verdict):
        """Write verdict atomically (replaces write_critique/write_approval)."""
        # Write JSON
        json_file = self.repo_dir / "critiques" / f"{verdict.phase_id}.json"
        self._atomic_write_json(json_file, verdict.to_json())
        
        # Optionally generate MD for humans
        if not verdict.approved:
            md_file = self.repo_dir / "critiques" / f"{verdict.phase_id}.md"
            self._atomic_write(md_file, verdict.to_markdown())
    
    def get_current_phase(self) -> Phase:
        """Read CURRENT.json."""
        current_file = self.repo_dir / "briefs/CURRENT.json"
        data = json.loads(current_file.read_text())
        return Phase.from_json(data)
    
    def set_current_phase(self, phase: Phase):
        """Update CURRENT.json atomically."""
        current_file = self.repo_dir / "briefs/CURRENT.json"
        self._atomic_write_json(current_file, phase.to_json())
    
    def _atomic_write(self, path: Path, content: str):
        """Write file atomically using temp + rename."""
        # Implementation
    
    def _atomic_write_json(self, path: Path, data: dict):
        """Write JSON file atomically."""
        # Implementation
```

**Refactor:**
- Remove file I/O from judge.py
- Remove file I/O from phasectl.py
- All .repo/ access goes through ProtocolState

**Tests:**
```python
tests/unit/core/test_state.py
tests/unit/core/test_state_atomicity.py  # Test crash recovery
```

**Success criteria:**
- ✅ Single source of truth for all .repo/ paths
- ✅ All writes are atomic (tested with crash simulation)
- ✅ Zero direct Path(...).write_text() calls outside state.py

---

### Week 6: Simplify Critique Format

**Goal:** Eliminate redundant file formats

**Before:**
```
.repo/critiques/
├── P01-scaffold.md         # Human-readable
├── P01-scaffold.json       # Machine-readable (needs revision)
├── P01-scaffold.OK         # Approval marker
├── P01-scaffold.OK.json    # Machine-readable (approved)
```

**After:**
```
.repo/critiques/
├── P01-scaffold.json       # Single source of truth
├── P01-scaffold.md         # Generated from JSON (optional)
```

**JSON format:**
```json
{
  "phase": "P01-scaffold",
  "timestamp": 1729234567.0,
  "protocol_version": 1,
  "status": "approved",  // "approved" | "needs_revision"
  "gate_results": [
    {
      "gate": "tests",
      "passed": true,
      "messages": []
    }
  ]
}
```

**Migration strategy:**
1. Support both formats for 6 months
2. Auto-migrate on first review: `.OK` → `.json` with `status: "approved"`
3. Provide migration tool: `./tools/migrate_critiques.py`
4. Update documentation

**Implementation:**
```python
# tools/core/state.py
def write_verdict(self, verdict: Verdict):
    """Write verdict in new format."""
    json_file = self.critiques_dir / f"{verdict.phase_id}.json"
    self._atomic_write_json(json_file, {
        "phase": verdict.phase_id,
        "timestamp": verdict.timestamp,
        "protocol_version": 1,
        "status": "approved" if verdict.approved else "needs_revision",
        "gate_results": [r.to_json() for r in verdict.gate_results]
    })
    
    # Clean up old format files
    self._cleanup_legacy_files(verdict.phase_id)

def _cleanup_legacy_files(self, phase_id: str):
    """Remove .OK, .OK.json, and old .json files."""
    for ext in [".OK", ".OK.json"]:
        old_file = self.critiques_dir / f"{phase_id}{ext}"
        if old_file.exists():
            old_file.unlink()
```

**Tests:**
```python
tests/unit/core/test_verdict_format.py
tests/integration/test_legacy_format_migration.py
```

**Success criteria:**
- ✅ Single JSON file per phase
- ✅ Old format auto-migrates on first review
- ✅ Migration tool tested on real repos

---

## Phase 3: Quality (Weeks 7-9)

### Week 7: Documentation

**Add Architecture Decision Records (ADRs):**

```markdown
# docs/adr/001-file-based-protocol.md
# ADR 001: File-Based Protocol Over Framework

## Context
We need a way for autonomous AI agents to work through multi-phase projects
with quality enforcement. Traditional approaches use APIs or frameworks.

## Decision
Use a file-based protocol (.repo/ directory) similar to how Git uses .git/.

## Rationale
- Context-window proof: All state persists to disk
- Language-agnostic: Any tool can implement the protocol
- Terminal-native: No servers, no APIs
- Debuggable: Human-readable files

## Consequences
- (+) Extremely simple integration
- (+) Works across context windows
- (-) Requires file I/O for all operations
- (-) Not suitable for high-frequency operations (1000s of phases/sec)
```

**Add module docstrings:**
```python
# tools/core/judge.py
"""
Phase evaluation and quality gate execution.

The Judge is the trust anchor for autonomous execution. It:
1. Verifies protocol integrity (SHA256) before running any gates
2. Executes gates in sequence (early exit on blocking failures)
3. Returns structured Verdict (never exits process)

Gates are registered in __init__ and run in order. To add a new gate:
1. Implement Gate interface (see tools/core/gates/base.py)
2. Add to self.gates list in Judge.__init__
3. Configure in plan.yaml phases[].gates section

Example:
    judge = Judge(Path("/repo"))
    verdict = judge.evaluate_phase("P01-scaffold")
    if verdict.approved:
        print("Phase approved!")
"""
```

**Add "why" comments to complex logic:**
```python
# Before
if baseline_sha:
    result = subprocess.run(["git", "diff", f"{baseline_sha}...HEAD"])

# After  
# Use baseline_sha (captured at phase start) instead of merge-base
# to prevent false drift positives as base branch advances during
# long-running phases. See ADR-003 for rationale.
if baseline_sha:
    result = subprocess.run(["git", "diff", f"{baseline_sha}...HEAD"])
```

**Tasks:**
- [ ] Write ADRs for key decisions (file protocol, gate pattern, SHA256 integrity)
- [ ] Add module docstrings to all `tools/core/` modules
- [ ] Add "why" comments to algorithms in scope.py, git_ops.py
- [ ] Update PROTOCOL.md to reference ADRs

---

### Week 8: Type Safety

**Add mypy configuration:**
```toml
# pyproject.toml
[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_any_generics = true
check_untyped_defs = true

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false
```

**Add type hints:**
```python
# Before
def get_changed_files(repo_root, include_committed=True, base_branch="main"):
    # ...

# After
def get_changed_files(
    repo_root: Path,
    include_committed: bool = True,
    base_branch: str = "main",
    baseline_sha: Optional[str] = None
) -> List[str]:
    """
    Get changed files using git diff.
    
    Args:
        repo_root: Repository root directory
        include_committed: Include committed changes in addition to staged/unstaged
        base_branch: Branch for merge-base fallback (used if baseline_sha is None)
        baseline_sha: Fixed baseline commit for consistent diffs (preferred)
    
    Returns:
        List of relative file paths changed since baseline
    """
```

**Tasks:**
- [ ] Run `mypy tools/ --install-types`
- [ ] Fix all type errors in `tools/core/`
- [ ] Add type hints to all `tools/lib/` modules
- [ ] Add type hints to all test helpers
- [ ] Add CI check: `mypy tools/ --strict`

---

### Week 9: Property-Based Tests

**Add hypothesis tests for invariants:**

```python
# tests/property/test_scope_invariants.py
from hypothesis import given, strategies as st

@given(
    files=st.lists(st.text(min_size=1, max_size=50)),
    patterns=st.lists(st.text(min_size=1, max_size=20))
)
def test_classify_files_partition(files, patterns):
    """in_scope ∪ out_of_scope = all_files (partition invariant)."""
    in_scope, out_of_scope = classify_files(files, patterns, [])
    
    # Union equals original
    assert set(in_scope) | set(out_of_scope) == set(files)
    
    # No overlap (disjoint sets)
    assert set(in_scope) & set(out_of_scope) == set()

@given(
    files=st.lists(st.text(min_size=1)),
    include=st.lists(st.text(min_size=1)),
    exclude=st.lists(st.text(min_size=1))
)
def test_exclude_overrides_include(files, include, exclude):
    """If a file matches exclude, it's out of scope (even if matches include)."""
    in_scope, out_of_scope = classify_files(files, include, exclude)
    
    for file in files:
        if matches_any_pattern(file, exclude):
            assert file in out_of_scope

@given(st.data())
def test_gate_result_serialization_roundtrip(data):
    """GateResult.from_json(r.to_json()) == r (serialization invariant)."""
    result = data.draw(st.builds(
        GateResult,
        gate_name=st.text(min_size=1),
        passed=st.booleans(),
        messages=st.lists(st.text())
    ))
    
    serialized = result.to_json()
    deserialized = GateResult.from_json(serialized)
    
    assert result == deserialized
```

**Tasks:**
- [ ] Install hypothesis: `pip install hypothesis`
- [ ] Add property tests for scope.py (partition, exclusion)
- [ ] Add property tests for models (serialization roundtrip)
- [ ] Add property tests for git_ops.py (diff correctness)
- [ ] Run tests with `pytest --hypothesis-show-statistics`

---

## Success Criteria

### Code Quality Targets

| Metric | Before | Target | Measurement |
|--------|--------|--------|-------------|
| Lines of code | 2,751 | 2,500 | `find . -name "*.py" \| xargs wc -l` |
| Avg cyclomatic complexity | ~12 | <8 | `radon cc -a tools/` |
| Test coverage | ~40% | >80% | `pytest --cov=tools --cov-report=term` |
| Avg function length | ~45 | <30 | `radon raw -s tools/` |
| Type coverage | 0% | 100% | `mypy tools/ --strict` |

### Architecture Validation

- ✅ Can add new gate without modifying judge.py
- ✅ Can use Judge/PhaseController programmatically (no CLI dependency)
- ✅ All .repo/ I/O goes through ProtocolState
- ✅ Zero print() in tools/core/
- ✅ All critical paths covered by integration tests

### Documentation Completeness

- ✅ ADRs for all major design decisions
- ✅ Module docstrings explain "why" not just "what"
- ✅ Complex algorithms have inline explanations
- ✅ Migration guide for new critique format

---

## Risk Mitigation

### Breaking Changes

**High-risk changes:**
1. Critique file format change (.OK → .json)
2. CLI tool restructuring (judge.py → cli/judge_cli.py)

**Mitigation:**
- Support both formats for 6 months
- Keep old entry points as shims with deprecation warnings
- Provide auto-migration tool
- Comprehensive changelog

### Testing Strategy

**Before merging any refactor:**
1. Run existing tests: `pytest tests/ -v`
2. Run integration tests: `pytest tests/integration/ -v`
3. Run property tests: `pytest tests/property/ --hypothesis-show-statistics`
4. Manual smoke test: `./tools/phasectl.py review P01-scaffold`

### Rollback Plan

Each week's changes are independently deployable:
- Week 1: Models can coexist with dicts
- Week 2: Gate pattern can be feature-flagged
- Week 3: Integration tests are additive
- Week 4-6: CLI/Core separation can be phased

If issues arise, revert specific week's changes while keeping others.

---

## Maintenance

After completion, establish:

1. **Code quality checks in CI:**
   ```yaml
   # .github/workflows/quality.yml
   - name: Type check
     run: mypy tools/ --strict
   
   - name: Test coverage
     run: pytest --cov=tools --cov-fail-under=80
   
   - name: Complexity check
     run: radon cc -a -nc tools/
   ```

2. **Quarterly architecture reviews:**
   - Review new gates added
   - Check for layering violations
   - Update ADRs as needed

3. **Dependency updates:**
   - Use dependabot for automated PRs
   - Pin versions in requirements.txt
   - Test against latest Python versions

---

## Questions & Answers

**Q: Why not use an existing orchestration framework?**  
A: The file-based protocol is unique and enables autonomous agents to recover from context window exhaustion. No framework provides this.

**Q: Why such a heavy focus on testing?**  
A: The protocol is the trust anchor for autonomous execution. If gates can be bypassed, the entire system is compromised.

**Q: Can we skip the CLI/Core separation?**  
A: No. Without it, the protocol can't be used programmatically (e.g., from other tools, in CI, in tests).

**Q: Is 9 weeks too aggressive?**  
A: Timeline assumes 1 senior engineer full-time. Can extend to 12-15 weeks with 50% allocation.

---

**Next step:** Review STRATEGIC_AUDIT.md for detailed analysis, then start Week 1 (Domain Models).
