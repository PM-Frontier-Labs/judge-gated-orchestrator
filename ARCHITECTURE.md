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
├── phasectl.py          # Main controller
├── judge.py             # Gate validator (refactored)
├── llm_judge.py         # LLM-based code review
└── lib/                 # Shared utilities
    ├── gate_interface.py    # Pluggable gate system
    ├── gates.py             # Individual gate implementations
    ├── file_lock.py         # Atomic file operations
    ├── command_utils.py     # Command builders
    ├── llm_config.py        # Centralized LLM config
    ├── git_ops.py           # Git utilities
    ├── scope.py             # Scope resolution
    ├── traces.py            # Pattern storage
    ├── amendments.py        # Amendment system
    ├── state.py             # State management
    ├── protocol_guard.py    # Integrity verification
    └── plan_validator.py    # Schema validation
```

## Key Architectural Improvements

### 1. Pluggable Gate System

**Problem:** The original `judge.py` was a monolithic file with hardcoded gate logic, making it difficult to test and extend.

**Solution:** Clean gate interface with individual gate classes.

```python
class GateInterface(ABC):
    @abstractmethod
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        pass
```

**Benefits:**
- **Testability**: Each gate can be tested independently
- **Extensibility**: New gates can be added without modifying core logic
- **Maintainability**: Gate logic is isolated and focused
- **Error Handling**: Graceful error handling per gate

**Gate Implementations:**
- `ArtifactsGate` - Check for required artifacts
- `TestsGate` - Validate test execution results
- `LintGate` - Check linting results
- `DocsGate` - Validate documentation requirements
- `DriftGate` - Check for plan drift
- `LLMReviewGate` - LLM-based code review
- `IntegrityGate` - Protocol integrity verification

### 2. Atomic File Operations

**Problem:** Concurrent file operations could lead to data corruption, especially in CI/multi-agent scenarios.

**Solution:** Atomic writes using `tempfile` + `os.replace` pattern.

```python
def safe_write_json(file_path: Path, data: Dict[str, Any]) -> None:
    with tempfile.NamedTemporaryFile(
        mode='w', 
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix='.tmp',
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)
        json.dump(data, temp_file)
        temp_file.flush()
        os.fsync(temp_file.fileno())
    
    os.replace(temp_path, file_path)
```

**Benefits:**
- **Data Integrity**: No partial writes or corruption
- **Concurrency Safety**: File locking prevents race conditions
- **Error Recovery**: Automatic cleanup on failures
- **Consistency**: All file operations use the same pattern

### 3. Robust Error Handling

**Problem:** Technical errors were cryptic and didn't provide actionable guidance.

**Solution:** Smart error classification and actionable error messages.

```python
def explain_error(error: Exception) -> str:
    error_type = classify_error(error)
    details = extract_error_details(error)
    
    if error_type == "insufficient_budget":
        return f"❌ Insufficient budget: {details['current']}/{details['required']}\n💡 Run: ./tools/phasectl.py amend propose add_budget {details['needed']}"
    elif error_type == "missing_brief":
        return f"❌ Missing brief: {details['phase_id']}\n💡 Run: ./tools/phasectl.py generate-briefs"
    # ... more error types
```

**Benefits:**
- **User Experience**: Clear, actionable error messages
- **Debugging**: Faster issue resolution
- **Self-Service**: Users can fix issues without support
- **Graceful Degradation**: System continues operating with partial failures

### 4. Self-Updating Tools

**Problem:** Protocol tools could become outdated, leading to compatibility issues.

**Solution:** Automatic version detection and atomic updates.

```python
def auto_update_protocol():
    if not check_protocol_version():
        print("⚠️  Using outdated protocol tools")
        if can_update():
            create_tool_backup()
            try:
                run_install_script()
                verify_tool_integrity()
            except Exception:
                rollback_tools()
                raise
```

**Benefits:**
- **Zero Maintenance**: Tools stay current automatically
- **Atomic Updates**: Backup, update, verify, rollback on failure
- **Integrity Verification**: SHA256 checksums ensure update integrity
- **Zero Downtime**: Updates don't interrupt ongoing work

### 5. Enhanced Dependencies

**Problem:** Silent fallbacks and inconsistent behavior across different environments.

**Solution:** Mandatory dependencies with clear error messages.

```python
try:
    import pathspec
except ImportError:
    raise ImportError(
        "pathspec is required for scope resolution. "
        "Run: pip install pathspec"
    )
```

**Benefits:**
- **Consistency**: Same behavior across all environments
- **Predictability**: No silent fallbacks or unexpected behavior
- **Clear Errors**: Helpful error messages for missing dependencies
- **Reliability**: Mandatory dependencies ensure functionality

### 6. Centralized Configuration

**Problem:** LLM configuration was scattered across multiple files with inconsistent pricing and model names.

**Solution:** Centralized configuration module.

```python
# tools/lib/llm_config.py
DEFAULT_LLM_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 2000,
    "temperature": 0,
    "budget_usd": 2.0,
    # ... other config
}

PRICING = {
    "input_per_1k": 0.003,
    "output_per_1k": 0.015,
}
```

**Benefits:**
- **Consistency**: Single source of truth for LLM configuration
- **Maintainability**: Easy to update pricing and model names
- **Accuracy**: Consistent cost calculations across the system
- **Extensibility**: Easy to add new LLM providers

### 7. Comprehensive Testing

**Problem:** Limited test coverage made it difficult to ensure reliability and catch regressions.

**Solution:** Comprehensive test suite with 86 test cases.

**Test Categories:**
- **Unit Tests**: Individual component testing
- **Integration Tests**: End-to-end workflow testing
- **Error Scenario Tests**: Edge cases and failure modes
- **Concurrency Tests**: Multi-process safety verification

**Benefits:**
- **Reliability**: Comprehensive test coverage ensures stability
- **Regression Prevention**: Tests catch breaking changes
- **Documentation**: Tests serve as usage examples
- **Confidence**: Safe to make changes with test coverage

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
