#!/usr/bin/env python3
"""Tests for state management."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.state import (
    get_current_phase, set_current_phase, clear_current_phase,
    has_scope_justification, save_scope_justification,
    append_learning, get_recent_learnings
)


def test_set_and_get_current_phase(tmp_path):
    """Test setting and getting current phase."""
    current = set_current_phase("P01-test", tmp_path)
    
    assert current["phase_id"] == "P01-test"
    assert "started_at" in current
    assert "baseline_sha" in current
    
    retrieved = get_current_phase(tmp_path)
    assert retrieved["phase_id"] == "P01-test"


def test_clear_current_phase(tmp_path):
    """Test clearing current phase."""
    set_current_phase("P01-test", tmp_path)
    clear_current_phase(tmp_path)
    
    current = get_current_phase(tmp_path)
    assert current is None


def test_scope_justification(tmp_path):
    """Test saving and checking scope justification."""
    phase_id = "P01-test"
    files = ["out/file1.py", "out/file2.py"]
    justification = "These files were needed for X reason."
    
    # Initially no justification
    assert not has_scope_justification(phase_id, tmp_path)
    
    # Save justification
    save_scope_justification(phase_id, files, justification, tmp_path)
    
    # Now should exist
    assert has_scope_justification(phase_id, tmp_path)
    
    # Check file contents
    audit_file = tmp_path / ".repo" / "scope_audit" / f"{phase_id}.md"
    content = audit_file.read_text()
    assert "out/file1.py" in content
    assert justification in content


def test_append_learning(tmp_path):
    """Test appending learnings."""
    phase_id = "P01-test"
    learning = "Testing is important."
    
    append_learning(phase_id, learning, tmp_path)
    
    learnings_file = tmp_path / ".repo" / "learnings.md"
    assert learnings_file.exists()
    
    content = learnings_file.read_text()
    assert phase_id in content
    assert learning in content


def test_get_recent_learnings_empty(tmp_path):
    """Test getting learnings when file doesn't exist."""
    learnings = get_recent_learnings(3, tmp_path)
    assert "No learnings recorded" in learnings


def test_get_recent_learnings(tmp_path):
    """Test getting recent learnings."""
    append_learning("P01", "Learning 1", tmp_path)
    append_learning("P02", "Learning 2", tmp_path)
    append_learning("P03", "Learning 3", tmp_path)
    
    learnings = get_recent_learnings(2, tmp_path)
    assert "P02" in learnings or "P03" in learnings
