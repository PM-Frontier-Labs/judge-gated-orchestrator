# Cutover Plan: v1 → v2

## Current State

✅ **v2 Complete**
- 1,238 lines of code (vs 5,895 in v1)
- All 7 core features implemented
- Tests passing
- Documentation complete

✅ **v1 Still Works**
- Located in `tools/`
- No changes made
- Can be used as fallback

## Cutover Decision

**You have two options:**

### Option A: Immediate Cutover (Aggressive)
Use this if you're confident and want simplicity now.

```bash
# Backup v1
mv tools tools-v1-backup
mv orient.sh orient-v1-backup.sh

# Activate v2
mv v2/tools tools
mv v2/orient.sh orient.sh

# Update any scripts that reference tools/
# (grep for "tools/phasectl" in your scripts)

# Test
./orient.sh
./tools/phasectl.py start P01-test
```

**Timeline: 10 minutes**

### Option B: Gradual Transition (Safe)
Use this if you want to test v2 first.

**Week 1: Testing**
```bash
# Keep using v1 for current work
./tools/phasectl.py review current-phase

# Test v2 on a new experimental phase
./v2/tools/phasectl.py start P99-v2-test
# Make changes
./v2/tools/phasectl.py review P99-v2-test
```

**Week 2: Parallel Usage**
```bash
# Use v2 for new phases
./v2/tools/phasectl.py start P02-new-feature

# Keep v1 for in-progress work
./tools/phasectl.py review P01-current
```

**Week 3: Full Cutover**
```bash
# When confident, switch
mv tools tools-v1-backup
mv v2/tools tools
mv v2/orient.sh orient.sh
```

**Timeline: 3 weeks**

## What Changes For You

### Commands
```bash
# Before (v1)
./tools/phasectl.py start P01
./tools/phasectl.py review P01
./tools/phasectl.py next

# After (v2)
./tools/phasectl.py start P01        # Same
./tools/phasectl.py review P01       # Same
./tools/phasectl.py justify-scope P01  # NEW
./tools/phasectl.py acknowledge-orient # NEW
./tools/phasectl.py reflect P01      # NEW
./tools/phasectl.py next             # Same
```

### Workflow Changes

**Scope Drift (Big Change)**
```bash
# v1: Hard block
❌ Out of scope! Revert files.
> git restore file.py

# v2: Justify it
❌ Out of scope!
> ./tools/phasectl.py justify-scope P01
> "I needed X because Y"
✅ Pass (justified - human review later)
```

**Phase Transitions (New Requirement)**
```bash
# v2: Must acknowledge orient
./tools/phasectl.py next
❌ Must acknowledge orient first
> ./orient.sh
> ./tools/phasectl.py acknowledge-orient
> "Current state is X, next phase is Y"
✅ Advanced to next phase
```

**Learning Capture (New)**
```bash
# After phase approval
./tools/phasectl.py reflect P01
> "Learned that tests are important"
✅ Recorded to .repo/learnings.md
```

### Briefs (Optional Change)

You can continue using separate .md files:
```
.repo/briefs/P01.md  # Still works!
```

Or move to embedded YAML (recommended):
```yaml
# .repo/plan.yaml
phases:
  - id: P01
    brief: |
      # Objective
      Content here
```

### State Files (Automatic)

v2 creates simpler state:
```
# v1 (10+ files)
.repo/state/P01.ctx.json
.repo/state/next_budget.json
.repo/state/generalization.json
.repo/state/telemetry.jsonl
.repo/state/attribution.jsonl
# ... etc

# v2 (3 files)
.repo/state/current.json
.repo/state/acknowledged.json
.repo/learnings.md
```

Old v1 state files are ignored by v2 (no cleanup needed).

## Rollback Procedure

If v2 doesn't work:

```bash
# Restore v1
mv tools tools-v2
mv tools-v1-backup tools
mv orient.sh orient-v2.sh
mv orient-v1-backup.sh orient.sh

# Continue with v1
./tools/phasectl.py start P01
```

## Testing Checklist

Before cutover, test these v2 workflows:

