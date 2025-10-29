"""
Tests for plan loading and validation.
"""
import pytest
from pathlib import Path
import tempfile
import yaml

import sys
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.plan import load_plan, get_phase, get_brief, PlanError


def test_load_valid_plan():
    """Test loading a valid plan.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        repo_dir = repo_root / ".repo"
        repo_dir.mkdir()
        
        plan_data = {
            "plan": {
                "id": "test-plan",
                "phases": [
                    {
                        "id": "P01-test",
                        "brief": "Test brief",
                        "gates": {}
                    }
                ]
            }
        }
        
        plan_path = repo_dir / "plan.yaml"
        with open(plan_path, "w") as f:
            yaml.dump(plan_data, f)
        
        plan = load_plan(repo_root)
        assert plan["plan"]["id"] == "test-plan"
        assert len(plan["plan"]["phases"]) == 1


def test_load_missing_plan():
    """Test loading when plan.yaml doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        with pytest.raises(PlanError, match="Plan not found"):
            load_plan(repo_root)


def test_get_phase():
    """Test retrieving a phase by ID."""
    plan = {
        "plan": {
            "phases": [
                {"id": "P01-test", "brief": "Test"},
                {"id": "P02-test", "brief": "Test 2"}
            ]
        }
    }
    
    phase = get_phase(plan, "P01-test")
    assert phase["id"] == "P01-test"
    
    phase2 = get_phase(plan, "P02-test")
    assert phase2["id"] == "P02-test"


def test_get_phase_not_found():
    """Test retrieving a non-existent phase."""
    plan = {
        "plan": {
            "phases": [
                {"id": "P01-test", "brief": "Test"}
            ]
        }
    }
    
    with pytest.raises(PlanError, match="Phase P99-missing not found"):
        get_phase(plan, "P99-missing")


def test_get_brief_embedded():
    """Test getting an embedded brief."""
    plan = {
        "plan": {
            "phases": [
                {"id": "P01-test", "brief": "# Test Brief\n\nThis is a test."}
            ]
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        brief = get_brief(plan, "P01-test", repo_root)
        assert "Test Brief" in brief
        assert "This is a test" in brief
