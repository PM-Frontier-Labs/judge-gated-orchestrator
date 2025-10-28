# 🔧 Protocol Simplification Plan

## 🎯 **FINAL DECISION SUMMARY**

### **✅ KEEP (Proven Useful)**
1. **Planning** - Break work into phases
2. **`orient.sh`** - Enforce as gate before next phase
3. **Test checks** - Unit + integration
4. **Lint checks**
5. **LLM code feedback** (when enabled)
6. **Docs check**
7. **Learnings during phases** (if we keep, simplify)

### **❌ REMOVE (Creates Deadlocks/Complexity)**
1. **Replay gate + budget shaping**
2. **Scope amendment system**
3. **Pattern learning / collective intelligence**
4. **Hard scope enforcement** (replace with LLM intent validation)
5. **Two-tier scope** (inner/outer)
6. **Budget system**
7. **Maintenance burst**

### **🔄 REPLACE**
**Old:** Hard scope blocking (creates deadlocks)
```yaml
scope:
  include: ["frontend/package.json", ...]  # Must predict ALL files upfront
  # Agent can't predict lint cascades → deadlock
```

**New:** Intent + LLM drift evaluation
```yaml
intent: "Create modern frontend foundation"  # Just describe what you want
# No file list - agent changes what's needed
# LLM at review time judges if changes match intent
```

---

## 📋 **MULTI-STEP SURGICAL REMOVAL PLAN**

## **PHASE 1: Audit Current Code**

### **Step 1.1: Identify Files to Touch**
**Affected files:**
```
TO MODIFY:
- tools/phasectl.py (remove amendment/budget/pattern logic)
- tools/judge.py (replace scope gate with LLM intent evaluation)
- tools/lib/gates.py (remove drift gate, add intent gate)
- .repo/plan.yaml (update schema to use "intent" instead of "scope")

MAY NEED TOUCHING:
- tools/lib/state.py (simplify - remove budget/amendment state)
- tools/lib/amendments.py (delete entire file)
- tools/lib/traces.py (remove pattern learning functions)
- tools/lib/collective_intelligence.py (if exists, delete)

MINOR UPDATES:
- tools/lib/git_ops.py (keep as-is)
- tools/lib/scope.py (keep for backward compat, phase out)
```

### **Step 1.2: Map Feature to Code**
```python
# Features to remove → Code locations:

FEATURE: Budget shaping
├─ Function: apply_budget_shaping()
├─ File: tools/judge.py (lines ~1171-1245)
├─ Function: _apply_guardrailed_budget_shaping()
├─ State: .repo/state/next_budget.json
└─ Telemetry: .repo/state/generalization.json

FEATURE: Replay gate
├─ Function: run_replay_if_passed()
├─ File: tools/judge.py (lines ~707-761)
├─ Function: budget_for_replay(), run_phase_like()
└─ State: .repo/state/generalization.json

FEATURE: Scope amendments
├─ Function: propose_amendment(), apply_amendments()
├─ File: tools/lib/amendments.py (ENTIRE FILE)
├─ Calls in: tools/phasectl.py (lines ~654, 682)
└─ State: .repo/amendments/

FEATURE: Pattern learning
├─ Function: auto_capture_patterns_from_critique()
├─ File: tools/judge.py (lines ~1023-1071)
├─ Function: load_relevant_patterns(), store_pattern()
├─ File: tools/lib/traces.py (lines ~97-153)
└─ State: .repo/collective_intelligence/patterns.jsonl

FEATURE: Hard scope enforcement
├─ Function: check_drift() 
├─ File: tools/lib/gates.py (lines ~53-104)
├─ Function: check_drift()
├─ File: tools/judge.py (lines ~332-456)
└─ Logic: Hard pattern matching + block logic
```

---

## **PHASE 2: Update Schema**

### **Step 2.1: Plan.yaml Schema Changes**
**Old schema:**
```yaml
phases:
  - id: P01-foundation
    scope:
      include: ["frontend/package.json", ...]  # Rigid file list
      exclude: []
    gates:
      drift: { allowed_out_of_scope_changes: 0 }
```

