#!/bin/bash
# install-protocol.sh - IC9 minimal protocol installation
# 
# This script installs only protocol tools, preserving project-specific configuration.
# It prevents the critical bug where protocol updates overwrite project plans.

set -e

echo "🔧 Installing Judge-Gated Protocol Tools..."

# Check if we're in a git repository
if [ ! -d ".git" ]; then
    echo "❌ Error: Not in a git repository"
    echo "   Run this script from your project root directory"
    exit 1
fi

# Determine source directory (could be current dir or parent)
if [ -d "tools" ] && [ -f "tools/phasectl.py" ]; then
    # Running from protocol repository itself
    SOURCE_DIR="."
elif [ -d "../judge-gated-orchestrator/tools" ]; then
    # Running from project with protocol in parent
    SOURCE_DIR="../judge-gated-orchestrator"
else
    echo "❌ Error: Cannot find protocol tools"
    echo "   Expected to find tools/ directory with phasectl.py"
    echo "   Either run from protocol repository or ensure judge-gated-orchestrator is in parent directory"
    exit 1
fi

# Create tools directory if it doesn't exist
mkdir -p tools

# Copy only protocol tools, never project config
echo "📦 Copying protocol tools from $SOURCE_DIR..."
cp -r $SOURCE_DIR/tools/* ./tools/

# CRITICAL: Never copy .repo directory from protocol repository
# This prevents overwriting project-specific plans and state
if [ -d "$SOURCE_DIR/.repo" ]; then
    echo "⚠️  Skipping protocol repository's .repo directory to preserve your project configuration"
fi

# Ensure tools are executable
chmod +x tools/phasectl.py
chmod +x tools/judge.py
chmod +x tools/llm_judge.py
chmod +x tools/generate_manifest.py

# Create .repo directory structure if it doesn't exist
mkdir -p .repo/briefs
mkdir -p .repo/critiques
mkdir -p .repo/traces
mkdir -p .repo/state

# Check if plan.yaml exists and warn about preservation
if [ -f ".repo/plan.yaml" ]; then
    echo "✅ Project plan preserved: .repo/plan.yaml"
    echo "⚠️  Protocol tools installed without overwriting your project configuration"
    
    # Check if this looks like the protocol's plan (safety check)
    if grep -q "PROMPT-LAB-IMPLEMENTATION" .repo/plan.yaml 2>/dev/null; then
        echo ""
        echo "🚨 WARNING: Detected protocol repository's plan.yaml!"
        echo "   This suggests your project plan was overwritten."
        echo "   Your original plan may be lost."
        echo ""
        echo "💡 Recovery options:"
        echo "   1. Check git history: git log --oneline .repo/plan.yaml"
        echo "   2. Restore from backup: git checkout HEAD~1 -- .repo/plan.yaml"
        echo "   3. Recreate your plan from scratch"
        echo ""
    fi
else
    echo "ℹ️  No existing plan.yaml found"
    echo "   Create your project plan: touch .repo/plan.yaml"
fi

echo ""
echo "✅ Protocol installation complete!"
echo ""
echo "Next steps:"
echo "1. Create your project plan: touch .repo/plan.yaml"
echo "2. Discover plan structure: ./tools/phasectl.py discover"
echo "3. Generate briefs: ./tools/phasectl.py generate-briefs"
echo ""
echo "🔒 Your project configuration is protected from protocol overwrites"
