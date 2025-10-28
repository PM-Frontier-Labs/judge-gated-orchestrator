#!/usr/bin/env python3
"""
Plan loading with embedded YAML briefs.

Supports both:
- New format: briefs embedded in plan.yaml
- Legacy format: briefs in separate .md files (backward compatible)
"""

import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class PlanError(Exception):
    """Plan loading or validation error."""
    pass


def load_plan(repo_root: Path = None) -> Dict[str, Any]:
    """
    Load and validate plan.yaml.
    
    Returns:
        Plan dictionary with phases
        
    Raises:
        PlanError: If plan is missing or invalid
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    plan_path = repo_root / ".repo" / "plan.yaml"
    
    if not plan_path.exists():
        raise PlanError(f"Plan not found: {plan_path}")
    
    try:
        with plan_path.open() as f:
            plan = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise PlanError(f"Invalid YAML in plan.yaml: {e}")
    
    # Validate basic structure
    if not isinstance(plan, dict):
        raise PlanError("Plan must be a dictionary")
    
    if "plan" not in plan:
        raise PlanError("Plan missing 'plan' key")
    
    if "phases" not in plan.get("plan", {}):
        raise PlanError("Plan missing 'phases' list")
    
    return plan


def get_phase(plan: Dict[str, Any], phase_id: str) -> Dict[str, Any]:
    """
    Get phase configuration by ID.
    
    Args:
        plan: Plan dictionary from load_plan()
        phase_id: Phase identifier (e.g., "P01-scaffold")
        
    Returns:
        Phase dictionary
        
    Raises:
        PlanError: If phase not found
    """
    phases = plan.get("plan", {}).get("phases", [])
    
    for phase in phases:
        if phase.get("id") == phase_id:
            return phase
    
    raise PlanError(f"Phase {phase_id} not found in plan")


def get_brief(plan: Dict[str, Any], phase_id: str, repo_root: Path = None) -> str:
    """
    Get brief for phase.
    
    Supports two formats:
    1. Embedded YAML brief (new format):
       phases:
         - id: P01
           brief: |
             # Objective
             ...
    
    2. External .md file (legacy format):
       .repo/briefs/P01-scaffold.md
    
    Args:
        plan: Plan dictionary
        phase_id: Phase identifier
        repo_root: Repository root (defaults to cwd)
        
    Returns:
        Brief content as string
        
    Raises:
        PlanError: If brief not found in either location
    """
    if repo_root is None:
        repo_root = Path.cwd()
    
    phase = get_phase(plan, phase_id)
    
    # Check for embedded brief (new format)
    if "brief" in phase:
        return phase["brief"]
    
    # Fall back to external .md file (legacy format)
    brief_path = repo_root / ".repo" / "briefs" / f"{phase_id}.md"
    
    if not brief_path.exists():
        raise PlanError(
            f"Brief not found for phase {phase_id}.\n"
            f"Expected either:\n"
            f"  1. Embedded in plan.yaml: phases[{phase_id}].brief\n"
            f"  2. External file: {brief_path}"
        )
    
    return brief_path.read_text()


def get_all_phases(plan: Dict[str, Any]) -> list[Dict[str, Any]]:
    """Get list of all phases in order."""
    return plan.get("plan", {}).get("phases", [])


def get_next_phase(plan: Dict[str, Any], current_phase_id: str) -> Optional[Dict[str, Any]]:
    """
    Get next phase after current phase.
    
    Returns:
        Next phase dict, or None if current is last phase
    """
    phases = get_all_phases(plan)
    
    for i, phase in enumerate(phases):
        if phase.get("id") == current_phase_id:
            if i + 1 < len(phases):
                return phases[i + 1]
            return None
    
    return None


def validate_plan_schema(plan: Dict[str, Any]) -> list[str]:
    """
    Validate plan schema and return list of errors.
    
    Returns:
        List of error messages (empty if valid)
    """
    errors = []
    
    # Check top-level structure
    if "plan" not in plan:
        errors.append("Missing 'plan' key")
        return errors
    
    plan_obj = plan["plan"]
    
    # Check required fields
    if "id" not in plan_obj:
        errors.append("Missing plan.id")
    
    if "phases" not in plan_obj:
        errors.append("Missing plan.phases")
        return errors
    
    phases = plan_obj["phases"]
    
    if not isinstance(phases, list):
        errors.append("plan.phases must be a list")
        return errors
    
    if len(phases) == 0:
        errors.append("plan.phases is empty")
    
    # Check each phase
    phase_ids = set()
    for i, phase in enumerate(phases):
        if not isinstance(phase, dict):
            errors.append(f"Phase {i} is not a dictionary")
            continue
        
        # Check required phase fields
        if "id" not in phase:
            errors.append(f"Phase {i} missing 'id'")
        else:
            phase_id = phase["id"]
            
            # Check for duplicate IDs
            if phase_id in phase_ids:
                errors.append(f"Duplicate phase ID: {phase_id}")
            phase_ids.add(phase_id)
        
        # Check that phase has either embedded brief or can fall back to .md
        if "brief" not in phase and "description" not in phase:
            errors.append(f"Phase {phase.get('id', i)} missing 'brief' or 'description'")
    
    return errors