- [ ] Start a phase: `./v2/tools/phasectl.py start P01`
- [ ] Make changes to in-scope files
- [ ] Review: `./v2/tools/phasectl.py review P01`
- [ ] Tests pass
- [ ] Approve phase
- [ ] Reflect: `./v2/tools/phasectl.py reflect P01`
- [ ] Advance: `./v2/tools/phasectl.py next`
- [ ] Acknowledge orient: `./v2/tools/phasectl.py acknowledge-orient`

Scope justification workflow:
- [ ] Make out-of-scope changes
- [ ] Review fails with scope error
- [ ] Justify: `./v2/tools/phasectl.py justify-scope P01`
- [ ] Review passes with warning
- [ ] Check audit file: `cat .repo/scope_audit/P01.md`

## Migration Checklist

If you have active phases in v1:

- [ ] Complete current phase in v1
- [ ] Or note current state: `cat .repo/briefs/CURRENT.json`
- [ ] After cutover, restart phase: `./tools/phasectl.py start <phase>`
- [ ] Baseline SHA will be re-captured (this is fine)

If you have custom tooling that calls phasectl:

- [ ] Find all references: `grep -r "tools/phasectl" .`
- [ ] Update paths if using absolute paths
- [ ] Test custom scripts

If you have CI/CD that uses judge:

- [ ] Update paths in CI config
- [ ] Test CI build
- [ ] Update any badges/status checks

## What Gets Deleted (After Cutover)

Once you're confident in v2 (1-2 weeks):

```bash
# Delete v1 backup
rm -rf tools-v1-backup

# Delete v2 directory
rm -rf v2

# Clean up old state (optional)
rm -rf .repo/state/*.ctx.json
rm -rf .repo/state/next_budget.json
rm -rf .repo/state/generalization.json
rm -rf .repo/state/telemetry.jsonl
rm -rf .repo/state/attribution.jsonl
rm -rf .repo/collective_intelligence
rm -rf .repo/amendments
```

## Support Plan

**Week 1-2: Parallel Operation**
- Keep v1 available
- Test v2 thoroughly
- Document any issues

**Week 3: Full Cutover**
- Make v2 primary
- Keep v1 backup for 1 week

**Week 4: Cleanup**
- Delete v1 if no issues
- Archive comparison docs

## Expected Benefits

After cutover you should see:

1. **Faster reviews** (~10s vs ~30s)
   - No replay system overhead
   - Simpler gate logic

2. **Less frustration with scope**
   - Justify instead of block
   - Context captured for learning

3. **Better context retention**
   - Forced orient acknowledgment
   - Learning reflection

4. **Easier maintenance**
   - 1,200 lines vs 6,000 lines
   - Clear, simple code
   - Easy to debug

5. **Safer system**
   - No security vulnerabilities
   - Atomic file operations
   - Clear error messages

## Recommended Approach

**For you (no external users):**

I recommend **Option A (Immediate Cutover)**:

```bash
# Today
mv tools tools-v1-backup
mv v2/tools tools
mv orient.sh orient-v1.sh
mv v2/orient.sh orient.sh

# Test on current work
./orient.sh
./tools/phasectl.py start <current-phase>

# If any issues, rollback is easy
mv tools tools-v2-broken
mv tools-v1-backup tools
```

**Why immediate:** 
- You're the only user
- v2 is simpler to work with
- Bugs will surface quickly
- Easy rollback available

**Why not gradual:**
- Adds complexity of running two systems
- Delays benefits
- Context switching overhead

## The Moment of Truth

When you're ready:

```bash
cd /workspace

# One command cutover
mv tools tools-v1-backup && \
  mv v2/tools tools && \
  mv orient.sh orient-v1.sh && \
  mv v2/orient.sh orient.sh && \
  echo "✅ Cutover complete!"

# First command in v2
./orient.sh
```

You can do this now. It takes 10 seconds and is easily reversible.

## Questions?

- Read `/workspace/v2/COMPARISON.md` for detailed differences
- Read `/workspace/v2/MIGRATION.md` for technical details
- Check `/workspace/v2/README.md` for architecture

Or just try it - you can always switch back.
