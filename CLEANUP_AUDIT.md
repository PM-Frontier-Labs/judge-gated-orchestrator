# Repository Cleanup Audit - Post v2 Cutover

**Date:** 2025-10-28  
**Context:** After successful v2 cutover (79% code reduction)

---

## Executive Summary

The repository contains significant obsolete content from the v1→v2 transition:
- **Total size to remove:** ~149MB (mostly frontend/)
- **Files to delete:** 45+ files
- **Documentation to consolidate:** 8 documents
- **Test files to remove:** 8 obsolete test files

**Impact:** Cleaner repository, easier onboarding, reduced confusion

---

## Audit Findings

### 1. Obsolete Code Directories

#### ❌ `v2/` directory (140KB)
**Status:** DELETE
**Reason:** v2 code has been moved to `tools/`. Only docs remain here.
**Contents:**
- `v2/tools/` → Already copied to `tools/`
- `v2/tests/` → Obsolete v2-specific tests
- `v2/COMPARISON.md` → Transition doc, no longer needed
- `v2/IMPLEMENTATION_SUMMARY.md` → Transition doc
- `v2/MIGRATION.md` → Transition doc
- `v2/README.md` → v2 architecture (already in ARCHITECTURE.md)
- `v2/orient.sh` → Already replaced root orient.sh

**Action:** Delete entire directory

#### ❌ `tools-v1-backup/` directory (216KB)
**Status:** DELETE
**Reason:** v1 backup preserved in git history. Cutover was weeks ago.
**Contents:**
- Complete v1 codebase (5,895 lines)
- v1 lib modules
- v1 judge.py, phasectl.py, llm_judge.py

**Action:** Delete entire directory
**Safety:** Full v1 code preserved in git history at commit e84aa1a~1

#### ❌ `frontend/` directory (148MB)
**Status:** DELETE
**Reason:** Unrelated to judge protocol. Separate "Frontier Orchestrator" UI project.
**Contents:**
- React/TypeScript frontend
- 10,991 node_modules files
- Separate project with own package.json

**Action:** Delete or move to separate repository
**Note:** This appears to be a completely separate project

#### ❌ `src/mvp/` directory
**Status:** DELETE
**Reason:** Demo code for testing protocol. Not core functionality.
**Contents:**
- `feature.py` - Simple demo function
- `__init__.py` - Hello world function
- Only used by tests/mvp/test_*.py

**Action:** Delete if not needed for examples

---

### 2. Obsolete Documentation

#### ❌ Cutover/Transition Documents (DELETE)

1. **CUTOVER_COMPLETE.md** (5.4KB)
   - Purpose: Announce v2 cutover completion
   - Status: Historical record, no longer needed
   - Action: DELETE

2. **CUTOVER_PLAN.md** (7.1KB)
   - Purpose: Plan for v1→v2 transition
   - Status: Transition complete, obsolete
   - Action: DELETE

3. **V2_COMPLETE.md** (8.0KB)
   - Purpose: v2 implementation announcement
   - Status: Implementation complete, obsolete
   - Action: DELETE

4. **IMPLEMENTATION_COMPLETE.md** (10.5KB)
   - Purpose: v2 delivery summary
   - Status: Transition complete, obsolete
   - Action: DELETE

5. **START_HERE.md** (3.7KB)
   - Purpose: v2 transition quick start
   - Status: Obsolete, use GETTING_STARTED.md instead
   - Action: DELETE

6. **PROTOCOL_SIMPLIFICATION_PLAN.md** (15.2KB)
   - Purpose: Plan for v2 simplification
   - Status: Completed, historical only
   - Action: DELETE

7. **DELIVERY_SUMMARY.txt** (11.3KB)
   - Purpose: Summary of v2 delivery
   - Status: Transition complete, obsolete
   - Action: DELETE

**Total to delete:** 61.2KB of transition documentation

#### ❌ Redundant Prompt Files (DELETE)

1. **AGENT_UPDATE_PROMPT.md** (1.1KB)
   - Purpose: Prompt for updating agent
   - Status: Unclear purpose, possibly obsolete
   - Action: DELETE or consolidate into GETTING_STARTED.md

2. **AGENT_WORKFLOW_PROMPT.md** (1.8KB)
   - Purpose: Workflow prompt for agents
   - Status: Already covered in PROTOCOL.md
   - Action: DELETE

3. **SUMMARY.md** (11.9KB)
   - Purpose: Project summary
   - Status: Redundant with README.md
   - Action: DELETE or consolidate

#### ❌ Old Scripts (DELETE)

