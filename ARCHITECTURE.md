# Architecture Guide

**Audience:** Developers contributing to or extending the gated phase protocol

**Purpose:** Technical documentation of the protocol's architecture and design decisions

---

## Overview

The Gated Phase Protocol is built on a robust, modular architecture designed for production use. This document covers the key architectural improvements made to ensure reliability, testability, and maintainability.

## Core Architecture

### File-Based Protocol
The protocol is fundamentally file-based, not framework-based. All state lives in files:
- `.repo/plan.yaml` - Project configuration and phase definitions
- `.repo/briefs/` - Phase instructions and current state
- `.repo/critiques/` - Judge feedback and approvals
- `.repo/traces/` - Test output and execution traces
- `.repo/state/` - Runtime state and context

### Modular Design
The protocol is split into focused, testable modules:

```
tools/
├── phasectl.py          # Main controller (452 lines)
├── judge.py             # Gate validator (260 lines)
└── lib/                 # Shared utilities
    ├── gates.py         # Gate implementations (433 lines)
    ├── git_ops.py       # Git utilities (83 lines)
    ├── plan.py          # Plan loading (207 lines)
    ├── scope.py         # Scope matching (54 lines)
    ├── state.py         # State management (271 lines)
    └── traces.py        # Command tracing (102 lines)

Total: ~1,862 lines (79% reduction from v1's 5,895 lines)
```

## Key Architectural Features

### 1. Simple Gate System

**Philosophy:** Clear, focused gate implementations without over-abstraction.

**Gate Implementations:**
- **TestsGate** - Validate test execution results
- **LintGate** - Check linting results (optional)
- **DocsGate** - Validate documentation requirements
- **DriftGate** - Check for scope violations (with justification workflow)
- **LLMReviewGate** - LLM-based code review (optional)

**Benefits:**
- **Simplicity**: Straightforward implementations, easy to understand
- **Maintainability**: Minimal abstraction, easy to modify
- **Focused**: Each gate does one thing well
- **Conversation over Enforcement**: Scope drift can be justified, not just blocked

### 2. File-Based State Management

**Philosophy:** All state lives in files, making it transparent and recoverable.

**State Files:**
```python
.repo/
├── plan.yaml                    # Phase definitions (human-written)
├── briefs/CURRENT.json          # Active phase pointer
├── critiques/<phase>.{md,OK}    # Judge feedback
├── learnings.md                 # Accumulated insights
├── scope_audit/<phase>.md       # Drift justifications
├── state/
│   ├── current.json             # Current phase state
│   └── acknowledged.json        # Orient acknowledgment
└── traces/
    └── last_tests.txt           # Test output
```

**Benefits:**
- **Transparency**: All state is visible and inspectable
- **Recoverability**: Context recovery via `./orient.sh`
- **Simplicity**: JSON files, no databases
- **Debuggability**: Easy to understand and fix issues

### 3. Conversational Workflows

**Philosophy:** Dialog over blocking when issues arise.

**Scope Justification:**
```bash
# Instead of blocking on drift:
❌ Drift detected!
./tools/phasectl.py justify-scope P01
# Provide justification → saved for review
✅ Gates pass with warning
```

**Orient Acknowledgment:**
```bash
# Force context recovery:
./tools/phasectl.py next
❌ Must acknowledge orient first
./orient.sh                         # Review state
./tools/phasectl.py acknowledge-orient
✅ Advanced to next phase
```

**Benefits:**
- **Keeps work moving**: No blocking on scope drift
- **Preserves context**: Mandatory acknowledgment prevents context loss
- **Human review**: Justifications recorded for later review
- **Flexibility**: Pragmatic over dogmatic

### 4. Learning and Reflection

**Philosophy:** Capture institutional knowledge as you work.

**Reflection System:**
```bash
./tools/phasectl.py reflect P01
# "Tests caught a bug early. Always write tests first."
# Saved to .repo/learnings.md
# Visible in next ./orient.sh
```

**Benefits:**
- **Knowledge Retention**: Insights preserved across phases
- **Pattern Recognition**: See what works, what doesn't
- **Team Learning**: Shared understanding (even with yourself)
- **Continuous Improvement**: Build on past successes

## Design Principles

### 1. Fail Fast, Fail Clearly
- Validate inputs early with clear error messages
- Use type hints and schema validation
- Provide actionable guidance for common errors

### 2. Atomic Operations
- All file operations are atomic
- Use tempfile + os.replace pattern
- Automatic cleanup on failures

### 3. Graceful Degradation
- System continues operating with partial failures
- Optional features don't break core functionality
- Clear error messages for missing dependencies

### 4. Testability
- Clean interfaces and dependency injection
- Mockable components
- Comprehensive test coverage

### 5. Extensibility
- Pluggable gate system
- Centralized configuration
- Clear extension points

## Performance Considerations

### File Operations
- Atomic writes prevent corruption but add slight overhead
- File locking prevents race conditions
- Temporary files are cleaned up automatically

### Memory Usage
- File-based state keeps memory usage low
- No large in-memory data structures
- Garbage collection friendly

### Concurrency
- File locking prevents race conditions
- Atomic operations ensure consistency
- Multiple agents can work safely

## Security Considerations

### Protocol Integrity
- SHA256-based tamper detection
- Immutable protocol files
- Automatic integrity verification

### File Permissions
- Proper file permission handling
- Secure temporary file creation
- Cleanup of sensitive data

### Input Validation
- Schema validation for all inputs
- Sanitization of user-provided data
- Bounds checking for all operations

## Future Extensibility

### Adding New Gates
1. Create a new class inheriting from `GateInterface`
2. Implement `is_enabled()` and `run()` methods
3. Add to `GATE_REGISTRY` in `gate_interface.py`
4. Add tests for the new gate

### Adding New File Operations
1. Follow the atomic write pattern
2. Use `tempfile` + `os.replace`
3. Add proper error handling
4. Include cleanup on failures

### Adding New Dependencies
1. Add to `requirements.txt`
2. Add import error handling with helpful messages
3. Update documentation
4. Add tests for the new functionality

## Conclusion

The architectural improvements make the protocol production-ready with:
- **Reliability**: Comprehensive error handling and atomic operations
- **Testability**: Clean interfaces and comprehensive test coverage
- **Maintainability**: Modular design and centralized configuration
- **Extensibility**: Pluggable gate system and clear extension points
- **Performance**: Efficient file operations and low memory usage
- **Security**: Protocol integrity and input validation

These improvements ensure the protocol can handle real-world usage scenarios while remaining maintainable and extensible for future development.
