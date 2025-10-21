# Agent Workflow Prompt

Use this prompt when handing off to an AI agent to implement a plan:

```
You are working with the Judge-Gated Protocol. Follow these steps exactly:

1. First, run: ./orient.sh
   This shows you the current project status and available phases.

2. CRITICAL: Before making ANY changes, run:
   ./tools/phasectl.py start <phase-id>
   
   This creates the baseline SHA and properly initializes the phase state.
   NEVER manually create CURRENT.json - always use this command.

3. Read the phase brief:
   cat .repo/briefs/<phase-id>.md

4. Implement the changes within the specified scope.

5. Submit for review:
   ./tools/phasectl.py review <phase-id>

6. If approved, advance to next phase:
   ./tools/phasectl.py next

7. Repeat for remaining phases.

IMPORTANT: Always use the protocol commands. Never manually create state files.
```

## Key Points for Agents

- **Always start with `./tools/phasectl.py start <phase-id>`** - this is mandatory
- **Never manually create CURRENT.json** - the protocol manages all state
- **Follow the scope exactly** - out-of-scope changes will be rejected
- **Use `./tools/phasectl.py review <phase-id>`** to submit changes
- **Use `./tools/phasectl.py next`** to advance after approval

## What the Protocol Does

- Creates baseline SHA for change tracking
- Manages phase state automatically
- Runs quality gates (tests, lint, docs, drift detection)
- Provides clear feedback on what needs to be fixed
- Learns from successful patterns for future phases

## Recovery

If you get confused or lose context:
```bash
./orient.sh  # Shows current status
./tools/phasectl.py health  # Shows protocol health
```

The protocol is designed to be context-window proof - all state is in files.
