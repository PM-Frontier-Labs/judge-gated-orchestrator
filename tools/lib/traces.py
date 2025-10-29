#!/usr/bin/env python3
"""
Test/lint command execution with trace file output.
"""

import subprocess
import time
from pathlib import Path
from typing import List, Optional, Dict, Any


def run_command_with_trace(
    command: List[str],
    repo_root: Path,
    traces_dir: Path,
    trace_name: str
) -> int:
    """
    Run command and save trace file.
    
    Args:
        command: Command to run as list of strings
        repo_root: Working directory
        traces_dir: Directory to write trace files
        trace_name: Name for trace file (e.g., "tests", "lint")
        
    Returns:
        Exit code
    """
    # Run command
    result = subprocess.run(
        command,
        cwd=repo_root,
        capture_output=True,
        text=True
    )
    
    # Write trace
    traces_dir.mkdir(parents=True, exist_ok=True)
    trace_file = traces_dir / f"last_{trace_name}.txt"
    
    trace_content = f"""Exit code: {result.returncode}
Timestamp: {time.time()}
Command: {' '.join(command)}
Working directory: {repo_root}

=== STDOUT ===
{result.stdout}

=== STDERR ===
{result.stderr}
"""
    
    trace_file.write_text(trace_content)
    
    return result.returncode


def build_test_command(phase: Dict[str, Any], plan: Dict[str, Any], mode: str = "simple") -> List[str]:
    """
    Build test command from phase/plan configuration.
    
    Supports phase-level command override for flexibility.
    
    Args:
        phase: Phase configuration
        plan: Plan configuration
        mode: "simple", "unit", or "integration"
        
    Returns:
        Command as list of strings
    """
    tests_config = phase.get("gates", {}).get("tests", {})
    
    # Check for phase-level test_command override (Priority 1B)
    phase_test_cmd = phase.get("test_command")
    if phase_test_cmd:
        return phase_test_cmd.split()
    
    # Check for custom command in test config
    if mode == "unit" and "unit" in tests_config:
        custom_cmd = tests_config["unit"].get("command")
        if custom_cmd:
            return custom_cmd.split()
    
    if mode == "integration" and "integration" in tests_config:
        custom_cmd = tests_config["integration"].get("command")
        if custom_cmd:
            return custom_cmd.split()
    
    # Check for plan-level test command
    plan_test_cmd = plan.get("plan", {}).get("test_command")
    if plan_test_cmd:
        return plan_test_cmd.split()
    
    # Default: pytest
    return ["pytest", "tests/", "-v"]


def build_lint_command(phase: Dict[str, Any], plan: Dict[str, Any]) -> List[str]:
    """
    Build lint command from configuration.
    
    Supports phase-level override for monorepo flexibility.
    """
    # Check for phase-level lint_command override (Priority 1B)
    phase_lint_cmd = phase.get("lint_command")
    if phase_lint_cmd:
        return phase_lint_cmd.split()
    
    # Check for plan-level lint command
    plan_lint_cmd = plan.get("plan", {}).get("lint_command")
    if plan_lint_cmd:
        return plan_lint_cmd.split()
    
    # Default: ruff
    return ["ruff", "check", "."]

