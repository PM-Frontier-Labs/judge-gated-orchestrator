# Phase P01: Scaffold

## Objective
Create the skeleton module structure with a golden test and initial documentation.

## Scope 🎯

✅ **YOU MAY TOUCH:**
- `src/mvp/**` - Module code
- `tests/mvp/**` - Test files
- `docs/mvp.md` - Documentation

❌ **DO NOT TOUCH:**
- `requirements.txt` - Dependencies (use separate phase)
- `pyproject.toml` - Project config (use separate phase)
- `src/**/legacy/**` - Legacy code (excluded)
- Other modules outside `mvp/`

🤔 **IF YOU NEED TO TOUCH THESE:**
Stop and create a separate phase. Drift prevention will fail the review.

## Required Artifacts
- [ ] `src/mvp/__init__.py` - Module initialization
- [ ] `tests/mvp/test_golden.py` - Golden path test
- [ ] `docs/mvp.md` - Initial documentation

## Gates
- **Tests:** Must pass
- **Docs:** Must update `docs/mvp.md`
- **Drift:** 0 out-of-scope changes allowed (enforced)

## Implementation Steps

1. **Create module structure**
   - Create `src/mvp/__init__.py` with basic module setup
   - Add a simple `hello_world()` function for testing

2. **Create golden test**
   - Create `tests/mvp/test_golden.py`
   - Write a test that validates `hello_world()` returns expected value
   - Ensure test passes

3. **Create documentation**
   - Create `docs/mvp.md`
   - Document the module purpose and basic API

4. **Submit for review**
   - Run: `./tools/phasectl.py review P01-scaffold`
   - Wait for judge feedback
   - If critique appears, fix issues and re-run review
   - When approved, run: `./tools/phasectl.py next`

## 4-Step Protocol

1. **Read** this brief and understand scope boundaries
2. **Implement** only files within the defined scope
3. **Review** via `./tools/phasectl.py review P01-scaffold`
4. **Iterate** until judge approves, then advance with `./tools/phasectl.py next`