1. **orient-v1.sh** (6.7KB)
   - Purpose: v1 orient script
   - Status: v1 is backed up, no longer needed
   - Action: DELETE

---

### 3. Obsolete Test Files

#### ❌ Tests for Removed v1 Features (DELETE)

1. **test_collective_intelligence.py**
   - Tests for collective intelligence feature (removed in v2)
   - Action: DELETE

2. **test_collective_intelligence_consolidation.py**
   - Tests for CI consolidation (removed in v2)
   - Action: DELETE

3. **test_rearchitecture.py**
   - Tests for v1→v2 rearchitecture
   - Action: DELETE (transition complete)

4. **test_atomic_writes.py**
   - Tests for v1 atomic writes (if removed in v2)
   - Action: VERIFY if v2 still uses, then DELETE or KEEP

5. **test_gate_interface.py**
   - Tests for v1 gate interface
   - Action: VERIFY if v2 still uses, then DELETE or KEEP

6. **test_pathspec_requirement.py**
   - Tests for pathspec requirement
   - Action: VERIFY if v2 still uses, then DELETE or KEEP

7. **test_scope_matching.py**
   - Tests for scope matching
   - Action: VERIFY if v2 still uses, then DELETE or KEEP

8. **test_test_scoping.py**
   - Tests for test scoping
   - Action: VERIFY if v2 still uses, then DELETE or KEEP

#### ❌ Root Test Files (DELETE)

1. **test_baseline.py**
   - Root-level test, should be in tests/
   - Action: DELETE or move to tests/

2. **test_enhanced_baseline.py**
   - Root-level test, should be in tests/
   - Action: DELETE or move to tests/

#### 📁 Tests to Keep (tests/mvp/)
- **test_golden.py** - MVP demo tests
- **test_feature.py** - Feature tests
- Keep these if src/mvp/ is kept for examples

---

### 4. Documentation to Update

#### 🔄 README.md (UPDATE)
**Issues:**
- Still references v1 features (replay, amendments, etc.)
- Line counts show v1 numbers
- Comparison table includes removed features

**Actions:**
- Remove v1 feature descriptions
- Update line counts to reflect v2
- Remove experimental feature references
- Remove replay/amendments/attribution/telemetry sections
- Simplify to focus on current v2 features

#### 🔄 PROTOCOL.md (UPDATE)
**Issues:**
- 36KB file with extensive v1 feature documentation
- Documents removed features:
  - Replay gate
  - Budget shaping
  - Pattern auto-injection
  - Two-tier scope
  - Amendments
  - Attribution tracking
  - Collective intelligence

**Actions:**
- Remove all v1 feature documentation
- Focus on v2's 7 core features
- Remove experimental feature sections
- Simplify to current v2 capabilities
- Reduce file size significantly (target: <10KB)

#### 🔄 ARCHITECTURE.md (UPDATE)
**Issues:**
- References v1 architecture components
- May include removed modules

**Actions:**
- Verify all content is still accurate for v2
- Remove references to removed modules
- Update module descriptions to match v2

---

### 5. Files to Keep

#### ✅ Core Documentation
- **README.md** (update for v2)
- **PROTOCOL.md** (update for v2)
- **GETTING_STARTED.md** (current, keep)
- **GITHUB_SETUP.md** (current, keep)
- **ARCHITECTURE.md** (update for v2)

