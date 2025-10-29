"""
Tests for gate implementations.
"""
import sys
from pathlib import Path
import tempfile

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.gates import check_artifacts, check_docs


def test_check_artifacts_dict_format():
    """Test artifacts gate with dict format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create some test files
        (repo_root / "README.md").write_text("# Test")
        (repo_root / "src").mkdir()
        (repo_root / "src" / "main.py").write_text("print('hello')")
        
        phase = {
            "artifacts": {
                "must_exist": ["README.md", "src/main.py"]
            }
        }
        
        issues = check_artifacts(phase, repo_root)
        assert len(issues) == 0


def test_check_artifacts_missing():
    """Test artifacts gate with missing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        phase = {
            "artifacts": {
                "must_exist": ["README.md", "missing.txt"]
            }
        }
        
        issues = check_artifacts(phase, repo_root)
        assert len(issues) == 2  # Both files missing
        assert any("README.md" in issue for issue in issues)
        assert any("missing.txt" in issue for issue in issues)


def test_check_artifacts_empty():
    """Test artifacts gate with empty files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create empty file
        (repo_root / "empty.txt").write_text("")
        
        phase = {
            "artifacts": ["empty.txt"]
        }
        
        issues = check_artifacts(phase, repo_root)
        assert len(issues) == 1
        assert "empty" in issues[0].lower()


def test_check_docs():
    """Test docs gate."""
    changed_files = ["src/main.py", "README.md", "tests/test.py"]
    
    phase = {
        "id": "P01-test",
        "gates": {
            "docs": {
                "must_update": ["README.md"]
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Create the doc file
        (repo_root / "README.md").write_text("# Test")
        
        # Docs were updated
        issues = check_docs(phase, changed_files, repo_root)
        assert len(issues) == 0


def test_check_docs_not_updated():
    """Test docs gate when docs not updated."""
    changed_files = ["src/main.py", "tests/test.py"]
    
    phase = {
        "id": "P01-test",
        "gates": {
            "docs": {
                "must_update": ["README.md"]
            }
        }
    }
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        
        # Docs NOT updated
        issues = check_docs(phase, changed_files, repo_root)
        assert len(issues) > 0
        assert "README.md" in issues[0]
