# Phase P02: Implement Feature

## Objective
Implement a simple feature with refactoring and documentation section.

## Scope
**Include:**
- `src/mvp/feature.py`
- `tests/mvp/test_feature.py`
- `docs/mvp.md`

## Required Artifacts
- [ ] `src/mvp/feature.py` - Feature implementation
- [ ] `tests/mvp/test_feature.py` - Feature tests

## Gates
- **Tests:** Must pass
- **Docs:** Must update `docs/mvp.md#feature` section
- **Lint:** Max cyclomatic complexity 12
- **Drift:** 0 allowed out-of-scope changes

## Implementation Steps

1. **Create feature module**
   - Create `src/mvp/feature.py`
   - Implement a `calculate_score(value: int) -> int` function
   - Function should validate input and return value * 2
   - Keep cyclomatic complexity below 12

2. **Create feature tests**
   - Create `tests/mvp/test_feature.py`
   - Test valid inputs (positive, zero, negative)
   - Test edge cases
   - Ensure all tests pass

3. **Update documentation**
   - Add a "## Feature" section to `docs/mvp.md`
   - Document the `calculate_score` function
   - Include usage examples

4. **Submit for review**
   - Run: `./tools/phasectl.py review P02-impl-feature`
   - Wait for judge feedback
   - If critique appears, fix issues and re-run review
   - When approved, pipeline is complete!

## 4-Step Protocol

1. **Read** this brief and understand scope boundaries
2. **Implement** only files within the defined scope
3. **Review** via `./tools/phasectl.py review P02-impl-feature`
4. **Iterate** until judge approves, then complete
