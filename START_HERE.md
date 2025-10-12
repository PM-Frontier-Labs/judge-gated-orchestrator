# 🚀 New Claude Instance? Start Here!

**Purpose:** Quick orientation when resuming work in a new context window

---

## ⚡ 60-Second Quick Start

### 1. Orient (10 seconds)
```bash
./orient.sh
```

Shows: current phase, progress, status, next steps

### 2. Request Permissions (If Needed)

**Say to user:**

> "I'm resuming work on this project. To continue autonomously, I need approval for:
>
> - **Read** all files (`./**`)
> - **Write** to `src/`, `tests/`, `docs/`, `.repo/`
> - **Execute** judge tools (`./tools/phasectl.py`)
> - **Git operations** (status, diff, add)
>
> All operations scoped to this project. See `.claude-code.json` for details. Proceed?"

### 3. Resume Work (40 seconds)

**Check current status:**
```bash
PHASE_ID=$(cat .repo/briefs/CURRENT.json | grep -o '"phase_id":"[^"]*"' | cut -d'"' -f4)
cat .repo/briefs/${PHASE_ID}.md
```

**If critique exists:**
```bash
cat .repo/critiques/${PHASE_ID}.md  # Read feedback
# Fix issues, then re-run review
```

**If no critique:**
```bash
# Continue implementation or submit for review
./tools/phasectl.py review ${PHASE_ID}
```

**If phase approved:**
```bash
./tools/phasectl.py next  # Advance to next phase
```

---

## 📋 Context Recovery Checklist

- [ ] Run `./orient.sh` to see status
- [ ] Request permissions (use template above)
- [ ] Check `CURRENT.json` for active phase
- [ ] Read current brief (`.repo/briefs/<PHASE>.md`)
- [ ] Check for critique (`.repo/critiques/<PHASE>.md`)
- [ ] Resume implementation

---

## 🎯 Common Scenarios

### Scenario A: Mid-Implementation
**Indicators:** Files partially created, no critique yet

**Action:**
1. Read brief: `cat .repo/briefs/<PHASE>.md`
2. Check work: `git status`
3. Continue implementing
4. When done: `./tools/phasectl.py review <PHASE>`

### Scenario B: Needs Fixes
**Indicators:** Critique file (`.md`) exists

**Action:**
1. Read critique: `cat .repo/critiques/<PHASE>.md`
2. Fix each issue
3. Re-submit: `./tools/phasectl.py review <PHASE>`

### Scenario C: Phase Complete
**Indicators:** Approval file (`.OK`) exists

**Action:**
1. Verify: `cat .repo/critiques/<PHASE>.OK`
2. Advance: `./tools/phasectl.py next`
3. Read new brief and start

---

## 🔧 Quick Commands

```bash
# Get status
./orient.sh

# Read current brief
cat .repo/briefs/$(cat .repo/briefs/CURRENT.json | grep brief_path | cut -d'"' -f4)

# Submit review
PHASE=$(cat .repo/briefs/CURRENT.json | grep phase_id | cut -d'"' -f4)
./tools/phasectl.py review $PHASE

# Check last review
cat .repo/critiques/${PHASE}.md 2>/dev/null || cat .repo/critiques/${PHASE}.OK 2>/dev/null

# Advance to next
./tools/phasectl.py next
```

---

## 🌙 For Overnight Autonomous Work

**Before bed, tell Claude:**

> "Work through as many phases as possible overnight. For each phase:
> 1. Read brief
> 2. Implement files
> 3. Write tests
> 4. Submit review (`./tools/phasectl.py review <PHASE>`)
> 5. Fix critiques (max 3 attempts)
> 6. Advance when approved (`./tools/phasectl.py next`)
>
> Target: 2-3 phases complete by morning."

**Wake up:**
```bash
./orient.sh  # See progress
git log --oneline --since="8 hours ago"  # What happened
```

---

## 📚 Reference

- **This file:** Quick start for new instances
- **README.md:** Complete system documentation
- **QUICK_TEST.md:** Testing guide
- **.claude-code.json:** Auto-approved tool patterns
- **orient.sh:** Status dashboard script

---

## ✅ You're Ready!

**Your workflow:**
1. `./orient.sh` → Get status
2. Read brief → Understand task
3. Implement → Build it
4. Review → `./tools/phasectl.py review <PHASE>`
5. Fix/Advance → Iterate until all phases done

**The system is context-window proof** - everything you need is in files! 🎉
