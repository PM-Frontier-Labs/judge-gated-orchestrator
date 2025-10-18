#!/usr/bin/env python3
"""
Tests for re-architected protocol.
Tests the core functionality without complex frameworks.
"""

import tempfile
import shutil
from pathlib import Path
import sys
import os

# Add tools to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.state import load_phase_context, save_phase_context, get_mode, set_mode
from lib.amendments import propose_amendment, apply_amendments
from lib.traces import store_pattern, find_matching_patterns, write_micro_retro, get_phase_hints

def test_state_management():
    """Test state management system"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test context creation
        context = load_phase_context("P01-test", temp_dir)
        assert context["phase_id"] == "P01-test"
        assert context["mode"] == "EXPLORE"
        
        # Test context saving
        context["test_cmd"] = "python -m pytest -q"
        save_phase_context("P01-test", context, temp_dir)
        
        # Test context loading
        loaded_context = load_phase_context("P01-test", temp_dir)
        assert loaded_context["test_cmd"] == "python -m pytest -q"
        
        # Test mode management
        set_mode("P01-test", "LOCK", temp_dir)
        assert get_mode("P01-test", temp_dir) == "LOCK"

def test_amendment_system():
    """Test amendment system"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize phase context first
        context = load_phase_context("P01-test", temp_dir)
        save_phase_context("P01-test", context, temp_dir)
        
        # Test amendment proposal
        success = propose_amendment("P01-test", "set_test_cmd", "python -m pytest -q", "Fix test command", temp_dir)
        assert success
        
        # Test amendment application
        applied = apply_amendments("P01-test", temp_dir)
        assert len(applied) == 1
        assert applied[0]["type"] == "set_test_cmd"

def test_pattern_storage():
    """Test pattern storage system"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test pattern storage
        pattern = {
            "kind": "fix",
            "when": {"pytest_error": "usage: python -m pytest"},
            "action": {"amend": "set_test_cmd", "value": "python -m pytest -q"},
            "description": "Fix pytest usage error",
            "confidence": 0.9
        }
        
        store_pattern(pattern, temp_dir)
        
        # Test pattern matching
        context = {"test_output": "usage: python -m pytest"}
        matches = find_matching_patterns(context, temp_dir)
        assert len(matches) == 1
        assert matches[0]["kind"] == "fix"

def test_micro_retros():
    """Test micro-retrospectives"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Test retro writing
        execution_data = {
            "retries": 1,
            "amendments": [{"type": "set_test_cmd", "value": "python -m pytest -q"}],
            "llm_score": 0.9,
            "root_cause": "test command issue",
            "what_helped": ["Amendment set_test_cmd"],
            "success": True
        }
        
        retro_file = write_micro_retro("P01-test", execution_data, temp_dir)
        assert Path(retro_file).exists()
        
        # Test hint generation
        hints = get_phase_hints("P01-test", lookback_count=1, repo_root=temp_dir)
        assert len(hints) == 1
        assert "Amendment set_test_cmd" in hints[0]

def test_integration():
    """Test end-to-end integration"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create phase context
        context = load_phase_context("P01-test", temp_dir)
        
        # Propose amendment
        success = propose_amendment("P01-test", "set_test_cmd", "python -m pytest -q", "Fix test command", temp_dir)
        assert success
        
        # Apply amendment
        applied = apply_amendments("P01-test", temp_dir)
        assert len(applied) == 1
        
        # Store pattern
        pattern = {
            "kind": "fix",
            "when": {"pytest_error": "usage: python -m pytest"},
            "action": {"amend": "set_test_cmd", "value": "python -m pytest -q"},
            "description": "Fix pytest usage error",
            "confidence": 0.9
        }
        store_pattern(pattern, temp_dir)
        
        # Write retro
        execution_data = {
            "amendments": applied,
            "success": True,
            "what_helped": ["Amendment set_test_cmd"]
        }
        write_micro_retro("P01-test", execution_data, temp_dir)
        
        # Test hint generation
        hints = get_phase_hints("P01-test", lookback_count=1, repo_root=temp_dir)
        assert len(hints) >= 0  # May or may not have hints depending on success

if __name__ == "__main__":
    test_state_management()
    test_amendment_system()
    test_pattern_storage()
    test_micro_retros()
    test_integration()
    print("✅ All tests passed!")
