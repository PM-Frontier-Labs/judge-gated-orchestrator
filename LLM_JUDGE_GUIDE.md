# LLM Judge Integration Guide

## What Was Added

The judge now supports **optional LLM-based code review** using Claude to check:
- Architecture and design patterns
- Code clarity and naming
- Complexity and maintainability
- Edge case handling
- Documentation quality
- Type safety
- Python best practices

## Files Modified/Created

1. **requirements.txt** - Added `anthropic>=0.39.0`
2. **tools/llm_judge.py** - New module with LLM review logic (~160 lines)
3. **tools/judge.py** - Integrated LLM review (~10 lines added)
4. **.repo/plan.yaml** - Enabled LLM review for P02

## How It Works

### 1. Rule-Based Gates (Always Run)
```
✓ Artifacts exist
✓ Tests pass
✓ Docs updated
✓ No plan drift
✓ Lint rules
```

### 2. LLM Review (Runs If Enabled)
```
🤖 Sends code to Claude
🤖 Gets semantic feedback
🤖 Adds issues to critique
```

## Usage

### Step 1: Set Your API Key

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Or add to a `.env` file:
```bash
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .env
source .env
```

### Step 2: Enable in Plan

Edit `.repo/plan.yaml`:

```yaml
- id: P02-impl-feature
  gates:
    tests: { must_pass: true }
    llm_review: { enabled: true }  # ← Add this
```

### Step 3: Run Review

```bash
./tools/phasectl.py review P02-impl-feature
```

**Output with LLM:**
```
📋 Submitting phase P02-impl-feature for review...
🧪 Running tests...
⚖️  Invoking judge...
  🔍 Checking artifacts... ✓
  🔍 Checking tests... ✓
  🔍 Checking documentation... ✓
  🔍 Checking for plan drift... ✓
  🔍 Checking lint rules... ✓
  🤖 Running LLM code review...     ← NEW!
✅ Phase P02-impl-feature approved!
```

## Testing Without API Key

If `ANTHROPIC_API_KEY` is not set:

```bash
./tools/phasectl.py review P02-impl-feature
```

**Output:**
```
❌ Phase P02-impl-feature needs revision:

## Issues Found
- LLM review enabled but ANTHROPIC_API_KEY not set in environment
```

This ensures you know LLM review is enabled but can't run.

## Example LLM Critique

If Claude finds issues:

```markdown
# Critique: P02-impl-feature

## Issues Found

- Code quality: Function `calculate_score` should validate upper bounds to prevent integer overflow
- Code quality: Consider adding type hints to return values for better IDE support
- Code quality: Missing docstring example for edge case with negative numbers
- Code quality: Error handling could be more specific about which validation failed

## Resolution

Please address the issues above and re-run:
./tools/phasectl.py review P02-impl-feature
```

## Disabling LLM Review

### Option 1: Remove from Plan
```yaml
gates:
  tests: { must_pass: true }
  # llm_review: { enabled: true }  ← Comment out or remove
```

### Option 2: Set to False
```yaml
gates:
  llm_review: { enabled: false }
```

### Option 3: Don't Set API Key
If no API key is set, LLM review will error (by design - you know it's configured but not running).

## Cost Estimates

Typical review (2-3 files, ~200 lines):
- **Tokens:** ~1,500 input + ~500 output
- **Cost:** ~$0.01 per review
- **Time:** 3-5 seconds

For a 10-phase project:
- **Total cost:** ~$0.10
- **Total time:** ~30-50 seconds added

## Advanced Configuration

You can customize the LLM review in `tools/llm_judge.py`:

```python
# Line 82: Change model
model="claude-sonnet-4-20250514"  # Or opus-4, haiku, etc.

# Line 83: Adjust token limit
max_tokens=2000  # Increase for longer critiques

# Line 84: Set temperature
temperature=0  # 0 = deterministic, 1 = creative
```

## Tips

1. **Use for high-stakes phases** - Enable LLM review for critical implementations
2. **Skip for scaffolding** - Don't enable for simple setup phases (P01)
3. **Combine with manual review** - LLM catches patterns, you catch business logic
4. **Iterate on prompts** - Edit the prompt in `llm_judge.py` to focus on your needs

## Comparison

| Judge Type | Speed | Cost | Coverage |
|------------|-------|------|----------|
| **Rule-based** | 1s | $0 | Syntax, tests, files, scope |
| **+ LLM** | 4s | $0.01 | + Architecture, patterns, naming, edge cases |

## Troubleshooting

**Issue:** "LLM review enabled but anthropic package not installed"
- **Fix:** `pip install anthropic`

**Issue:** "LLM review enabled but ANTHROPIC_API_KEY not set"
- **Fix:** `export ANTHROPIC_API_KEY=sk-ant-...`

**Issue:** "LLM review failed: Connection timeout"
- **Fix:** Check internet connection, retry

**Issue:** LLM approves bad code
- **Fix:** Edit prompt in `llm_judge.py` lines 55-80 to be more strict

## Next Steps

With LLM judge integrated, you can:
1. Run autonomous reviews with semantic validation
2. Catch architecture issues early
3. Enforce coding standards automatically
4. Build "good trace" datasets for AI-Native development

Happy coding! 🚀
