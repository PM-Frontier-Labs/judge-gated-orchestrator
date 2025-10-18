# Phase P02: Implement Feature

## Objective
Implement feature with tests and documentation.

## Scope 🎯

| Allowed ✅ | Forbidden ❌ |
|-----------|-------------|
| `src/mvp/feature.py` | `requirements.txt` |
| `tests/mvp/test_feature.py` | `pyproject.toml` |
| `docs/mvp.md` | `.github/**` |
| | Other modules |

**If you need forbidden files:** Stop and create a separate phase.

## Required Artifacts
- [ ] `src/mvp/feature.py` - Feature implementation
- [ ] `tests/mvp/test_feature.py` - Feature tests

## Gates
- **Tests:** Must pass
- **Docs:** Must update `docs/mvp.md#feature` section
- **LLM Review:** Enabled (semantic code quality check)
- **Drift:** 0 out-of-scope changes allowed (enforced)

## Implementation Steps

1. **Create feature** → `src/mvp/feature.py` with `calculate_score(value: int) -> int`
   - Validates input and returns value * 2
2. **Create tests** → `tests/mvp/test_feature.py`
   - Test valid inputs (positive, zero, negative)
   - Test edge cases and type validation
3. **Update docs** → Add "## Feature" section to `docs/mvp.md`
   - Document function and usage examples
4. **Submit review** → `./tools/phasectl.py review P02-impl-feature`
5. **Iterate** → Fix any critique issues and re-review
6. **Complete** → Pipeline finished when approved!

## 4-Step Protocol

1. **Read** this brief and understand scope boundaries
2. **Implement** only files within the defined scope
3. **Review** via `./tools/phasectl.py review P02-impl-feature`
4. **Iterate** until judge approves, then complete