**New schema:**
```yaml
phases:
  - id: P01-foundation
    intent: "Create modern frontend foundation with TypeScript, React, build tooling"  # Descriptive
    gates:
      intent_eval: { enabled: true }  # LLM judges drift
      # OR if user wants no drift checking at all:
      # (just remove this gate entirely)
```

**Migration strategy:**
- Auto-convert existing `scope.include` patterns → `intent` descriptions
- Warn if `scope.exclude` was used (becomes ignored)
- Update plan validator

### **Step 2.2: Update Plan Validator**
**File:** `tools/lib/plan_validator.py`
- Remove scope validation (lines ~179-201)
- Remove drift gate validation (lines ~296-315)
- Add `intent` field validation
- Remove `experimental_features.replay_budget` validation

---

## **PHASE 3: Update Gate System**

### **Step 3.1: Replace DriftGate with IntentGate**
**File:** `tools/lib/gate_interface.py`

**Delete:**
```python
class DriftGate(GateInterface):
    # DELETE ENTIRE CLASS - hard scope checking
```

**Add:**
```python
class IntentGate(GateInterface):
    """Gate that validates changed files match phase intent via LLM."""
    
    @property
    def name(self) -> str:
        return "intent"
    
    @property
    def description(self) -> str:
        return "Validate changes match phase intent"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        intent_gate = phase.get("gates", {}).get("intent_eval", {})
        return intent_gate.get("enabled", True)  # Default on
    
    def run(self, phase, plan, context):
        from .gates import check_intent_match
        return check_intent_match(phase, context, changed_files)
```

**File:** `tools/lib/gates.py`

**Delete:**
```python
def check_drift(phase, plan, baseline_sha):
    # DELETE - hard scope enforcement
```

**Add:**
```python
def check_intent_match(phase, context, changed_files):
    """Check if changed files match phase intent using LLM."""
    
    intent = phase.get("intent")
    if not intent:
        return []  # No intent defined = allow anything
    
    # Only check if gates passed (don't waste LLM call on broken gates)
    test_result = check_test_gate_passed(context)
    lint_result = check_lint_gate_passed(context)
    
    if not (test_result and lint_result):
        return []  # Gates failed - judge will handle that
    
    # Call LLM to evaluate drift
    return evaluate_intent_with_llm(intent, changed_files)
```

### **Step 3.2: Implement LLM Intent Evaluation**
**Function:** `evaluate_intent_with_llm(intent, changed_files)`
```python
def evaluate_intent_with_llm(intent: str, changed_files: List[str], context: Dict) -> List[str]:
    """
    Use LLM to judge if changed files match phase intent.
    Returns list of stray files that don't match, or [] if OK.
    """
    
    if not changed_files:
        return []
    
    # Group files by directory for cleaner analysis
    files_by_dir = {}
    for f in changed_files:
        dir_path = os.path.dirname(f) or "."
        if dir_path not in files_by_dir:
            files_by_dir[dir_path] = []
        files_by_dir[dir_path].append(os.path.basename(f))
    
    prompt = f"""
You are evaluating a phase of work against its stated intent.

Phase Intent: "{intent}"

Files changed ({len(changed_files)} total):
{_format_files_for_llm(files_by_dir)}

Test results: {context.get('test_result')}
Lint results: {context.get('lint_result')}

Question: Which files (if any) appear to be unrelated to the stated intent?

Consider:
- If a "frontend foundation" phase touched backend/, that's likely unrelated
- If a "fix lint" phase touched all files with formatting, that's FINE
- If intent is "create new feature X" but changes are to unrelated feature Y, that's drift

Respond with JSON:
{{
  "stray_files": ["path/to/unrelated/file.js", ...],
  "reasoning": "Brief explanation"
}}

If all files relate to the intent, return {{"stray_files": [], "reasoning": "..."}}.
"""
    
    # Call LLM
    response = llm_client.generate(prompt, model="claude-3.5-sonnet")
    result = json.loads(response)
    
    stray_files = result.get("stray_files", [])
    if stray_files:
        return stray_files
    
    return []  # No drift detected
```

---

## **PHASE 4: Remove Amendment System**

