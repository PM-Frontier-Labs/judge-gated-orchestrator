"""
Tests for scope classification.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.scope import classify_files


def test_classify_simple_include():
    """Test simple include pattern matching."""
    changed_files = [
        "src/auth/login.py",
        "src/auth/user.py",
        "src/utils/helper.py",
        "tests/test_auth.py"
    ]
    
    include_patterns = ["src/auth/**", "tests/test_auth.py"]
    exclude_patterns = []
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    assert "src/auth/login.py" in in_scope
    assert "src/auth/user.py" in in_scope
    assert "tests/test_auth.py" in in_scope
    assert "src/utils/helper.py" in out_of_scope


def test_classify_with_exclude():
    """Test exclude pattern."""
    changed_files = [
        "src/auth/login.py",
        "src/auth/__pycache__/login.pyc",
        "src/utils/helper.py"
    ]
    
    include_patterns = ["src/**"]
    exclude_patterns = ["**/__pycache__/**"]
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    assert "src/auth/login.py" in in_scope
    assert "src/utils/helper.py" in in_scope
    assert "src/auth/__pycache__/login.pyc" in out_of_scope


def test_classify_wildcard_patterns():
    """Test wildcard pattern matching."""
    changed_files = [
        "README.md",
        "docs/api.md",
        "src/main.py"
    ]
    
    include_patterns = ["*.md", "docs/**"]
    exclude_patterns = []
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    assert "README.md" in in_scope
    assert "docs/api.md" in in_scope
    assert "src/main.py" in out_of_scope


def test_classify_empty_patterns():
    """Test with no include patterns."""
    changed_files = ["src/main.py", "tests/test.py"]
    
    include_patterns = []
    exclude_patterns = []
    
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    # With no include patterns, everything is out of scope
    assert len(in_scope) == 0
    assert len(out_of_scope) == 2
