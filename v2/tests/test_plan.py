#!/usr/bin/env python3
"""Tests for plan loading."""

import pytest
import yaml
from pathlib import Path
import sys

# Add lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.plan import load_plan, get_phase, get_brief, get_next_phase, PlanError


def test_load_plan_with_embedded_brief(tmp_path):
    """Test loading plan with embedded YAML brief."""
    repo_dir = tmp_path / ".repo"
    repo_dir.mkdir()
    
    plan = {
        "plan": {
            "id": "test-project",
            "phases": [
                {
                    "id": "P01-test",
                    "description": "Test phase",
                    "brief": "# Objective\nTest implementation",
                    "scope": {
                        "include": ["src/**"],
                    },
                    "gates": {
                        "tests": {"must_pass": True}
                    }
                }
            ]
        }
    }
    
    plan_file = repo_dir / "plan.yaml"
    with plan_file.open('w') as f:
        yaml.dump(plan, f)
    
    loaded = load_plan(tmp_path)
    assert loaded["plan"]["id"] == "test-project"
    assert len(loaded["plan"]["phases"]) == 1


def test_get_phase(tmp_path):
    """Test getting phase by ID."""
    repo_dir = tmp_path / ".repo"
    repo_dir.mkdir()
    
    plan = {
        "plan": {
            "id": "test",
            "phases": [
                {"id": "P01", "description": "Phase 1"},
                {"id": "P02", "description": "Phase 2"},
            ]
        }
    }
    
    plan_file = repo_dir / "plan.yaml"
    with plan_file.open('w') as f:
        yaml.dump(plan, f)
    
    loaded = load_plan(tmp_path)
    phase = get_phase(loaded, "P02")
    assert phase["id"] == "P02"
    assert phase["description"] == "Phase 2"


def test_get_phase_not_found(tmp_path):
    """Test error when phase not found."""
    repo_dir = tmp_path / ".repo"
    repo_dir.mkdir()
    
    plan = {
        "plan": {
            "id": "test",
            "phases": [{"id": "P01", "description": "Phase 1"}]
        }
    }
    
    plan_file = repo_dir / "plan.yaml"
    with plan_file.open('w') as f:
        yaml.dump(plan, f)
    
    loaded = load_plan(tmp_path)
    
    with pytest.raises(PlanError, match="Phase P99 not found"):
        get_phase(loaded, "P99")


def test_get_brief_embedded(tmp_path):
    """Test getting embedded brief."""
    repo_dir = tmp_path / ".repo"
    repo_dir.mkdir()
    
    brief_content = "# Test Brief\nObjective here"
    
    plan = {
        "plan": {
            "id": "test",
            "phases": [
                {
                    "id": "P01",
                    "brief": brief_content
                }
            ]
        }
    }
    
    plan_file = repo_dir / "plan.yaml"
    with plan_file.open('w') as f:
        yaml.dump(plan, f)
    
    loaded = load_plan(tmp_path)
    brief = get_brief(loaded, "P01", tmp_path)
    assert brief == brief_content


def test_get_brief_external_file(tmp_path):
    """Test getting brief from external .md file (legacy)."""
    repo_dir = tmp_path / ".repo"
    repo_dir.mkdir()
    briefs_dir = repo_dir / "briefs"
    briefs_dir.mkdir()
    
    brief_content = "# Test Brief\nFrom file"
    brief_file = briefs_dir / "P01.md"
    brief_file.write_text(brief_content)
    
    plan = {
        "plan": {
            "id": "test",
            "phases": [{"id": "P01", "description": "Test"}]
        }
    }
    
    plan_file = repo_dir / "plan.yaml"
    with plan_file.open('w') as f:
        yaml.dump(plan, f)
    
    loaded = load_plan(tmp_path)
    brief = get_brief(loaded, "P01", tmp_path)
    assert brief == brief_content


def test_get_next_phase(tmp_path):
    """Test getting next phase."""
    repo_dir = tmp_path / ".repo"
    repo_dir.mkdir()
    
    plan = {
        "plan": {
            "id": "test",
            "phases": [
                {"id": "P01", "description": "Phase 1"},
                {"id": "P02", "description": "Phase 2"},
                {"id": "P03", "description": "Phase 3"},
            ]
        }
    }
    
    plan_file = repo_dir / "plan.yaml"
    with plan_file.open('w') as f:
        yaml.dump(plan, f)
    
    loaded = load_plan(tmp_path)
    
    next_phase = get_next_phase(loaded, "P01")
    assert next_phase["id"] == "P02"
    
    next_phase = get_next_phase(loaded, "P02")
    assert next_phase["id"] == "P03"
    
    next_phase = get_next_phase(loaded, "P03")
    assert next_phase is None  # Last phase
