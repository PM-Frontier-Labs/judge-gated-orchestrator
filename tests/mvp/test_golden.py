"""
Golden path tests for MVP module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mvp import hello_world


def test_hello_world():
    """Test that hello_world returns the expected greeting."""
    result = hello_world()
    assert result == "Hello from MVP!"
    assert isinstance(result, str)
    assert len(result) > 0
