#!/usr/bin/env python3
"""
Simple state management for v2.

Philosophy: Minimal state, clear contracts, no complex state machines.

State files:
- .repo/state/current.json     - Current phase pointer
- .repo/state/acknowledged.json - Orient acknowledgments  
- .repo/learnings.md            - Human-readable learnings
- .repo/scope_audit/            - Scope justifications
"""

import json
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class StateError(Exception):
    """State operation error."""
    pass


def get_current_phase(repo_root: Path = None) -> Optional[Dict[str, Any]]:
    """
    Get current phase state.
    
    Returns:
        Current phase dict with:
        - phase_id: str
        - started_at: timestamp
        - baseline_sha: git commit SHA
        - plan_sha: hash of plan.yaml at start
    
    Returns None if no phase active.
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    current_file = repo_root / ".repo" / "state" / "current.json"
    
    if not current_file.exists():
        return None
    
    try:
        return json.loads(current_file.read_text())
    except (json.JSONDecodeError, OSError):
        return None


def set_current_phase(phase_id: str, repo_root: Path = None) -> Dict[str, Any]:
    """
    Set current phase and capture baseline state.
    
    Args:
        phase_id: Phase to activate
        repo_root: Repository root
        
    Returns:
        Current phase state dict
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    # Capture baseline SHA (current HEAD)
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True
        )
        baseline_sha = result.stdout.strip()
    except subprocess.CalledProcessError:
        # Not in git repo or git not available
        baseline_sha = "unknown"
    
    # Compute plan SHA for tamper detection
    plan_path = repo_root / ".repo" / "plan.yaml"
    if plan_path.exists():
        plan_sha = hashlib.sha256(plan_path.read_bytes()).hexdigest()
    else:
        plan_sha = "unknown"
    
    # Create current state
    current = {
        "phase_id": phase_id,
        "started_at": datetime.now().isoformat(),
        "baseline_sha": baseline_sha,
        "plan_sha": plan_sha
    }
    
    # Write atomically
    current_file = repo_root / ".repo" / "state" / "current.json"
    current_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Atomic write using temp file + rename
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=current_file.parent,
        delete=False,
        prefix='.current.',
        suffix='.tmp'
    ) as f:
        json.dump(current, f, indent=2)
        temp_path = f.name
    
    os.replace(temp_path, current_file)
    
    return current


def clear_current_phase(repo_root: Path = None):
    """Clear current phase (after completion)."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    current_file = repo_root / ".repo" / "state" / "current.json"
    
    if current_file.exists():
        current_file.unlink()


def is_orient_acknowledged(phase_id: str, repo_root: Path = None) -> bool:
    """Check if agent has acknowledged orient.sh for this phase."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    ack_file = repo_root / ".repo" / "state" / "acknowledged.json"
    
    if not ack_file.exists():
        return False
    
    try:
        acks = json.loads(ack_file.read_text())
        return phase_id in acks.get("phases", [])
    except (json.JSONDecodeError, OSError):
        return False


def acknowledge_orient(phase_id: str, summary: str, repo_root: Path = None):
    """Record orient acknowledgment."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    ack_file = repo_root / ".repo" / "state" / "acknowledged.json"
    ack_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing acknowledgments
    if ack_file.exists():
        try:
            acks = json.loads(ack_file.read_text())
        except (json.JSONDecodeError, OSError):
            acks = {"phases": [], "summaries": {}}
    else:
        acks = {"phases": [], "summaries": {}}
    
    # Add this phase
    if phase_id not in acks["phases"]:
        acks["phases"].append(phase_id)
    
    acks["summaries"][phase_id] = {
        "timestamp": datetime.now().isoformat(),
        "summary": summary
    }
    
    # Write atomically
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(
        mode='w',
        dir=ack_file.parent,
        delete=False,
        prefix='.ack.',
        suffix='.tmp'
    ) as f:
        json.dump(acks, f, indent=2)
        temp_path = f.name
    
    os.replace(temp_path, ack_file)


def save_scope_justification(phase_id: str, files: List[str], justification: str, repo_root: Path = None):
    """Save scope drift justification for human review."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    audit_dir = repo_root / ".repo" / "scope_audit"
    audit_dir.mkdir(parents=True, exist_ok=True)
    
    audit_file = audit_dir / f"{phase_id}.md"
    
    content = f"""# Scope Drift Justification: {phase_id}

**Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Out-of-Scope Files ({len(files)})

{chr(10).join(f"- `{f}`" for f in files)}

## Justification

{justification}

---
*This file is for human review. The agent has justified why these out-of-scope changes were necessary.*
"""
    
    audit_file.write_text(content)


def has_scope_justification(phase_id: str, repo_root: Path = None) -> bool:
    """Check if scope justification exists for this phase."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    audit_file = repo_root / ".repo" / "scope_audit" / f"{phase_id}.md"
    return audit_file.exists()


def append_learning(phase_id: str, learning: str, repo_root: Path = None):
    """Append learning to learnings.md."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    learnings_file = repo_root / ".repo" / "learnings.md"
    
    # Create file with header if it doesn't exist
    if not learnings_file.exists():
        learnings_file.parent.mkdir(parents=True, exist_ok=True)
        learnings_file.write_text("# Project Learnings\n\n")
    
    # Append learning
    entry = f"""## {datetime.now().strftime("%Y-%m-%d")}: {phase_id}

{learning}

---

"""
    
    with learnings_file.open('a') as f:
        f.write(entry)


def get_recent_learnings(limit: int = 3, repo_root: Path = None) -> str:
    """Get recent learnings for display in orient.sh."""
    if repo_root is None:
        repo_root = Path.cwd()
    
    learnings_file = repo_root / ".repo" / "learnings.md"
    
    if not learnings_file.exists():
        return "No learnings recorded yet."
    
    content = learnings_file.read_text()
    
    # Extract last N learning entries
    entries = content.split("---")
    recent = entries[-limit-1:-1] if len(entries) > limit else entries[1:]
    
    if not recent:
        return "No learnings recorded yet."
    
    return "\n---\n".join(recent)
