#!/usr/bin/env python3
"""
Amendment System: Bounded, auditable mutability.
Implements the core amendment system with budgets.
"""

import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

def propose_amendment(phase_id: str, amendment_type: str, value: Any, reason: str, repo_root: str = ".") -> bool:
    """Propose an amendment. Returns True if within budget."""
    if not _check_budget(phase_id, amendment_type, repo_root):
        return False
    
    amendment = {
        "type": amendment_type,
        "value": value,
        "reason": reason,
        "phase_id": phase_id,
        "timestamp": datetime.now().isoformat()
    }
    
    pending_dir = Path(repo_root) / ".repo" / "amendments" / "pending"
    pending_dir.mkdir(parents=True, exist_ok=True)
    
    amendment_file = pending_dir / f"{amendment_type}_{len(list(pending_dir.glob('*')))}.yaml"
    with open(amendment_file, 'w') as f:
        yaml.dump(amendment, f)
    
    return True

def apply_amendments(phase_id: str, repo_root: str = ".") -> List[Dict[str, Any]]:
    """Apply all pending amendments for phase"""
    pending_dir = Path(repo_root) / ".repo" / "amendments" / "pending"
    applied_dir = Path(repo_root) / ".repo" / "amendments" / "applied"
    applied_dir.mkdir(parents=True, exist_ok=True)
    
    applied = []
    pending_files = list(pending_dir.glob(f"*_{phase_id}.yaml"))
    
    for file_path in pending_files:
        with open(file_path, 'r') as f:
            amendment = yaml.safe_load(f)
        
        if _apply_amendment(phase_id, amendment, repo_root):
            applied.append(amendment)
            applied_file = applied_dir / file_path.name
            file_path.rename(applied_file)
    
    return applied

def _check_budget(phase_id: str, amendment_type: str, repo_root: str) -> bool:
    """Check if amendment is within budget"""
    from lib.state import load_phase_context
    
    context = load_phase_context(phase_id, repo_root)
    used = context.get("amendments_used", {})
    budget = context.get("amendments_budget", {})
    
    return used.get(amendment_type, 0) < budget.get(amendment_type, 0)

def _apply_amendment(phase_id: str, amendment: Dict[str, Any], repo_root: str) -> bool:
    """Apply a single amendment"""
    from lib.state import load_phase_context, save_phase_context
    
    amendment_type = amendment["type"]
    value = amendment["value"]
    
    context = load_phase_context(phase_id, repo_root)
    
    if amendment_type == "set_test_cmd":
        context["test_cmd"] = value
    elif amendment_type == "add_scope":
        scope_cache = context.get("scope_cache", {})
        scope_cache["additional"] = scope_cache.get("additional", []) + [value]
        context["scope_cache"] = scope_cache
    elif amendment_type == "note_baseline_shift":
        context["baseline_sha"] = value
    
    # Update usage count
    used = context.get("amendments_used", {})
    used[amendment_type] = used.get(amendment_type, 0) + 1
    context["amendments_used"] = used
    
    save_phase_context(phase_id, context, repo_root)
    return True
