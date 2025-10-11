# Quick Test: LLM Judge

## Option 1: Test With Your Anthropic API Key

### Step 1: Get Your API Key

If you don't have one:
1. Go to https://console.anthropic.com/settings/keys
2. Create a new API key
3. Copy it

### Step 2: Set the Key and Test

```bash
cd /Users/henryec/judge-gated-orchestrator

# Set your key (replace with your actual key)
export ANTHROPIC_API_KEY='sk-ant-api03-...'

# Run the test
./test_llm_judge.sh
```

### Expected Output

```
🔍 Testing LLM Judge Integration

✓ ANTHROPIC_API_KEY is set

Running review for P02-impl-feature...

📋 Submitting phase P02-impl-feature for review...
🧪 Running tests...
⚖️  Invoking judge...
  🔍 Checking artifacts... ✓
  🔍 Checking tests... ✓
  🔍 Checking documentation... ✓
  🔍 Checking for plan drift... ✓
  🔍 Checking lint rules... ✓
  🤖 Running LLM code review... ✓
✅ Phase P02-impl-feature approved!
```

---

## Option 2: Test Without API Key (Skip LLM Review)

Disable LLM review temporarily:

```bash
cd /Users/henryec/judge-gated-orchestrator

# Edit plan.yaml - change enabled to false
sed -i '' 's/llm_review: { enabled: true }/llm_review: { enabled: false }/' .repo/plan.yaml

# Test
./tools/phasectl.py review P02-impl-feature
```

---

## Option 3: See a Demo (I'll Use My Key)

I can test it for you if you want to see the output without setting up your own key first.

---

Which option would you like?
