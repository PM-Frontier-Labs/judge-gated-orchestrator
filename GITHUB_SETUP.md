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

### Step 4: Discover and Generate Briefs

```bash
# Discover plan structure and validate
./tools/phasectl.py discover

# Generate brief templates from plan phases
./tools/phasectl.py generate-briefs
```

### Step 5: Initialize First Phase

```bash
# Set current phase (replace P01-scaffold with your first phase ID)
echo '{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": '$(date +%s.%N)'
}' > .repo/briefs/CURRENT.json
```

### Step 6: Verify Setup

```bash
# Check protocol health
./tools/phasectl.py health

# See current status
./tools/phasectl.py discover
```

**You're ready to start autonomous execution!**

---

## 🔄 Transitioning Between Plans

When you complete one project and want to start a new one:

### Step 1: Clean Up Old Plan State

```bash
# Remove old phase briefs and state
rm -rf .repo/briefs/P*.md
rm -f .repo/briefs/CURRENT.json
rm -rf .repo/critiques/
rm -rf .repo/traces/
rm -rf .repo/state/
rm -rf .repo/amendments/
rm -rf .repo/collective_intelligence/

# Create fresh directory structure
mkdir -p .repo/briefs .repo/critiques .repo/traces .repo/state .repo/amendments/pending .repo/amendments/applied .repo/collective_intelligence
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

# Generate briefs for new phases
./tools/phasectl.py generate-briefs

# Initialize first phase
echo '{
  "phase_id": "P01-scaffold",
  "brief_path": ".repo/briefs/P01-scaffold.md",
  "status": "active",
  "started_at": '$(date +%s.%N)'
}' > .repo/briefs/CURRENT.json
```

### Step 6: Verify Clean State

```bash
# Check everything is working
./tools/phasectl.py health
./tools/phasectl.py discover
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

# 4. Discover and generate
./tools/phasectl.py discover
./tools/phasectl.py generate-briefs

# 5. Initialize first phase
echo '{"phase_id": "P01-scaffold", "brief_path": ".repo/briefs/P01-scaffold.md", "status": "active", "started_at": '$(date +%s.%N)'}' > .repo/briefs/CURRENT.json
```

### Plan Transition Commands

```bash
# 1. Clean old state
rm -rf .repo/briefs/P*.md .repo/briefs/CURRENT.json .repo/critiques/ .repo/traces/ .repo/state/ .repo/amendments/ .repo/collective_intelligence/

# 2. Update tools (optional)
cd ../judge-gated-orchestrator && git pull origin main && cd ../your-project
../judge-gated-orchestrator/install-protocol.sh

# 3. Create new plan (with AI assistant)
# Edit .repo/plan.yaml

# 4. Initialize new project
./tools/generate_manifest.py
./tools/phasectl.py discover
./tools/phasectl.py generate-briefs
echo '{"phase_id": "P01-scaffold", "brief_path": ".repo/briefs/P01-scaffold.md", "status": "active", "started_at": '$(date +%s.%N)'}' > .repo/briefs/CURRENT.json
```

### Health Check Commands

```bash
# Check protocol health
./tools/phasectl.py health

# Get solutions for issues
./tools/phasectl.py solutions

# Discover plan structure
./tools/phasectl.py discover
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
