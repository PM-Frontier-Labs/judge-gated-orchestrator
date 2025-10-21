#!/bin/bash
# Quick orientation for new Claude Code instances

echo "════════════════════════════════════════════════════════════════"
echo "  Judge-Gated Orchestration - Status"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Protocol status
echo "🔧 PROTOCOL STATUS"
echo "────────────────────────────────────────────────────────────────"
if [ -f "tools/phasectl.py" ]; then
    echo "Protocol tools: ✅ Available"
    if ./tools/phasectl.py discover >/dev/null 2>&1; then
        echo "Protocol health: ✅ Healthy"
    else
        echo "Protocol health: ❌ Issues detected"
        echo "   Run: ./tools/phasectl.py discover"
    fi
else
    echo "Protocol tools: ❌ Missing"
    echo "   Run: ../judge-gated-orchestrator/install-protocol.sh"
fi
echo ""

# Current phase
echo "📍 CURRENT PHASE"
echo "────────────────────────────────────────────────────────────────"
if [ -f .repo/briefs/CURRENT.json ]; then
    PHASE_ID=$(cat .repo/briefs/CURRENT.json | grep -o '"phase_id"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)"/\1/')
    BRIEF_PATH=$(cat .repo/briefs/CURRENT.json | grep -o '"brief_path"[[:space:]]*:[[:space:]]*"[^"]*"' | sed 's/.*"\([^"]*\)"/\1/')
    echo "Phase: $PHASE_ID"
    echo "Brief: $BRIEF_PATH"
else
    echo "⚠️  No CURRENT.json found"
fi
echo ""

# Progress
echo "📊 PROGRESS"
echo "────────────────────────────────────────────────────────────────"
TOTAL_PHASES=$(grep "id:" .repo/plan.yaml | grep -v "plan:" | wc -l | tr -d ' ')
COMPLETED=$(ls .repo/critiques/*.OK 2>/dev/null | wc -l | tr -d ' ')
echo "Completed phases: $COMPLETED/$TOTAL_PHASES"
if [ $COMPLETED -gt 0 ]; then
    echo "✅ Approved:"
    ls .repo/critiques/*.OK 2>/dev/null | xargs -n1 basename | sed 's/.OK$//' | sed 's/^/   - /'
fi
echo ""

# Current status
echo "🔍 CURRENT STATUS"
echo "────────────────────────────────────────────────────────────────"
if [ -n "$PHASE_ID" ]; then
    if [ -f .repo/critiques/${PHASE_ID}.OK ]; then
        echo "✅ Phase approved - ready to advance"
        echo "   Run: ./tools/phasectl.py next"
    elif [ -f .repo/critiques/${PHASE_ID}.md ]; then
        echo "❌ Critique exists - needs fixes"
        echo "   Read: cat .repo/critiques/${PHASE_ID}.md"
        echo ""
        echo "Issues:"
        grep "^- " .repo/critiques/${PHASE_ID}.md 2>/dev/null | head -3
    else
        echo "⏳ No review yet - ready to implement or submit"
        echo "   Run: ./tools/phasectl.py review $PHASE_ID"
    fi
fi
echo ""

# Automatic Intelligence Status
echo "🧠 AUTOMATIC INTELLIGENCE STATUS"
echo "────────────────────────────────────────────────────────────────"
if [ -n "$PHASE_ID" ]; then
    # Check for patterns
    PATTERNS_FILE=".repo/collective_intelligence/patterns.jsonl"
    if [ -f "$PATTERNS_FILE" ]; then
        PATTERN_COUNT=$(wc -l < "$PATTERNS_FILE" 2>/dev/null || echo "0")
        echo "📚 Auto-captured patterns: $PATTERN_COUNT"
    else
        echo "📚 Auto-captured patterns: 0"
    fi
    
    # Check for attribution data
    ATTRIBUTION_FILE=".repo/state/attribution.jsonl"
    if [ -f "$ATTRIBUTION_FILE" ]; then
        ATTRIBUTION_COUNT=$(wc -l < "$ATTRIBUTION_FILE" 2>/dev/null || echo "0")
        echo "📊 Attribution records: $ATTRIBUTION_COUNT"
    else
        echo "📊 Attribution records: 0"
    fi
    
    # Check for generalization scores
    GEN_FILE=".repo/state/generalization.json"
    if [ -f "$GEN_FILE" ]; then
        echo "🎯 Generalization scores: Available"
    else
        echo "🎯 Generalization scores: None yet"
    fi
    
    # Check for budget shaping
    BUDGET_FILE=".repo/state/next_budget.json"
    if [ -f "$BUDGET_FILE" ]; then
        echo "💰 Budget shaping: Active"
    else
        echo "💰 Budget shaping: Default"
    fi
else
    echo "⚠️  No active phase - run ./tools/phasectl.py start <phase-id>"
fi
echo ""

# Git status
echo "📝 GIT STATUS"
echo "────────────────────────────────────────────────────────────────"
CHANGED=$(git status --short 2>/dev/null | wc -l | tr -d ' ')
if [ $CHANGED -eq 0 ]; then
    echo "No changes (working tree clean)"
else
    echo "Files changed: $CHANGED"
    git status --short 2>/dev/null | head -5
    if [ $CHANGED -gt 5 ]; then
        echo "   ... and $((CHANGED - 5)) more"
    fi
fi
echo ""

# Next steps
echo "🎯 NEXT STEPS"
echo "────────────────────────────────────────────────────────────────"
if [ -n "$PHASE_ID" ]; then
    if [ -f .repo/critiques/${PHASE_ID}.OK ]; then
        echo "1. Advance: ./tools/phasectl.py next"
        echo "2. Read new brief"
        echo "3. Start implementation"
    elif [ -f .repo/critiques/${PHASE_ID}.md ]; then
        echo "1. Read critique: cat .repo/critiques/${PHASE_ID}.md"
        echo "2. Fix issues"
        echo "3. Re-submit: ./tools/phasectl.py review $PHASE_ID"
    else
        echo "1. Read brief: cat $BRIEF_PATH"
        echo "2. Implement required files"
        echo "3. Submit: ./tools/phasectl.py review $PHASE_ID"
    fi
fi
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "📚 Docs: GETTING_STARTED.md | README.md"
echo "════════════════════════════════════════════════════════════════"

# Mark that orient.sh was run (for protocol enforcement)
mkdir -p .repo
touch .repo/.orient_run_timestamp
