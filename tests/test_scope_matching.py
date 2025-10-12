"""Tests for scope pattern matching with globstar support."""

import sys
from pathlib import Path

# Add tools/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.scope import classify_files, check_forbidden_files


def test_globstar_recursive_matching():
    """Test that ** matches nested directories."""
    files = [
        "src/foo.py",
        "src/bar/baz.py",
        "src/bar/qux/deep.py",
        "docs/readme.md",
        "tests/test_foo.py"
    ]
    include = ["src/**/*.py"]
    exclude = []

    in_scope, out_of_scope = classify_files(files, include, exclude)

    # All .py files under src/ should be in scope
    assert "src/foo.py" in in_scope
    assert "src/bar/baz.py" in in_scope
    assert "src/bar/qux/deep.py" in in_scope

    # Non-src files should be out of scope
    assert "docs/readme.md" in out_of_scope
    assert "tests/test_foo.py" in out_of_scope


def test_single_star_vs_double_star():
    """Test difference between * and ** patterns."""
    files = [
        "src/foo.py",
        "src/sub/bar.py",
        "src/sub/deep/baz.py"
    ]

    # Single star - matches only in current dir
    include_single = ["src/*.py"]
    in_scope, out_of_scope = classify_files(files, include_single, [])

    assert "src/foo.py" in in_scope
    # Single star won't match nested paths with pathspec
    # (fnmatch would fail here - this is the key difference)

    # Double star - matches recursively
    include_double = ["src/**/*.py"]
    in_scope, out_of_scope = classify_files(files, include_double, [])

    assert "src/foo.py" in in_scope
    assert "src/sub/bar.py" in in_scope
    assert "src/sub/deep/baz.py" in in_scope


def test_exclude_patterns():
    """Test that exclude patterns override include."""
    files = [
        "src/foo.py",
        "src/test_bar.py",
        "src/sub/baz.py",
        "src/sub/test_qux.py"
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


def test_multiple_include_patterns():
    """Test multiple include patterns."""
    files = [
        "src/foo.py",
        "tests/test_bar.py",
        "docs/readme.md",
        "scripts/deploy.sh"
    ]
    include = ["src/**/*.py", "tests/**/*.py"]
    exclude = []

    in_scope, out_of_scope = classify_files(files, include, exclude)

    assert "src/foo.py" in in_scope
    assert "tests/test_bar.py" in in_scope
    assert "docs/readme.md" in out_of_scope
    assert "scripts/deploy.sh" in out_of_scope


def test_forbidden_files():
    """Test forbidden file detection."""
    files = [
        "src/foo.py",
        "requirements.txt",
        "pyproject.toml",
        "README.md"
    ]
    forbid = ["requirements.txt", "pyproject.toml"]

    forbidden = check_forbidden_files(files, forbid)

    assert "requirements.txt" in forbidden
    assert "pyproject.toml" in forbidden
    assert "src/foo.py" not in forbidden
    assert "README.md" not in forbidden


def test_forbidden_with_wildcards():
    """Test forbidden patterns with wildcards."""
    files = [
        "src/foo.py",
        ".env",
        ".env.local",
        "config/.secrets.yml",
        "README.md"
    ]
    forbid = [".env*", "**/.secrets.yml"]

    forbidden = check_forbidden_files(files, forbid)

    assert ".env" in forbidden
    assert ".env.local" in forbidden
    assert "config/.secrets.yml" in forbidden
    assert "src/foo.py" not in forbidden


def test_edge_case_empty_patterns():
    """Test behavior with empty patterns."""
    files = ["src/foo.py", "docs/readme.md"]

    # Empty include - all should be out of scope
    in_scope, out_of_scope = classify_files(files, [], [])
    assert len(in_scope) == 0
    assert len(out_of_scope) == 2

    # Empty exclude - no exclusions
    in_scope, out_of_scope = classify_files(files, ["**/*.py"], [])
    assert "src/foo.py" in in_scope


def test_edge_case_no_files():
    """Test behavior with no files."""
    in_scope, out_of_scope = classify_files([], ["**/*.py"], [])
    assert len(in_scope) == 0
    assert len(out_of_scope) == 0


def test_gitignore_style_patterns():
    """Test .gitignore-style patterns."""
    files = [
        "node_modules/foo.js",
        "src/node_modules/bar.js",  # nested
        ".git/config",
        "src/.git/HEAD",  # nested
        "build/output.js",
        "src/build/main.js"  # nested
    ]
    exclude = ["node_modules/**", ".git/**", "build/**"]

    in_scope, out_of_scope = classify_files(files, ["**/*"], exclude)

    # All excluded patterns should be out of scope
    assert "node_modules/foo.js" in out_of_scope
    assert ".git/config" in out_of_scope
    assert "build/output.js" in out_of_scope
