#!/usr/bin/env python3
"""
Tests for pathspec requirement enforcement.

Tests that pathspec is properly required and the import error is handled.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch

# Add tools/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


class TestPathspecRequirement:
    """Test that pathspec is properly required."""
    
    def test_pathspec_import_success(self):
        """Test that pathspec imports successfully when available."""
        # This should not raise an exception
        from lib.scope import matches_pattern, classify_files
        assert callable(matches_pattern)
        assert callable(classify_files)
    
    def test_pathspec_import_error(self):
        """Test that ImportError is raised when pathspec is missing."""
        with patch.dict('sys.modules', {'pathspec': None}):
            with pytest.raises(ImportError) as exc_info:
                # Re-import the module to trigger the import error
                import importlib
                importlib.reload(sys.modules['lib.scope'])
            
            assert "pathspec is required for scope resolution" in str(exc_info.value)
            assert "pip install pathspec" in str(exc_info.value)
    
    def test_pathspec_functionality(self):
        """Test that pathspec functionality works correctly."""
        from lib.scope import matches_pattern, classify_files
        
        # Test matches_pattern
        patterns = ["src/**/*.py", "tests/**/*.py"]
        assert matches_pattern("src/foo.py", patterns) == True
        assert matches_pattern("src/sub/bar.py", patterns) == True
        assert matches_pattern("tests/test_foo.py", patterns) == True
        assert matches_pattern("docs/readme.md", patterns) == False
        
        # Test classify_files
        files = ["src/foo.py", "src/sub/bar.py", "tests/test_foo.py", "docs/readme.md"]
        include = ["src/**/*.py", "tests/**/*.py"]
        exclude = []
        
        in_scope, out_of_scope = classify_files(files, include, exclude)
        
        assert "src/foo.py" in in_scope
        assert "src/sub/bar.py" in in_scope
        assert "tests/test_foo.py" in in_scope
        assert "docs/readme.md" in out_of_scope
    
    def test_pathspec_globstar_support(self):
        """Test that ** globstar patterns work correctly."""
        from lib.scope import matches_pattern
        
        # Test recursive matching with **
        patterns = ["src/**/*.py"]
        
        # These should match
        assert matches_pattern("src/foo.py", patterns) == True
        assert matches_pattern("src/sub/bar.py", patterns) == True
        assert matches_pattern("src/sub/deep/baz.py", patterns) == True
        
        # These should not match
        assert matches_pattern("src/foo.txt", patterns) == False
        assert matches_pattern("docs/readme.md", patterns) == False
        assert matches_pattern("tests/test_foo.py", patterns) == False
    
    def test_pathspec_exclude_patterns(self):
        """Test that exclude patterns work correctly."""
        from lib.scope import classify_files
        
        files = [
            "src/foo.py",
            "src/test_bar.py",
            "src/sub/baz.py",
            "src/sub/test_qux.py",
            "docs/readme.md"
        ]
        include = ["src/**/*.py"]
        exclude = ["**/test_*.py"]
        
        in_scope, out_of_scope = classify_files(files, include, exclude)
        
        # Regular files should be in scope
        assert "src/foo.py" in in_scope
        assert "src/sub/baz.py" in in_scope
        
        # Test files should be excluded
        assert "src/test_bar.py" in out_of_scope
        assert "src/sub/test_qux.py" in out_of_scope
        
        # Non-src files should be out of scope
        assert "docs/readme.md" in out_of_scope
    
    def test_pathspec_gitignore_style(self):
        """Test .gitignore-style patterns."""
        from lib.scope import classify_files
        
        files = [
            "node_modules/foo.js",
            "src/node_modules/bar.js",
            ".git/config",
            "src/.git/HEAD",
            "build/output.js",
            "src/build/main.js"
        ]
        include = ["**/*"]
        exclude = ["node_modules/**", ".git/**", "build/**"]
        
        in_scope, out_of_scope = classify_files(files, include, exclude)
        
        # Files matching exclude patterns should be out of scope
        assert "node_modules/foo.js" in out_of_scope
        assert ".git/config" in out_of_scope
        assert "build/output.js" in out_of_scope
        
        # Nested files might still be in scope depending on pathspec behavior
        # This test verifies the basic functionality works