### **Step 4.1: Delete Amendment File**
**File:** `tools/lib/amendments.py` - **DELETE ENTIRE FILE**

**Functions being removed:**
- `propose_amendment()`
- `apply_amendments()`
- `load_pending_amendments()`
- `record_amendment()`

**Directories to delete:**
- `.repo/amendments/pending/`
- `.repo/amendments/applied/`

### **Step 4.2: Remove Amendment Logic from phasectl.py**
**File:** `tools/phasectl.py`

**Find and delete:**
```python
# Line ~654: amend command
def cmd_amend(args):
    """Propose runtime scope changes."""
    # DELETE ENTIRE FUNCTION

# Line ~682: amend logic in start_phase
if args.amend:
    apply_amendments(repo_root, phase_id)  # DELETE THIS BLOCK

# Line ~[wherever amendments are applied]:
from lib.amendments import apply_amendments  # DELETE IMPORT
```

---

## **PHASE 5: Remove Budget Shaping**

### **Step 5.1: Remove from judge.py**
**File:** `tools/judge.py`

**Delete functions:**
- `apply_budget_shaping()` (lines ~1171-1245)
- `_apply_guardrailed_budget_shaping()` (if exists)
- `budget_for_replay()` (if exists)
- State loading for `generalization.json`, `next_budget.json`

**Delete logic:**
```python
# Line ~1023-1071: auto_capture_patterns
def auto_capture_patterns_from_critique(...):
    # DELETE ENTIRE FUNCTION

# Line ~707-761: run_replay_if_passed
def run_replay_if_passed(...):
    # DELETE ENTIRE FUNCTION
```

### **Step 5.2: Remove Pattern Learning**
**File:** `tools/lib/traces.py`

**Delete functions:**
- `load_relevant_patterns()`
- `store_pattern()`
- `auto_capture_patterns()` 
- Any pattern-specific loading/saving logic

**Keep:**
- Basic trace recording
- Command history

**Delete directory:**
- `.repo/collective_intelligence/`

---

## **PHASE 6: Simplify State Management**

### **Step 6.1: Simplify State Storage**
**File:** `tools/lib/state.py`

**Remove state fields:**
- `amendment_budget`
- `amendment_usage`
- `experimental_features`
- `pattern_learning_enabled`

**Keep:**
- `baseline_sha`
- `test_cmd` (if used)
- `mode` (if used)
- Basic phase state

**New simplified `CURRENT.json` structure:**
```json
{
  "active_phase": "P01-foundation",
  "baseline_sha": "abc123...",
  "status": "implementation_started",
  "started_at": 1234567890
}
```

---

## **PHASE 7: Update Main Entry Points**

### **Step 7.1: Update judge.py Entry Point**
**File:** `tools/judge.py`

**In `judge_phase()` function:**

**Delete:**
- Load generalization state
- Load next_budget state
- Apply budget shaping
- Auto-capture patterns
- Replay gate logic

**Add:**
- If `intent_eval` gate enabled → run `IntentGate`
- Otherwise skip drift checking

**Flow:**
```python
def judge_phase(phase_id):
    # Load plan, phase, baseline
    # Run deterministic gates (tests, lint, docs)
    # If they pass AND intent_eval enabled:
    #   - Run IntentGate
    #   - If drift found → critique with stray files
    # Write approval or critique
```

### **Step 7.2: Update phasectl.py Commands**
**File:** `tools/phasectl.py`

**Remove commands:**
- `phasectl amend` (delete function)
- Any budget-related commands

**Update commands:**
- `phasectl start` → enforce workflow, capture baseline
- `phasectl review` → run simplified judge
- `phasectl next` → transition to next phase (no budget logic)

---

## **PHASE 8: Update Documentation**

### **Step 8.1: Update PROTOCOL.md**
**Remove sections:**
- Amendment system
- Budget shaping
- Pattern learning
- Scope prediction (replace with intent)

**Add sections:**
- Intent definition
- LLM drift evaluation
- Simplified workflow diagram

### **Step 8.2: Update AGENT_WORKFLOW_PROMPT.md**
**Changes:**
- Remove amendment instructions
- Replace scope instructions with intent
- Update judge expectations
- Remove budget management instructions

