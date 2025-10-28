#!/bin/bash
# Orient.sh v2 - Enhanced context recovery

set -e

REPO_DIR=".repo"
CURRENT_FILE="$REPO_DIR/state/current.json"
LEARNINGS_FILE="$REPO_DIR/learnings.md"
CRITIQUES_DIR="$REPO_DIR/critiques"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  📍 PROJECT ORIENTATION                    ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if protocol v2 exists
if [ -d "v2/tools" ]; then
    echo -e "${BLUE}🆕 Protocol v2 Available${NC}"
    echo "   This project has the simplified v2 protocol"
    echo ""
fi

# Check if plan exists
if [ ! -f "$REPO_DIR/plan.yaml" ]; then
    echo -e "${RED}❌ No plan found${NC}"
    echo "   Create $REPO_DIR/plan.yaml to get started"
    exit 1
fi

# Get plan info
PLAN_ID=$(grep "^  id:" "$REPO_DIR/plan.yaml" | head -1 | awk '{print $2}')
echo -e "${GREEN}📋 Plan: $PLAN_ID${NC}"
echo ""

# Count phases
PHASE_COUNT=$(grep "^    - id:" "$REPO_DIR/plan.yaml" | wc -l | xargs)
echo -e "📊 Total Phases: $PHASE_COUNT"
echo ""

# Check current phase
if [ -f "$CURRENT_FILE" ]; then
    CURRENT_PHASE=$(python3 -c "import json; print(json.load(open('$CURRENT_FILE'))['phase_id'])" 2>/dev/null || echo "unknown")
    BASELINE_SHA=$(python3 -c "import json; print(json.load(open('$CURRENT_FILE'))['baseline_sha'][:8])" 2>/dev/null || echo "unknown")
    
    echo -e "${YELLOW}▶️  Current Phase: $CURRENT_PHASE${NC}"
    echo "   Baseline: $BASELINE_SHA"
    echo ""
    
    # Check status
    OK_FILE="$CRITIQUES_DIR/$CURRENT_PHASE.OK"
    CRITIQUE_FILE="$CRITIQUES_DIR/$CURRENT_PHASE.md"
    
    if [ -f "$OK_FILE" ]; then
        echo -e "${GREEN}✅ Status: APPROVED${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Reflect on learnings: ./v2/tools/phasectl.py reflect $CURRENT_PHASE"
        echo "  2. Advance: ./v2/tools/phasectl.py next"
    elif [ -f "$CRITIQUE_FILE" ]; then
        echo -e "${RED}❌ Status: NEEDS FIXES${NC}"
        echo ""
        echo "Review critique:"
        echo "  cat $CRITIQUE_FILE"
        echo ""
        echo "After fixing:"
        echo "  ./v2/tools/phasectl.py review $CURRENT_PHASE"
    else
        echo -e "${YELLOW}🔨 Status: IN PROGRESS${NC}"
        echo ""
        echo "When ready:"
        echo "  ./v2/tools/phasectl.py review $CURRENT_PHASE"
    fi
else
    echo -e "${YELLOW}⏸️  No Active Phase${NC}"
    echo ""
    
    # Find first phase
    FIRST_PHASE=$(grep "^    - id:" "$REPO_DIR/plan.yaml" | head -1 | awk '{print $3}')
    echo "Start first phase:"
    echo "  ./v2/tools/phasectl.py start $FIRST_PHASE"
fi

echo ""
echo "───────────────────────────────────────────────────────────"
echo ""

# Show recent learnings if they exist
if [ -f "$LEARNINGS_FILE" ]; then
    echo -e "${BLUE}💡 Recent Learnings${NC}"
    echo ""
    
    # Show last 3 learnings
    tail -n 30 "$LEARNINGS_FILE" | head -n 25 || true
    
    echo ""
    echo "───────────────────────────────────────────────────────────"
    echo ""
fi

# Git status
if git rev-parse --git-dir > /dev/null 2>&1; then
    BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    UNCOMMITTED=$(git diff --name-only HEAD 2>/dev/null | wc -l | xargs)
    
    echo -e "${BLUE}🔀 Git Status${NC}"
    echo "   Branch: $BRANCH"
    echo "   Uncommitted changes: $UNCOMMITTED files"
    echo ""
fi

echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    QUICK REFERENCE                         ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Commands:"
echo "  ./v2/tools/phasectl.py start <phase>       - Start phase"
echo "  ./v2/tools/phasectl.py review <phase>      - Submit for review"
echo "  ./v2/tools/phasectl.py justify-scope <p>   - Justify drift"
echo "  ./v2/tools/phasectl.py acknowledge-orient  - Acknowledge reading"
echo "  ./v2/tools/phasectl.py reflect <phase>     - Capture learnings"
echo "  ./v2/tools/phasectl.py next                - Advance phase"
echo ""

echo "Full context recovered ✅"
echo ""

