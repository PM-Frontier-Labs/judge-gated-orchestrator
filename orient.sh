#!/bin/bash
# Quick orientation for new Claude Code instances

echo "════════════════════════════════════════════════════════════════"
echo "  Judge-Gated Orchestration - Status"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Intelligence status
echo "🧠 INTELLIGENCE STATUS"
echo "────────────────────────────────────────────────────────────────"
if [ -n "$PHASE_ID" ]; then
    # Check for patterns
    PATTERNS_FILE=".repo/collective_intelligence/patterns.jsonl"
    if [ -f "$PATTERNS_FILE" ]; then
        PATTERN_COUNT=$(wc -l < "$PATTERNS_FILE" 2>/dev/null || echo "0")
        echo "📚 Stored patterns: $PATTERN_COUNT"
    else
        echo "📚 Stored patterns: 0"
    fi
    
    # Check for amendments
    AMENDMENTS_DIR=".repo/amendments/pending"
    if [ -d "$AMENDMENTS_DIR" ]; then
        AMENDMENT_COUNT=$(ls "$AMENDMENTS_DIR"/*.yaml 2>/dev/null | wc -l | tr -d ' ')
        echo "📝 Pending amendments: $AMENDMENT_COUNT"
    else
        echo "📝 Pending amendments: 0"
    fi
    
    # Show mechanism opportunities
    echo "🎯 Available mechanisms:"
    echo "   - ./tools/phasectl.py patterns list (check patterns)"
    echo "   - ./tools/phasectl.py amend propose (propose amendments)"
    echo "   - ./tools/phasectl.py recover (recover from corruption)"
else
    echo "⚠️  No active phase - run ./tools/phasectl.py start <phase-id>"
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
