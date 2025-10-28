#!/usr/bin/env python3
"""Tests for gate implementations."""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.gates import check_artifacts, check_docs, check_scope
from lib.scope import classify_files


def test_check_artifacts_pass(tmp_path):
    """Test artifacts gate passes when files exist."""
    # Create required files
    (tmp_path / "file1.py").write_text("content")
    (tmp_path / "file2.txt").write_text("data")
    
    phase = {
        "artifacts": {
            "must_exist": ["file1.py", "file2.txt"]
        }
    }
    
    issues = check_artifacts(phase, tmp_path)
    assert len(issues) == 0


def test_check_artifacts_missing(tmp_path):
    """Test artifacts gate fails when files missing."""
    phase = {
        "artifacts": {
            "must_exist": ["missing.py"]
        }
    }
    
    issues = check_artifacts(phase, tmp_path)
    assert len(issues) == 1
    assert "missing.py" in issues[0]


def test_check_artifacts_empty(tmp_path):
    """Test artifacts gate fails for empty files."""
    (tmp_path / "empty.py").write_text("")
    
    phase = {
        "artifacts": {
            "must_exist": ["empty.py"]
        }
    }
    
    issues = check_artifacts(phase, tmp_path)
    assert len(issues) == 1
    assert "empty" in issues[0].lower()


def test_check_docs_pass(tmp_path):
    """Test docs gate passes when docs updated."""
    (tmp_path / "docs.md").write_text("# Documentation\nContent")
    
    phase = {
        "id": "P01",
        "gates": {
            "docs": {
                "must_update": ["docs.md"]
            }
        }
    }
    
    changed_files = ["docs.md", "src/code.py"]
    
    issues = check_docs(phase, changed_files, tmp_path)
    assert len(issues) == 0


def test_check_docs_not_updated(tmp_path):
    """Test docs gate fails when docs not in changed files."""
    (tmp_path / "docs.md").write_text("# Documentation")
    
    phase = {
        "id": "P01",
        "gates": {
            "docs": {
                "must_update": ["docs.md"]
            }
        }
    }
    
    changed_files = ["src/code.py"]  # docs.md NOT in changes
    
    issues = check_docs(phase, changed_files, tmp_path)
    assert len(issues) == 1
    assert "not updated" in issues[0].lower()


def test_classify_files_simple():
    """Test file classification."""
    changed_files = [
        "src/main.py",
        "src/utils.py",
        "tests/test_main.py",
        "README.md",
        "tools/script.py"
    ]
    
    include_patterns = ["src/**", "tests/**"]
    exclude_patterns = []
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    assert "src/main.py" in in_scope
    assert "src/utils.py" in in_scope
    assert "tests/test_main.py" in in_scope
    assert "README.md" in out_of_scope
    assert "tools/script.py" in out_of_scope


def test_classify_files_with_exclude():
    """Test file classification with exclusions."""
    changed_files = [
        "src/main.py",
        "src/legacy/old.py",
        "tests/test_main.py"
    ]
    
    include_patterns = ["src/**", "tests/**"]
    exclude_patterns = ["src/legacy/**"]
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    assert "src/main.py" in in_scope
    assert "src/legacy/old.py" in out_of_scope  # Excluded
    assert "tests/test_main.py" in in_scope
