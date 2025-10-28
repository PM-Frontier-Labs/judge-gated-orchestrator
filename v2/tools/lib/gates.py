#!/usr/bin/env python3
"""
Core gate implementations for v2.

Gates are simple functions that return list of issues (empty = pass).
No complex orchestration, no state management, just pure checks.
"""

import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional


class GateError(Exception):
    """Gate execution error."""
    pass


def check_artifacts(phase: Dict[str, Any], repo_root: Path) -> List[str]:
    """
    Check that required artifacts exist and are non-empty.
    
    Supports two schemas:
    1. artifacts: {must_exist: [...]}  (v1 format)
    2. artifacts: [...]                (simple list)
    """
    issues = []
    
    artifacts_config = phase.get("artifacts", {})
    
    # Handle both schemas
    if isinstance(artifacts_config, dict):
        artifacts = artifacts_config.get("must_exist", [])
    elif isinstance(artifacts_config, list):
        artifacts = artifacts_config
    else:
        return []  # No artifacts specified
    
    for artifact in artifacts:
        path = repo_root / artifact
        
        if not path.exists():
            issues.append(f"Missing required artifact: {artifact}")
        elif path.is_file() and path.stat().st_size == 0:
            issues.append(f"Artifact is empty: {artifact}")
    
    return issues


def check_tests(phase: Dict[str, Any], repo_root: Path, traces_dir: Path) -> List[str]:
    """
    Check test execution results.
    
    Supports two modes:
    1. Simple: tests: {must_pass: true}
    2. Split: tests: {unit: {...}, integration: {...}}
    """
    issues = []
    
    tests_config = phase.get("gates", {}).get("tests", {})
    
    if not tests_config:
        return []  # Tests not required
    
    # Check if split mode (unit/integration)
    if "unit" in tests_config or "integration" in tests_config:
        # Split mode
        if "unit" in tests_config:
            unit_issues = _check_test_trace("tests_unit", traces_dir, "Unit tests")
            issues.extend(unit_issues)
        
        if "integration" in tests_config:
            integ_config = tests_config["integration"]
            allow_skip = integ_config.get("allow_skip", False)
            
            integ_issues = _check_test_trace("tests_integration", traces_dir, "Integration tests")
            
            if integ_issues and not allow_skip:
                issues.extend(integ_issues)
            elif integ_issues and allow_skip:
                # Just warn, don't fail
                print(f"  ⚠️  Integration tests failed (skippable): {integ_issues[0]}")
    else:
        # Simple mode
        if tests_config.get("must_pass", False):
            test_issues = _check_test_trace("tests", traces_dir, "Tests")
            issues.extend(test_issues)
    
    return issues


def _check_test_trace(trace_name: str, traces_dir: Path, label: str) -> List[str]:
    """Check a test trace file for pass/fail."""
    trace_file = traces_dir / f"last_{trace_name}.txt"
    
    if not trace_file.exists():
        return [f"{label} have not been run yet"]
    
    content = trace_file.read_text()
    
    # Extract exit code
    for line in content.split("\n"):
        if line.startswith("Exit code:"):
            try:
                exit_code = int(line.split(":", 1)[1].strip())
                
                if exit_code == 0:
                    return []  # Pass
                else:
                    return [f"{label} failed with exit code {exit_code}. See {trace_file.relative_to(traces_dir.parent.parent)}"]
            except (ValueError, IndexError):
                pass
    
    return [f"Could not parse {label} results from trace"]


def check_lint(phase: Dict[str, Any], repo_root: Path, traces_dir: Path) -> List[str]:
    """Check linting results."""
    lint_config = phase.get("gates", {}).get("lint", {})
    
    if not lint_config.get("must_pass", False):
        return []  # Lint not required
    
    trace_file = traces_dir / "last_lint.txt"
    
    if not trace_file.exists():
        return ["Linting has not been run yet"]
    
    content = trace_file.read_text()
    
    # Extract exit code
    for line in content.split("\n"):
        if line.startswith("Exit code:"):
            try:
                exit_code = int(line.split(":", 1)[1].strip())
                
                if exit_code == 0:
                    return []  # Pass
                else:
                    return [f"Linting failed with exit code {exit_code}. See {trace_file.relative_to(repo_root)}"]
            except (ValueError, IndexError):
                pass
    
    return ["Could not parse linting results from trace"]


