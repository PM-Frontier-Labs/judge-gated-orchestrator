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

## Testing

Run tests with:
```bash
pytest tests/mvp/test_golden.py -v
```

## Development

This module is part of a two-phase demonstration:
1. **P01-scaffold**: Initial module structure (this phase)
2. **P02-impl-feature**: Add feature implementation with scoring logic