#### ✅ Active Code
- **tools/** (v2 active code)
- **orient.sh** (v2 active script)
- **install-protocol.sh** (needed for setup)

#### ✅ Dependencies
- **requirements.txt** (keep)
- **requirements-llm.txt** (keep)

#### ✅ Active Tests
- **tests/conftest.py** (keep)
- **tests/test_gates.py** (keep)
- **tests/mvp/** (keep if src/mvp/ kept)

---

## Cleanup Plan

### Phase 1: Safe Deletions (Directories)

```bash
# 1. Delete v2 source directory (code already in tools/)
rm -rf v2/

# 2. Delete v1 backup (preserved in git)
rm -rf tools-v1-backup/

# 3. Delete frontend (unrelated project)
rm -rf frontend/

# 4. Delete demo code (if not needed)
rm -rf src/
```

**Space saved:** ~149MB

### Phase 2: Documentation Cleanup

```bash
# Delete transition docs
rm -f CUTOVER_COMPLETE.md
rm -f CUTOVER_PLAN.md
rm -f V2_COMPLETE.md
rm -f IMPLEMENTATION_COMPLETE.md
rm -f START_HERE.md
rm -f PROTOCOL_SIMPLIFICATION_PLAN.md
rm -f DELIVERY_SUMMARY.txt

# Delete redundant/obsolete docs
rm -f AGENT_UPDATE_PROMPT.md
rm -f AGENT_WORKFLOW_PROMPT.md
rm -f SUMMARY.md

# Delete old scripts
rm -f orient-v1.sh
```

**Files removed:** 11 documentation files

### Phase 3: Test Cleanup

```bash
# Delete obsolete v1 tests
rm -f tests/test_collective_intelligence.py
rm -f tests/test_collective_intelligence_consolidation.py
rm -f tests/test_rearchitecture.py

# Delete root test files
rm -f test_baseline.py
rm -f test_enhanced_baseline.py

# Verify and delete if obsolete:
# tests/test_atomic_writes.py
# tests/test_gate_interface.py
# tests/test_pathspec_requirement.py
# tests/test_scope_matching.py
# tests/test_test_scoping.py
```

### Phase 4: Update Documentation

1. **README.md**
   - Remove v1 features
   - Update line counts
   - Simplify feature table
   - Focus on v2 capabilities

2. **PROTOCOL.md**
   - Remove replay documentation
   - Remove budget shaping
   - Remove amendments/patterns
   - Remove experimental features
   - Reduce from 36KB to ~10KB

3. **ARCHITECTURE.md**
   - Verify v2 accuracy
   - Remove v1 module references

---

## Post-Cleanup Repository Structure

```
/workspace/
├── README.md                    # Main docs (updated)
├── PROTOCOL.md                  # Execution manual (updated)
├── GETTING_STARTED.md           # User guide
├── GITHUB_SETUP.md              # Setup instructions
├── ARCHITECTURE.md              # Architecture docs (updated)
├── install-protocol.sh          # Installation script
├── orient.sh                    # Context recovery
├── requirements.txt             # Dependencies
├── requirements-llm.txt         # Optional LLM deps
├── tools/                       # v2 active code
│   ├── judge.py
│   ├── phasectl.py
│   └── lib/
│       ├── gates.py
│       ├── git_ops.py
│       ├── plan.py
│       ├── scope.py
│       ├── state.py
│       └── traces.py
└── tests/                       # Active tests only
    ├── conftest.py
    └── test_gates.py
```

**Clean, minimal, v2-focused repository.**

---

## Risk Assessment

### Low Risk ✅
- Deleting v2/ (code in tools/)
- Deleting tools-v1-backup/ (in git)
- Deleting transition docs
- Deleting obsolete tests

### Medium Risk ⚠️
- Deleting frontend/ (verify not needed)
- Deleting src/mvp/ (used in tests)
- Updating PROTOCOL.md (extensive changes)

### Mitigation
- All deletions backed up in git
- Can restore from git history if needed
- Test suite should still pass after cleanup

---

## Expected Results

### Before Cleanup
- **Total files:** 11,000+ files (mostly node_modules)
- **Total size:** ~149MB
- **Documentation:** 20+ files, many redundant
- **Tests:** 12 files, 5 obsolete

### After Cleanup
- **Total files:** ~50 files
- **Total size:** ~500KB (99.7% reduction)
- **Documentation:** 5 core files, all current
- **Tests:** ~3-5 files, all relevant

### Benefits
1. ✅ **Clarity:** Only v2 content, no confusion
2. ✅ **Onboarding:** New users see only current system
3. ✅ **Maintenance:** Less to update and maintain
4. ✅ **Size:** 99%+ smaller repository
5. ✅ **Focus:** Single source of truth for v2

---

## Approval Required

Before executing cleanup:
1. ✅ Confirm frontend/ can be deleted (or moved to separate repo)
2. ✅ Confirm src/mvp/ not needed (or document as examples)
3. ✅ Review which test files are still needed
4. ✅ Approve massive PROTOCOL.md reduction

---

## Execution Checklist

- [ ] Phase 1: Delete directories (v2/, tools-v1-backup/, frontend/, src/)
- [ ] Phase 2: Delete transition documentation (11 files)
- [ ] Phase 3: Delete obsolete tests (5-8 files)
- [ ] Phase 4: Update README.md for v2
- [ ] Phase 5: Update PROTOCOL.md for v2
- [ ] Phase 6: Update ARCHITECTURE.md for v2
- [ ] Phase 7: Test remaining test suite
- [ ] Phase 8: Update .gitignore if needed
- [ ] Phase 9: Create cleanup summary
- [ ] Phase 10: Commit changes

---

## Next Steps

1. **Review this audit**
2. **Approve cleanup plan**
3. **Execute cleanup phases**
4. **Verify test suite passes**
5. **Commit clean v2 repository**

**Ready to proceed with cleanup?**
