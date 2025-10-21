# Agent Update Prompt

Use this prompt to update your protocol tools from GitHub:

```
Update the Judge-Gated Protocol tools to the latest version from GitHub.

Run these commands:

1. Update protocol repository:
   cd ../judge-gated-orchestrator
   git pull origin main

2. Reinstall tools in current project:
   cd ../your-project-name
   ../judge-gated-orchestrator/install-protocol.sh

3. Verify update:
   ./tools/phasectl.py health

The install script preserves your project's plan.yaml and only updates the protocol tools.
```

**What this does:**
- ✅ Pulls latest protocol updates from GitHub
- ✅ Reinstalls tools with atomic updates and verification
- ✅ Preserves your project configuration
- ✅ Verifies everything is working

**Alternative (if you don't have the protocol repo locally):**
```
Clone and install the latest Judge-Gated Protocol tools:

1. Clone protocol repository:
   git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git

2. Install tools in current project:
   ../judge-gated-orchestrator/install-protocol.sh

3. Verify installation:
   ./tools/phasectl.py health
```
