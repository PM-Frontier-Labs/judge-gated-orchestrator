# GitHub-Based Protocol Setup Guide

**Audience:** Teams and individuals setting up the Judge-Gated Protocol from GitHub

**Goal:** Clear instructions for (1) first-time setup and (2) transitioning between plans

---

## 🚀 First-Time Setup from GitHub

### Step 1: Clone Protocol Repository

```bash
# Clone the protocol repository
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git

# Navigate to your project directory
cd your-project-directory
```

### Step 2: Install Protocol Tools

```bash
# Install protocol tools in your project
../judge-gated-orchestrator/install-protocol.sh
```

**What this does:**
- ✅ Copies `tools/` directory to your project
- ✅ Creates `.repo/` directory structure
- ✅ Preserves your existing `plan.yaml` (if any)
- ✅ Makes tools executable

### Step 3: Create Your Project Plan

```bash
# Create your project plan file
touch .repo/plan.yaml
```

### Step 4: Add Phase Briefs

Add briefs to each phase in plan.yaml using the `brief: |` syntax:

```yaml
phases:
  - id: P01-scaffold
    description: "Setup project structure"
    brief: |
      # Objective
      Create basic project scaffolding
      
      ## Required Artifacts
      - src/__init__.py
      - tests/test_main.py
      
      ## Implementation Steps
      1. Create src/ directory
      2. Add basic test framework
    
    scope:
      include: ["src/**", "tests/**"]
    gates:
      tests: {must_pass: true}
```

### Step 5: Start First Phase

```bash
# Start the first phase (this creates .repo/state/current.json automatically)
./tools/phasectl.py start P01-scaffold
```

**You're ready to start autonomous execution!**

---

## 🔄 Transitioning Between Plans

When you complete one project and want to start a new one:

### Step 1: Clean Up Old Plan State

```bash
# Remove old plan state
rm -rf .repo/critiques/
rm -rf .repo/traces/
rm -rf .repo/state/
rm -f .repo/learnings.md
rm -rf .repo/scope_audit/
rm -f .repo/plan.yaml  # Remove old plan to ensure fresh start

# Create fresh directory structure
mkdir -p .repo/state .repo/critiques .repo/traces
```

### Step 2: Update Protocol Tools (Optional)

```bash
# Pull latest protocol updates
cd ../judge-gated-orchestrator
git pull origin main
cd ../your-project

# Reinstall tools (preserves your plan.yaml)
../judge-gated-orchestrator/install-protocol.sh
```

### Step 3: Create New Plan

Work with your AI assistant to create a new `plan.yaml`:

```
Help me create a new .repo/plan.yaml for my next project.

My new project is: [describe your new project]
I want to: [describe your new goal]

Let's break this into phases with clear scope and quality gates.
```

### Step 4: Generate New Protocol Manifest

```bash
# Update protocol integrity hashes
./tools/generate_manifest.py
```

### Step 5: Initialize New Project

```bash
# Discover and validate new plan
./tools/phasectl.py discover

# Start the first phase
./tools/phasectl.py start P01-scaffold
# This creates .repo/state/current.json and displays the brief
```

### Step 6: Verify Everything Works

```bash
# Check status
./orient.sh
```

**Key insight:** Each plan is independent. Old state doesn't carry over to new plans.

---

## 🔧 Protocol Tool Updates

### Automatic Updates

The protocol tools now include automatic update detection:

```bash
# Tools automatically check for updates on every command
./tools/phasectl.py discover
# If outdated: "🔄 Protocol tools outdated - attempting atomic update..."

# Manual update if needed
../judge-gated-orchestrator/install-protocol.sh
```

### Update Safety

- ✅ **Atomic updates** with backup/rollback
- ✅ **Verification** after update
- ✅ **Preserves project configuration** (never overwrites `plan.yaml`)
- ✅ **Automatic corruption detection** and recovery

---

## 📋 Quick Reference

### First-Time Setup Commands

```bash
# 1. Clone protocol
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git

# 2. Install in your project
cd your-project
../judge-gated-orchestrator/install-protocol.sh

# 3. Create plan
touch .repo/plan.yaml

# 4. Start first phase
./tools/phasectl.py start P01-scaffold
```

### Plan Transition Commands

```bash
# 1. Clean old state
rm -rf .repo/critiques/ .repo/traces/ .repo/state/ .repo/learnings.md .repo/scope_audit/

# 2. Update tools (optional)
cd ../judge-gated-orchestrator && git pull origin main && cd ../your-project
../judge-gated-orchestrator/install-protocol.sh

# 3. Create new plan (with AI assistant)
# Edit .repo/plan.yaml

# 4. Initialize new project
./tools/phasectl.py start P01-scaffold
```

### Health Check Commands

```bash
# See current status
./orient.sh

# Start a phase
./tools/phasectl.py start <phase-id>

# Review a phase
./tools/phasectl.py review <phase-id>
```

---

## 🆚 GitHub vs Local Setup

| Method | Pros | Cons | Use Case |
|--------|------|------|----------|
| **GitHub** | ✅ Always latest version<br>✅ Easy team sharing<br>✅ Automatic updates | ❌ Requires internet<br>❌ Git dependency | **Recommended** for most users |
| **Local** | ✅ Works offline<br>✅ No git dependency | ❌ Manual updates<br>❌ Version drift risk | Legacy/offline environments |

---

## 🚨 Common Issues

### Issue: "Cannot find protocol tools"

**Cause:** Running `install-protocol.sh` from wrong directory

**Fix:**
```bash
# Ensure you're in your project directory
cd your-project

# Ensure protocol repo is accessible
ls ../judge-gated-orchestrator/tools/
# Should show phasectl.py, judge.py, etc.

# Run install
../judge-gated-orchestrator/install-protocol.sh
```

### Issue: "Protocol tools outdated"

**Cause:** Local tools are older than GitHub version

**Fix:**
```bash
# Update protocol repo
cd ../judge-gated-orchestrator
git pull origin main

# Reinstall tools
cd ../your-project
../judge-gated-orchestrator/install-protocol.sh
```

### Issue: "Plan validation failed"

**Cause:** `plan.yaml` has schema errors

**Fix:**
```bash
# Check for common errors
./tools/phasectl.py discover

# Fix plan.yaml based on error messages
nano .repo/plan.yaml

# Try again
./tools/phasectl.py discover
```

---

## 📚 Additional Resources

- **README.md** - Overview and philosophy
- **GETTING_STARTED.md** - Detailed setup guide
- **PROTOCOL.md** - Execution manual for AI assistants
- **GitHub Issues** - https://github.com/PM-Frontier-Labs/judge-gated-orchestrator/issues

---

## 🎯 Next Steps

1. **Set up your first project** using the commands above
2. **Create your plan** with your AI assistant
3. **Start autonomous execution** with `PROTOCOL.md`
4. **Monitor progress** with `./tools/phasectl.py health`

**Welcome to autonomous multi-phase development with quality guarantees!** 🚀
