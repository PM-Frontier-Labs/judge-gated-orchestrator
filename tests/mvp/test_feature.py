"""
Tests for feature module.
"""

import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from mvp.feature import calculate_score


def test_calculate_score_positive():
    """Test calculate_score with positive values."""
    assert calculate_score(5) == 10
    assert calculate_score(100) == 200
    assert calculate_score(1) == 2


def test_calculate_score_zero():
    """Test calculate_score with zero."""
    assert calculate_score(0) == 0


def test_calculate_score_negative():
    """Test calculate_score with negative values."""
    assert calculate_score(-5) == -10
    assert calculate_score(-100) == -200


def test_calculate_score_type_validation():
    """Test that calculate_score validates input type."""
    with pytest.raises(TypeError):
        calculate_score("not an int")

    with pytest.raises(TypeError):
        calculate_score(3.14)

    with pytest.raises(TypeError):
        calculate_score(None)
