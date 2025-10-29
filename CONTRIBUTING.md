# Contributing to Judge-Gated Protocol

Thank you for your interest in contributing to the Judge-Gated Protocol! This document provides guidelines and instructions for contributing.

## 🎯 Project Philosophy

This is a **protocol, not a framework**. The implementation in this repository is a reference implementation following file-based conventions. Contributions should:

- Keep code simple and maintainable
- Prioritize clarity over cleverness
- Maintain the file-based, transparent design
- Avoid unnecessary abstractions

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Git
- Basic understanding of the protocol (read `README.md` and `GETTING_STARTED.md`)

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/PM-Frontier-Labs/judge-gated-orchestrator.git
cd judge-gated-orchestrator

# Install dependencies
pip install -r requirements.txt

# Run tests
python3 -m pytest tests/ -v

# Check code style
python3 -m ruff check tools/
```

## 📋 How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** with:
   - Clear description of the issue
   - Steps to reproduce
   - Expected vs actual behavior
   - Your environment (OS, Python version)
   - Relevant logs or error messages

### Suggesting Features

1. **Open an issue** to discuss the feature first
2. **Explain the use case** - why is this needed?
3. **Consider the philosophy** - does it fit the protocol's goals?
4. **Be specific** about the proposed solution

### Pull Requests

1. **Fork the repository** and create a branch
2. **Make your changes** following the coding standards below
3. **Add tests** for new functionality
4. **Update documentation** if needed
5. **Run tests** to ensure nothing breaks
6. **Submit a pull request** with a clear description

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_plan.py -v

# Run with coverage (if coverage installed)
python3 -m pytest tests/ --cov=tools --cov-report=term-missing
```

### Writing Tests

- Place tests in the `tests/` directory
- Name test files `test_*.py`
- Name test functions `test_*`
- Use descriptive names that explain what's being tested
- Include docstrings explaining the test purpose
- Test both success and failure cases
- Use `tempfile.TemporaryDirectory()` for file system tests

Example:
```python
def test_load_valid_plan():
    """Test loading a valid plan.yaml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        # ... test implementation
```

## 💻 Coding Standards

### Python Style

- Follow PEP 8 guidelines
- Use type hints for function parameters and returns
- Keep functions focused and single-purpose
- Maximum line length: 100 characters
- Use descriptive variable names

### Code Organization

```
tools/
├── phasectl.py       # User-facing CLI
├── judge.py          # Gate coordinator
└── lib/              # Shared utilities
    ├── gates.py      # Gate implementations
    ├── git_ops.py    # Git utilities
    ├── plan.py       # Plan loading
    ├── scope.py      # Scope matching
    ├── state.py      # State management
    └── traces.py     # Command tracing
```

### Error Handling

- Use custom exception classes (`PlanError`, `StateError`, `GateError`)
- Provide clear, actionable error messages
- Log errors appropriately
- Clean up resources in failure cases

### File Operations

- Use atomic writes (tempfile + os.replace)
- Handle missing files gracefully
- Validate paths before operations
- Use `Path` from `pathlib` instead of string paths

## 📝 Documentation

### Updating Documentation

- **README.md** - Overview and quick start
- **GETTING_STARTED.md** - Detailed setup guide for humans
- **PROTOCOL.md** - Execution manual for AI assistants
- **ARCHITECTURE.md** - Technical architecture details
- **GITHUB_SETUP.md** - GitHub-specific setup instructions

### Documentation Style

- Write for the target audience (humans vs AI)
- Use clear, concise language
- Include code examples
- Keep examples up to date with code changes
- Use markdown formatting consistently

### Inline Documentation

```python
def function_name(param: Type) -> ReturnType:
    """
    Brief description of what the function does.
    
    Args:
        param: Description of parameter
        
    Returns:
        Description of return value
        
    Raises:
        ErrorType: When this error occurs
    """
```

## 🔄 Git Workflow

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions/updates

### Commit Messages

Use conventional commit format:

```
type(scope): brief description

More detailed explanation if needed.

- Bullet points for multiple changes
- Reference issues with #123
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Test additions/updates
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

**Examples:**
```
feat(gates): add custom gate support

Add ability to define custom gates in plan.yaml.
Gates can now extend base gate class.

Closes #42
```

```
fix(state): handle missing state directory

Create .repo/state/ directory if it doesn't exist
before writing state files.

Fixes #38
```

## 🏗️ Architecture Guidelines

### Adding New Gates

1. Add gate implementation in `tools/lib/gates.py`
2. Follow existing gate pattern:
   ```python
   def check_my_gate(phase: Dict[str, Any], ...) -> List[str]:
       """
       Check my gate condition.
       
       Returns:
           List of issues (empty = pass)
       """
       issues = []
       # Check logic here
       return issues
   ```
3. Register gate in `judge.py`
4. Add tests in `tests/test_gates.py`
5. Document in README.md and PROTOCOL.md

### Adding New Commands

1. Add command handler in `tools/phasectl.py`
2. Follow existing command pattern
3. Update help text
4. Add tests
5. Document in all relevant docs

### Modifying State Schema

**State changes require careful consideration:**

1. Maintain backward compatibility
2. Update `tools/lib/state.py`
3. Add migration path if needed
4. Document changes
5. Update all state-related docs

## ✅ Pull Request Checklist

Before submitting a PR, ensure:

- [ ] Tests pass: `python3 -m pytest tests/ -v`
- [ ] Code follows style guidelines
- [ ] New functionality has tests
- [ ] Documentation is updated
- [ ] Commit messages follow conventions
- [ ] Branch is up to date with main
- [ ] No merge conflicts
- [ ] Changes are focused and related

## 🤝 Code Review Process

1. **Automated checks** run on PR submission
2. **Maintainer review** typically within 2-3 days
3. **Discussion and feedback** as needed
4. **Approval and merge** once ready

### Review Criteria

- Code quality and maintainability
- Test coverage
- Documentation completeness
- Adherence to protocol philosophy
- Backward compatibility

## 💡 Getting Help

- **Issues:** Ask questions in GitHub issues
- **Discussions:** Use GitHub discussions for general questions
- **Documentation:** Check docs before asking
- **Examples:** Look at existing code for patterns

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Thank You!

Your contributions help make the Judge-Gated Protocol better for everyone. We appreciate your time and effort!

---

**Questions?** Open an issue or start a discussion. We're here to help!
