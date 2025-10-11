#!/bin/bash
# Test script for LLM judge

echo "🔍 Testing LLM Judge Integration"
echo ""

# Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "❌ ANTHROPIC_API_KEY not set"
    echo ""
    echo "To set it, run:"
    echo "  export ANTHROPIC_API_KEY='sk-ant-your-key-here'"
    echo ""
    echo "Or get a key from: https://console.anthropic.com/settings/keys"
    echo ""
    exit 1
fi

echo "✓ ANTHROPIC_API_KEY is set"
echo ""

# Run the review
echo "Running review for P02-impl-feature..."
echo ""

cd "$(dirname "$0")"
./tools/phasectl.py review P02-impl-feature
