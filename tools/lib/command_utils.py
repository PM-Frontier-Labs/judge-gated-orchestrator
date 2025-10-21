#!/usr/bin/env python3
"""
Command Utilities: Centralized command reconstruction and execution.
Reduces duplication in test-scope and lint-scope command building.
"""

from typing import List, Optional
from pathlib import Path

def build_test_command(
    base_cmd: List[str], 
    files: List[str], 
    scope_mode: str = "scope"
) -> List[str]:
    """
    Build test command with scope filtering.
    
    Args:
        base_cmd: Base test command (e.g., ["pytest", "-v"])
        files: List of files to test
        scope_mode: "scope" to filter by files, "all" to run on all files
        
    Returns:
        Complete test command with file filtering
    """
    if scope_mode == "all" or not files:
        return base_cmd
    
    # Filter files to only include test files
    test_files = [f for f in files if _is_test_file(f)]
    
    if not test_files:
        return base_cmd
    
    # Add filtered files to command
    return base_cmd + test_files

def build_lint_command(
    base_cmd: List[str], 
    files: List[str], 
    scope_mode: str = "scope"
) -> List[str]:
    """
    Build lint command with scope filtering.
    
    Args:
        base_cmd: Base lint command (e.g., ["flake8"])
        files: List of files to lint
        scope_mode: "scope" to filter by files, "all" to run on all files
        
    Returns:
        Complete lint command with file filtering
    """
    if scope_mode == "all" or not files:
        return base_cmd
    
    # Filter files to only include lintable files
    lintable_files = [f for f in files if _is_lintable_file(f)]
    
    if not lintable_files:
        return base_cmd
    
    # Add filtered files to command
    return base_cmd + lintable_files

def _is_test_file(file_path: str) -> bool:
    """Check if file is a test file."""
    path = Path(file_path)
    
    # Check if it's in a test directory
    if "test" in path.parts:
        return True
    
    # Check if filename suggests it's a test
    name = path.name.lower()
    return (
        name.startswith("test_") or 
        name.endswith("_test.py") or 
        name.endswith("_test.ts") or
        name.endswith("_test.tsx")
    )

def _is_lintable_file(file_path: str) -> bool:
    """Check if file is lintable."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    # Common lintable file extensions
    lintable_extensions = {
        '.py', '.js', '.ts', '.tsx', '.jsx', 
        '.java', '.cpp', '.c', '.h', '.hpp',
        '.go', '.rs', '.rb', '.php', '.swift'
    }
    
    return suffix in lintable_extensions

def get_command_description(cmd: List[str]) -> str:
    """Get a human-readable description of a command."""
    if not cmd:
        return "No command"
    
    # Extract tool name and key flags
    tool = cmd[0]
    flags = [arg for arg in cmd[1:] if arg.startswith('-')]
    
    if flags:
        return f"{tool} {' '.join(flags)}"
    else:
        return tool

def validate_command(cmd: List[str]) -> tuple[bool, Optional[str]]:
    """
    Validate a command for basic issues.
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not cmd:
        return False, "Empty command"
    
    if not cmd[0]:
        return False, "Empty tool name"
    
    # Check for common issues
    if any(' ' in arg for arg in cmd if not arg.startswith('-')):
        return False, "Command arguments contain spaces (may need shell escaping)"
    
    return True, None