def check_docs(phase: Dict[str, Any], changed_files: List[str], repo_root: Path) -> List[str]:
    """
    Check that required documentation was updated.
    
    Verifies:
    1. Doc files exist
    2. Doc files are non-empty
    3. Doc files were actually changed in this phase
    """
    issues = []
    
    docs_config = phase.get("gates", {}).get("docs", {})
    must_update = docs_config.get("must_update", [])
    
    if not must_update:
        return []  # No docs required
    
    if not changed_files:
        issues.append(
            "Documentation gate: No changed files detected.\n"
            "  This usually means changes are not committed yet."
        )
        return issues
    
    for doc_path in must_update:
        # Handle section anchors like "docs/api.md#authentication"
        doc_file = doc_path.split("#")[0]
        path = repo_root / doc_file
        
        # Check existence
        if not path.exists():
            issues.append(f"Documentation not found: {doc_file}")
            continue
        
        # Check non-empty
        if path.is_file() and path.stat().st_size == 0:
            issues.append(f"Documentation is empty: {doc_file}")
            continue
        
        # Check if actually changed
        doc_was_changed = (
            doc_file in changed_files or
            any(f.startswith(doc_file) for f in changed_files)
        )
        
        if not doc_was_changed:
            issues.append(
                f"Documentation not updated: {doc_file}\n"
                f"  This file must be modified as part of {phase['id']}"
            )
    
    return issues


def check_scope(
    phase: Dict[str, Any],
    changed_files: List[str],
    repo_root: Path,
    baseline_sha: Optional[str]
) -> List[str]:
    """
    Check for scope drift with justification workflow.
    
    New approach:
    - Detect out-of-scope changes
    - If justification exists, record for audit and pass
    - If no justification, prompt for one
    """
    from .state import has_scope_justification
    from .scope import classify_files
    
    issues = []
    
    drift_config = phase.get("gates", {}).get("drift")
    
    if not drift_config:
        return []  # Scope checking not enabled
    
    if not changed_files:
        return []  # No changes to check
    
    # Get scope patterns
    scope_config = phase.get("scope", {})
    include_patterns = scope_config.get("include", [])
    exclude_patterns = scope_config.get("exclude", [])
    
    if not include_patterns:
        return []  # No scope defined
    
    # Classify files
    in_scope, out_of_scope = classify_files(changed_files, include_patterns, exclude_patterns)
    
    if not out_of_scope:
        return []  # All changes in scope
    
    # Check if justification exists
    phase_id = phase.get("id", "unknown")
    
    if has_scope_justification(phase_id, repo_root):
        # Justification provided - record for audit but pass
        print(f"  ⚠️  OUT OF SCOPE: {len(out_of_scope)} files (justified - see .repo/scope_audit/{phase_id}.md)")
        for f in out_of_scope[:5]:
            print(f"      - {f}")
        if len(out_of_scope) > 5:
            print(f"      ... and {len(out_of_scope) - 5} more")
        return []  # Pass
    
    # No justification - request one
    issues.append("OUT OF SCOPE CHANGES DETECTED")
    issues.append("")
    issues.append(f"Files modified outside phase scope ({len(out_of_scope)}):")
    for f in out_of_scope[:10]:
        issues.append(f"  - {f}")
    if len(out_of_scope) > 10:
        issues.append(f"  ... and {len(out_of_scope) - 10} more")
    
    issues.append("")
    issues.append("🤔 Please justify these changes:")
    issues.append(f"   ./v2/tools/phasectl.py justify-scope {phase_id}")
    issues.append("")
    issues.append("The LLM will explain why these changes were necessary.")
    issues.append("Justification will be recorded for human review.")
    
    return issues


