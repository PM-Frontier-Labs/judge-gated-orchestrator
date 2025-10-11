# MVP Module

## Overview

The MVP module demonstrates a judge-gated autonomous orchestration system for Claude Code.

## Purpose

This module serves as a proof of concept for:
- Judge-enforced quality gates
- Plan-adherence validation
- Autonomous multi-phase execution
- Test-driven development flow

## API

### `hello_world() -> str`

Returns a simple greeting message.

**Returns:**
- `str`: A greeting message

**Example:**
```python
from mvp import hello_world

message = hello_world()
print(message)  # Output: "Hello from MVP!"
```

## Feature

### `calculate_score(value: int) -> int`

Calculates a score by doubling the input value.

**Parameters:**
- `value` (int): Input integer value to calculate score from

**Returns:**
- `int`: The calculated score (value * 2)

**Raises:**
- `TypeError`: If value is not an integer

**Example:**
```python
from mvp.feature import calculate_score

score = calculate_score(42)
print(score)  # Output: 84

# Edge cases
print(calculate_score(0))   # Output: 0
print(calculate_score(-10)) # Output: -20
```

## Testing

Run all tests with:
```bash
pytest tests/mvp/ -v
```

Run specific tests:
```bash
pytest tests/mvp/test_golden.py -v  # Golden path tests
pytest tests/mvp/test_feature.py -v  # Feature tests
```

## Development

This module is part of a two-phase demonstration:
1. **P01-scaffold**: Initial module structure ✅
2. **P02-impl-feature**: Add feature implementation with scoring logic ✅
