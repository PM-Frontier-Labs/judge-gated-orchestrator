#!/usr/bin/env python3
"""
State Management: Runtime state separate from governance.
Implements the core Governance ≠ Runtime split.
"""

import json
from .file_lock import safe_write_json, safe_read_json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

def load_phase_context(phase_id: str, repo_root: str = ".") -> Dict[str, Any]:
    """Load phase context from Pxx.ctx.json"""
    ctx_file = Path(repo_root) / ".repo" / "state" / f"{phase_id}.ctx.json"
    if ctx_file.exists():
        with open(ctx_file, 'r') as f:
            return json.load(f)
    return _create_default_context(phase_id)

def save_phase_context(phase_id: str, context: Dict[str, Any], repo_root: str = ".") -> None:
    """Save phase context to Pxx.ctx.json"""
    ctx_file = Path(repo_root) / ".repo" / "state" / f"{phase_id}.ctx.json"
    ctx_file.parent.mkdir(parents=True, exist_ok=True)
    context["updated_at"] = datetime.now().isoformat()
    # Write context atomically
    safe_write_json(ctx_file, context, indent=2)

def get_baseline_sha(phase_id: str, repo_root: str = ".") -> str:
    """Get pinned baseline SHA for phase"""
    context = load_phase_context(phase_id, repo_root)
    return context.get("baseline_sha", "initial")

def get_test_cmd(phase_id: str, repo_root: str = ".") -> str:
    """Get current test command for phase"""
    context = load_phase_context(phase_id, repo_root)
    return context.get("test_cmd", "pytest tests/ -v")

def get_mode(phase_id: str, repo_root: str = ".") -> str:
    """Get current mode (EXPLORE/LOCK) for phase"""
    context = load_phase_context(phase_id, repo_root)
    return context.get("mode", "EXPLORE")

def set_mode(phase_id: str, mode: str, repo_root: str = ".") -> bool:
    """Set mode for phase with validation"""
    valid_modes = ["EXPLORE", "LOCK"]
    if mode not in valid_modes:
        print(f"❌ Invalid mode: {mode}. Must be one of {valid_modes}")
        return False
    
    context = load_phase_context(phase_id, repo_root)
    context["mode"] = mode
    context["mode_changed_at"] = datetime.now().isoformat()
    save_phase_context(phase_id, context, repo_root)
    return True

def _create_default_context(phase_id: str) -> Dict[str, Any]:
    """Create default context for new phase"""
    return {
        "phase_id": phase_id,
        "baseline_sha": "initial",
        "test_cmd": "pytest tests/ -v",
        "mode": "EXPLORE",
        "scope_cache": {},
        "amendments_used": {},
        "amendments_budget": {
            "add_scope": 2,
            "set_test_cmd": 1,
            "note_baseline_shift": 1
        },
        "created_at": datetime.now().isoformat()
    }