def check_llm_review(
    phase: Dict[str, Any],
    plan: Dict[str, Any],
    changed_files: List[str],
    repo_root: Path,
    baseline_sha: Optional[str]
) -> List[str]:
    """
    LLM-based semantic code review.
    
    Uses Claude to review changed code for:
    - Architecture issues
    - Code quality problems  
    - Security concerns
    - Goal alignment
    """
    llm_config = phase.get("gates", {}).get("llm_review", {})
    
    if not llm_config.get("enabled", False):
        return []  # LLM review not enabled
    
    # Check for API key
    import os
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ["LLM review enabled but ANTHROPIC_API_KEY not set"]
    
    # Filter to code files only
    code_extensions = [".py", ".ts", ".tsx", ".js", ".jsx"]
    code_files = [f for f in changed_files if any(f.endswith(ext) for ext in code_extensions)]
    
    if not code_files:
        return []  # No code files to review
    
    # Limit to reasonable size
    MAX_FILES = 10
    if len(code_files) > MAX_FILES:
        code_files = code_files[:MAX_FILES]
        print(f"  ℹ️  LLM review limited to first {MAX_FILES} files")
    
    # Build context from changed files
    context = _build_review_context(code_files, repo_root, baseline_sha)
    
    if not context:
        return []  # No readable files
    
    # Call Claude for review
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        phase_goal = phase.get("description", "No description provided")
        
        prompt = f"""You are reviewing code changes for this phase goal:

**Goal:** {phase_goal}

**Changed files:**
{context}

Review the code against the goal. Check for:
1. Does the code accomplish the stated goal?
2. Are there any obvious bugs or issues?
3. Is the code reasonably clean and maintainable?
4. Any security concerns?

If the code looks good, respond: "APPROVED - Code meets standards"
If there are issues, list each as "- Issue: [specific problem]"

Focus on meaningful problems, not nitpicks.
"""
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0,
            timeout=60.0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        review_text = response.content[0].text.strip()
        
        # Parse response
        if "APPROVED" in review_text.upper():
            return []  # Pass
        
        # Extract issues
        issues = []
        for line in review_text.split("\n"):
            line = line.strip()
            if line.startswith("- Issue:"):
                issue = line.replace("- Issue:", "").strip()
                issues.append(f"LLM review: {issue}")
        
        if not issues:
            # LLM provided feedback but no clear issues format
            issues.append(f"LLM review feedback:\n{review_text}")
        
        return issues
        
    except Exception as e:
        # Don't block on LLM errors
        print(f"  ⚠️  LLM review error (non-blocking): {e}")
        return []


def _build_review_context(file_paths: List[str], repo_root: Path, baseline_sha: Optional[str]) -> str:
    """Build context string from changed files."""
    context = ""
    
    for file_path in file_paths:
        path = repo_root / file_path
        
        if not path.exists() or not path.is_file():
            continue
        
        try:
            size = path.stat().st_size
            
            # Skip very large files
            if size > 50_000:  # 50KB limit
                context += f"\n[{file_path}: Skipped - {size//1024}KB exceeds limit]\n"
                continue
            
            content = path.read_text()
            context += f"\n{'='*60}\n"
            context += f"File: {file_path}\n"
            context += f"{'='*60}\n"
            context += content
            context += "\n"
            
        except Exception:
            continue
    
    return context


def check_orient_acknowledgment(phase: Dict[str, Any], repo_root: Path) -> List[str]:
    """
    Check if agent has acknowledged orient.sh.
    
    This forces agent to read context before advancing to next phase.
    """
    from .state import is_orient_acknowledged
    
    phase_id = phase.get("id", "unknown")
    
    if is_orient_acknowledged(phase_id, repo_root):
        return []  # Pass
    
    return [
        "ORIENT ACKNOWLEDGMENT REQUIRED",
        "",
        "Before completing this phase, you must:",
        "1. Run: ./orient.sh",
        "2. Read and understand the current state",
        "3. Acknowledge: ./v2/tools/phasectl.py acknowledge-orient",
        "",
        "This ensures you maintain full context between phases."
    ]