---

## **PHASE 9: Testing & Validation**

### **Step 9.1: Test New Intent Gate**
**Test cases:**
1. **Intent:** "Create frontend foundation" + only frontend files changed → PASS
2. **Intent:** "Create frontend foundation" + backend files changed → FAIL (drift detected)
3. **Intent:** "Fix all lint errors" + 200 files formatted → PASS (context understood)
4. **No intent defined** → PASS (legacy mode)

### **Step 9.2: Validate State Transitions**
- Start phase → no budget
- Review phase → LLM intent check runs
- Next phase → no amendment application

### **Step 9.3: Test Backward Compatibility**
- Existing plans with `scope` → convert to `intent`
- Old `.repo/amendments/` directory → not needed
- Old `generalization.json` → not needed

---

## **PHASE 10: Cleanup**

### **Step 10.1: Remove Obsolete Directories**
```bash
# Delete in .repo/
rm -rf .repo/amendments/
rm -rf .repo/collective_intelligence/
rm -f .repo/state/generalization.json
rm -f .repo/state/next_budget.json

# Delete tool files
rm tools/lib/amendments.py  # ENTIRE FILE
rm tools/lib/upgrade_safety.py  # Already deleted
rm tools/lib/llm_pipeline.py  # Already deleted
```

### **Step 10.2: Update Git History**
**Add commit message:**
```
refactor: Remove budget shaping, amendments, pattern learning

Simplified protocol by removing experimental features that caused deadlocks:
- Delete amendment system (replace with intent-based LLM evaluation)
- Delete budget shaping and replay gate
- Delete pattern learning
- Replace hard scope enforcement with LLM intent validation

BREAKING CHANGE: Plans must migrate from "scope" to "intent" field
```

---

## 🎯 **IMPLEMENTATION ORDER**

### **Recommended Execution Sequence:**

1. **Phase 1** (Audit) - Map features to code
2. **Phase 2** (Schema) - Add `intent` support
3. **Phase 3** (Gates) - Replace DriftGate with IntentGate
4. **Phase 4** (Amendments) - Delete amendment system
5. **Phase 5** (Budget) - Remove budget shaping
6. **Phase 6** (State) - Simplify state management
7. **Phase 7** (Entry Points) - Update judge & phasectl
8. **Phase 8** (Docs) - Update documentation
9. **Phase 9** (Testing) - Validate changes
10. **Phase 10** (Cleanup) - Delete obsolete files

---

## 🔍 **RISK ASSESSMENT**

### **High Risk**
- Breaking existing plans (mitigation: migration helper)
- LLM evaluation slowdown (mitigation: only if gates pass)
- Hidden dependencies (mitigation: refactor in phases)

### **Medium Risk**
- State file incompatibilities (mitigation: version migration)
- Test failures (mitigation: update tests in Phase 9)

### **Low Risk**
- Documentation drift (mitigation: cleanup in Phase 8)
- Git cleanup (mitigation: safe deletion)

---

## 🧪 **SUCCESS CRITERIA**

1. ✅ No compilation errors
2. ✅ All existing plans migrate successfully
3. ✅ `CURRENT.json` structure simplified
4. ✅ No deadlocks from scope issues
5. ✅ LLM catches real drift (not legitimate cascades)
6. ✅ All deterministic gates (tests, lint, docs) work as before

---

## 📊 **COMMUNICATION PLAN**

- Update `CHANGELOG.md` with breaking changes
- Create migration guide for existing plans
- Add examples of `intent` vs old `scope` in docs
- Write release notes explaining simplification rationale

---

## 🎯 **KEY BENEFITS OF THIS PLAN**

1. **Eliminates deadlocks** - No more budget/shape/amend conflicts
2. **Context-aware** - LLM understands cascades vs actual drift
3. **Simpler to use** - Write `intent` instead of predicting files
4. **Keeps proven features** - Tests, lint, docs, LLM review all preserved
5. **Surgical changes** - Removes specific problematic code, keeps core
6. **Easy to revert** - Deletions tracked, schema changes documented
