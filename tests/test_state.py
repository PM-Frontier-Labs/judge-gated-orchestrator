"""
Tests for state management.
"""
import sys
from pathlib import Path
import tempfile
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.state import (
    get_current_phase, set_current_phase, clear_current_phase,
    is_orient_acknowledged, acknowledge_orient,
    has_scope_justification, save_scope_justification
)


def test_set_and_get_current_phase():
    """Test setting and getting current phase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Set current phase
        current = set_current_phase("P01-test", repo_root)
        assert current["phase_id"] == "P01-test"
        assert "baseline_sha" in current
        assert "started_at" in current
        
        # Get current phase
        retrieved = get_current_phase(repo_root)
        assert retrieved["phase_id"] == "P01-test"


def test_clear_current_phase():
    """Test clearing current phase."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Set then clear
        set_current_phase("P01-test", repo_root)
        assert get_current_phase(repo_root) is not None
        
        clear_current_phase(repo_root)
        assert get_current_phase(repo_root) is None


def test_orient_acknowledgment():
    """Test orient acknowledgment workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Initially not acknowledged
        assert not is_orient_acknowledged("P01-test", repo_root)
        
        # Acknowledge
        acknowledge_orient("P01-test", "I understand the current state", repo_root)
        
        # Now should be acknowledged
        assert is_orient_acknowledged("P01-test", repo_root)


def test_scope_justification():
    """Test scope justification workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Initially no justification
        assert not has_scope_justification("P01-test", repo_root)
        
        # Save justification
        files = ["src/utils.py", "config/settings.py"]
        justification = "These changes were necessary because..."
        save_scope_justification("P01-test", files, justification, repo_root)
        
        # Now should have justification
        assert has_scope_justification("P01-test", repo_root)
        
        # Check file was created
        audit_file = repo_root / ".repo" / "scope_audit" / "P01-test.md"
        assert audit_file.exists()
        content = audit_file.read_text()
        assert "src/utils.py" in content
        assert "necessary because" in content
