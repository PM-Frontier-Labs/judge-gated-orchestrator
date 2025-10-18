# Phase P01: Scaffold

## Objective
Create skeleton module with golden test and initial documentation.

## Scope 🎯

| Allowed ✅ | Forbidden ❌ |
|-----------|-------------|
| `src/mvp/**` | `requirements.txt` |
| `tests/mvp/**` | `pyproject.toml` |
| `docs/mvp.md` | `src/**/legacy/**` |
| | Other modules |

**If you need forbidden files:** Stop and create a separate phase.

## Required Artifacts
- [ ] `src/mvp/__init__.py` - Module initialization
- [ ] `tests/mvp/test_golden.py` - Golden path test
- [ ] `docs/mvp.md` - Initial documentation

## Gates
- **Tests:** Must pass
- **Docs:** Must update `docs/mvp.md`
- **Drift:** 0 out-of-scope changes allowed (enforced)

## Implementation Steps

1. **Create module** → `src/mvp/__init__.py` with `hello_world()` function
2. **Create test** → `tests/mvp/test_golden.py` that validates function
3. **Create docs** → `docs/mvp.md` with module purpose and API
4. **Submit review** → `./tools/phasectl.py review P01-scaffold`
5. **Iterate** → Fix any critique issues and re-review
6. **Advance** → `./tools/phasectl.py next` when approved

## 4-Step Protocol

1. **Read** this brief and understand scope boundaries
2. **Implement** only files within the defined scope
3. **Review** via `./tools/phasectl.py review P01-scaffold`
4. **Iterate** until judge approves, then advance with `./tools/phasectl.py next`
