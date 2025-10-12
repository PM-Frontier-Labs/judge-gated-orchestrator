# New Instance Quick Start

**Goal:** Get oriented and resume work in <60 seconds.

## Step 1: Orient (10 seconds)

```bash
./orient.sh
```

Shows:
- Current phase
- Progress (X/Y complete)
- Status (approved/needs-fixes/in-progress)
- Next steps

## Step 2: Follow the Protocol (30 seconds)

The protocol is simple:

```
Read brief → Implement → Submit for review → Handle feedback → Next phase
```

**Check current phase:**
```bash
cat .repo/briefs/CURRENT.json
```

**Read the brief:**
```bash
cat .repo/briefs/<phase-id>.md
```

**Submit for review:**
```bash
./tools/phasectl.py review <phase-id>
```

**If approved:**
```bash
./tools/phasectl.py next
```

**If needs fixes:**
```bash
cat .repo/critiques/<phase-id>.md  # Read feedback
# Fix issues
./tools/phasectl.py review <phase-id>  # Re-submit
```

## Step 3: Resume Work (20 seconds)

Run `./orient.sh` and follow the "NEXT STEPS" section.

## Permission Setup (First Time Only)

If you see permission prompts, the project has `.claude-code.json` with auto-approval patterns. They should work automatically. If not, approve when asked—all operations are scoped to this project.

## That's It

- **All state is in files** - No memory needed
- **Protocol is simple** - Brief → Implement → Review → Next
- **orient.sh recovers context** - Run anytime

See **README.md** for protocol details.
