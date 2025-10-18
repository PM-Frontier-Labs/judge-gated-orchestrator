"""
Feature module - Score calculation functionality.
"""


def calculate_score(value: int) -> int:
    """
    Calculate a score by doubling the input value.

    Args:
        value: Input integer value to calculate score from

    Returns:
        int: The calculated score (value * 2)

    Raises:
        TypeError: If value is not an integer
    """
    # Explicitly reject bool since bool is a subclass of int in Python
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"Expected int, got {type(value).__name__}")

    return value * 2
