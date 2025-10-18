# Key Insights to Preserve During Re-architecture

## 1. Governance ≠ Runtime Split
- **Problem**: Circular locks when plan.yaml, CURRENT.json, scopes treated as immutable
- **Solution**: Split plan.yaml (human-locked governance) from .repo/state/ (AI-writable runtime)
- **Implementation**: Judge reads Pxx.ctx.json, not plan.yaml for runtime state
- **Files**: `.repo/state/Pxx.ctx.json`, `tools/lib/state.py`

## 2. Amendment System
- **Problem**: Static plan in dynamic world needs scoped, auditable tweaks
- **Solution**: Bounded mutability with budgets (add_scope:2, set_test_cmd:1)
- **Implementation**: YAML files in .repo/amendments/, auto-applied during review
- **Files**: `.repo/amendments/pending/`, `.repo/amendments/applied/`, `tools/lib/amendments.py`

## 3. State Machine
- **Problem**: Need controlled flexibility during execution
- **Solution**: EXPLORE → LOCK modes with auto-flip on first green
- **Implementation**: Mode field in Pxx.ctx.json with enforcement
- **Files**: Mode field in state files, enforcement in judge

## 4. Collective Intelligence
- **Problem**: No memory, kept relearning fixes
- **Solution**: JSONL pattern storage with auto-proposal
- **Implementation**: .repo/collective_intelligence/patterns.jsonl
- **Files**: `.repo/collective_intelligence/patterns.jsonl`, pattern functions in `tools/lib/traces.py`

## 5. LLM Pipeline
- **Problem**: Judge too dumb/brittle, couldn't help recover
- **Solution**: Critic → Verifier → Arbiter pipeline proposing amendments
- **Implementation**: LLM proposes fixes, doesn't edit files
- **Files**: `tools/lib/llm_pipeline.py`, integration in `tools/judge.py`

## 6. Enhanced Briefs
- **Problem**: Briefs lacked context and guardrails
- **Solution**: Hints from retros + guardrails from state
- **Implementation**: Brief enhancement during load
- **Files**: Micro-retro functions in `tools/lib/traces.py`, enhancement in `tools/phasectl.py`

## 7. Known Issues Matcher
- **Problem**: Common failures repeated without learning
- **Solution**: Pre-LLM pattern matching for 30-50% failure reduction
- **Implementation**: Simple regex patterns with auto-proposal
- **Files**: Pattern matching functions in `tools/lib/traces.py`

## 8. Outer Loop Learning
- **Problem**: No self-reflection or learning from execution
- **Solution**: Micro-retrospectives after each phase
- **Implementation**: .repo/traces/Pxx.outer.json files
- **Files**: `.repo/traces/Pxx.outer.json`, retro functions in `tools/lib/traces.py`

## Implementation Principles

### Keep Simple
- **Functions over classes**: Use simple functions, not complex class hierarchies
- **File operations over databases**: Use JSONL, YAML, JSON files
- **Direct imports over sys.path**: Clean, simple imports
- **Single entry point**: Everything through `phasectl.py`

### Maintain Protocol Philosophy
- **"This is a protocol, not a framework"**
- **"You don't import classes, you write files that match conventions"**
- **"You don't learn an API, you run shell commands"**
- **Files are the API**

### Surgical Integration
- **Minimal changes to GitHub foundation**
- **Add features as simple extensions**
- **Preserve clean architecture**
- **Maintain single responsibility**

## Success Metrics
- **Files**: 10 Python files (vs current 32)
- **Lines**: ~3,200 total lines (vs current 7,650)
- **CLI Tools**: 1 main tool (vs current 6)
- **Classes**: 0-2 classes (vs current 15+)
- **Complexity**: 60% reduction while preserving all functionality
