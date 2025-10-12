#!/usr/bin/env python3
"""
Generate COMPLETE_PACKAGE files containing the entire codebase.

This bundles all documentation, code, tests, and configuration into
single-file packages for easy sharing and review.
"""

from pathlib import Path
from datetime import date

REPO_ROOT = Path(__file__).parent.parent

# Count lines of code
def count_loc():
    """Count total lines of Python code."""
    total = 0
    for pattern in ["tools/**/*.py", "src/**/*.py", "tests/**/*.py"]:
        for file in REPO_ROOT.glob(pattern):
            if "__pycache__" not in str(file):
                total += len(file.read_text().splitlines())
    return total

def read_file(relative_path):
    """Read file content with error handling."""
    try:
        return (REPO_ROOT / relative_path).read_text()
    except Exception as e:
        return f"[Error reading {relative_path}: {e}]"

def generate_package():
    """Generate complete package file."""

    loc = count_loc()
    today = date.today().strftime("%Y-%m-%d")

    package = f"""# JUDGE-GATED ORCHESTRATOR - COMPLETE PACKAGE
# Version: 2.5 ({loc} LOC, includes Phase 1+2+2.5)
# Generated: {today}
# Purpose: Autonomous AI execution protocol with quality gates

===============================================================================
SECTION 1: DOCUMENTATION (HUMANS)
===============================================================================

--- README.md ---
{read_file('README.md')}

--- GETTING_STARTED.md ---
{read_file('GETTING_STARTED.md')}

--- TESTME.md ---
{read_file('TESTME.md')}

===============================================================================
SECTION 2: DOCUMENTATION (AI ASSISTANTS)
===============================================================================

--- LLM_PLANNING.md ---
{read_file('LLM_PLANNING.md')}

--- PROTOCOL.md ---
{read_file('PROTOCOL.md')}

===============================================================================
SECTION 3: CORE TOOLS (PYTHON)
===============================================================================

--- tools/phasectl.py ---
{read_file('tools/phasectl.py')}

--- tools/judge.py ---
{read_file('tools/judge.py')}

--- tools/llm_judge.py ---
{read_file('tools/llm_judge.py')}

--- tools/generate_manifest.py ---
{read_file('tools/generate_manifest.py')}

===============================================================================
SECTION 4: SHARED LIBRARIES
===============================================================================

--- tools/lib/__init__.py ---
{read_file('tools/lib/__init__.py')}

--- tools/lib/git_ops.py ---
{read_file('tools/lib/git_ops.py')}

--- tools/lib/scope.py ---
{read_file('tools/lib/scope.py')}

--- tools/lib/traces.py ---
{read_file('tools/lib/traces.py')}

--- tools/lib/protocol_guard.py ---
{read_file('tools/lib/protocol_guard.py')}

--- tools/lib/plan_validator.py ---
{read_file('tools/lib/plan_validator.py')}

--- tools/lib/file_lock.py ---
{read_file('tools/lib/file_lock.py')}

===============================================================================
SECTION 5: TESTS
===============================================================================

--- tests/mvp/test_golden.py ---
{read_file('tests/mvp/test_golden.py')}

--- tests/mvp/test_feature.py ---
{read_file('tests/mvp/test_feature.py')}

--- tests/test_scope_matching.py ---
{read_file('tests/test_scope_matching.py')}

--- tests/test_test_scoping.py ---
{read_file('tests/test_test_scoping.py')}

===============================================================================
SECTION 6: CONFIGURATION
===============================================================================

--- .repo/plan.yaml ---
{read_file('.repo/plan.yaml')}

--- .repo/protocol_manifest.json ---
{read_file('.repo/protocol_manifest.json')}

--- requirements.txt ---
{read_file('requirements.txt')}

===============================================================================
SECTION 7: EXAMPLE CODE
===============================================================================

--- src/mvp/__init__.py ---
{read_file('src/mvp/__init__.py')}

--- src/mvp/feature.py ---
{read_file('src/mvp/feature.py')}

===============================================================================
SECTION 8: PROJECT STRUCTURE
===============================================================================

```
judge-gated-orchestrator/
├── .repo/
│   ├── briefs/
│   │   ├── CURRENT.json         # Points to active phase
│   │   ├── P01-scaffold.md      # Phase briefs
│   │   └── P02-impl-feature.md
│   ├── critiques/
│   │   ├── P01-scaffold.OK      # Approval markers
│   │   ├── P02-impl-feature.md  # Or critique files
│   │   └── *.json               # Machine-readable versions (Phase 2)
│   ├── traces/
│   │   ├── last_test.txt        # Test execution output
│   │   └── last_lint.txt
│   ├── plan.yaml                # Roadmap + gates
│   └── protocol_manifest.json   # SHA256 hashes for integrity
├── tools/
│   ├── phasectl.py              # Controller (review/next)
│   ├── judge.py                 # Gate validator
│   ├── llm_judge.py             # Optional LLM review
│   ├── generate_manifest.py     # Update protocol hashes
│   ├── generate_complete_package.py  # This script
│   └── lib/                     # Shared utilities
│       ├── __init__.py
│       ├── git_ops.py           # Git operations
│       ├── scope.py             # Pattern matching (Phase 1: pathspec)
│       ├── traces.py            # Trace file handling
│       ├── protocol_guard.py    # Integrity checks
│       ├── plan_validator.py    # Schema validation
│       └── file_lock.py         # Concurrent execution prevention
├── src/mvp/                     # Example code
├── tests/                       # Test suite
│   ├── mvp/
│   ├── test_scope_matching.py   # Phase 1 tests
│   └── test_test_scoping.py     # Phase 2.5 tests
├── docs/mvp.md                  # Documentation
├── orient.sh                    # Status in 10 seconds
├── README.md                    # Human-readable overview
├── GETTING_STARTED.md           # Human setup and usage guide
├── LLM_PLANNING.md              # AI planning mode guide
├── PROTOCOL.md                  # AI execution mode manual
├── TESTME.md                    # Validation guide (12 tests)
├── COMPLETE_PACKAGE.txt         # Complete bundled codebase
├── COMPLETE_PACKAGE.md          # Markdown version
└── requirements.txt             # Python dependencies
```

===============================================================================
SECTION 9: USAGE GUIDE
===============================================================================

## Quick Start

```bash
# 1. Install
git clone <repo-url>
cd judge-gated-orchestrator
pip install -r requirements.txt

# 2. Orient (see current state)
./orient.sh

# 3. Review current phase
./tools/phasectl.py review P02-impl-feature

# 4. Advance to next phase (if approved)
./tools/phasectl.py next
```

## Key Commands

**./orient.sh** - Show current state in <10 seconds
**./tools/phasectl.py review <phase>** - Submit for review
**./tools/phasectl.py next** - Advance to next phase
**./tools/generate_manifest.py** - Update protocol hashes

## Features by Phase

**Phase 1 (Critical Fixes):**
- Per-phase baseline SHA (stable diffs)
- Docs gate verifies actual changes
- LLM review includes all changes
- Pathspec for proper globstar support

**Phase 2 (Need-to-Have):**
- Atomic critique writes (no lost feedback)
- Correct git commands (committed vs uncommitted)
- Machine-readable JSON output
- LLM gate configuration

**Phase 2.5 (Real-World):**
- Test scoping (run only relevant tests)
- Test quarantine (skip flaky/legacy tests)

## Testing

Run full validation suite:
```bash
pytest tests/ -v          # Run all tests (21 tests)
ruff check .              # Lint check
./tools/generate_manifest.py  # Regenerate hashes
```

Follow TESTME.md for comprehensive validation (12 tests, 25-30 minutes).

## Protocol Integrity

Protected files (SHA256-verified):
- tools/judge.py
- tools/phasectl.py
- tools/llm_judge.py
- tools/lib/*.py
- .repo/plan.yaml
- .repo/protocol_manifest.json

Modification requires dedicated protocol maintenance phase.

===============================================================================
END OF PACKAGE
===============================================================================

Total: {loc} lines of Python code across {len(list(REPO_ROOT.glob('**/*.py')))} files
Generated: {today}
Version: 2.5 (Phase 1 + Phase 2 + Phase 2.5)
"""

    return package

def main():
    """Generate both .txt and .md versions."""
    print("Generating complete package...")

    package = generate_package()

    # Write .txt version
    txt_file = REPO_ROOT / "COMPLETE_PACKAGE.txt"
    txt_file.write_text(package)
    print(f"✓ Generated {txt_file.relative_to(REPO_ROOT)}")

    # Write .md version (same content, markdown-friendly)
    md_file = REPO_ROOT / "COMPLETE_PACKAGE.md"
    md_file.write_text(package)
    print(f"✓ Generated {md_file.relative_to(REPO_ROOT)}")

    loc = count_loc()
    print(f"\n📊 Total: {loc} lines of Python code")
    print(f"📦 Package size: {len(package):,} characters")

if __name__ == "__main__":
    main()
