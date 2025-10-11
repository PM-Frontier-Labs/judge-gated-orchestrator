#!/usr/bin/env python3
"""
LLM-based semantic code review for judge system.

This module adds Claude as a code reviewer to check:
- Architecture and design patterns
- Code clarity and naming
- Complexity and maintainability
- Edge case handling
- Documentation quality
"""

import os
from typing import List, Dict, Any
from pathlib import Path


def llm_code_review(phase: Dict[str, Any], changed_files: List[Path]) -> List[str]:
    """
    Use Claude to review code quality semantically.

    Args:
        phase: Phase configuration from plan.yaml
        changed_files: List of files that were changed in this phase

    Returns:
        List of issues found (empty if approved)
    """
    # Check if LLM review is enabled for this phase
    llm_gate = phase.get("gates", {}).get("llm_review", {})
    if not llm_gate.get("enabled", False):
        return []  # Skip if not enabled

    # Require API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ["LLM review enabled but ANTHROPIC_API_KEY not set in environment"]

    try:
        from anthropic import Anthropic
    except ImportError:
        return ["LLM review enabled but anthropic package not installed. Run: pip install anthropic"]

    client = Anthropic(api_key=api_key)
    issues = []

    # Gather code to review
    code_context = ""
    file_count = 0
    for file_path in changed_files:
        # Only review Python files for now
        if file_path.suffix == ".py" and file_path.exists():
            code_context += f"\n{'='*60}\n"
            code_context += f"# File: {file_path}\n"
            code_context += f"{'='*60}\n"
            code_context += file_path.read_text()
            code_context += "\n"
            file_count += 1

    if not code_context:
        return []  # No code to review

    # Build review prompt
    prompt = f"""You are a senior code reviewer. Review this code for phase: "{phase['description']}"

{file_count} file(s) to review:
{code_context}

Review criteria:
1. **Architecture**: Does it follow good design patterns? Is it well-structured?
2. **Naming**: Are variable/function names clear and consistent?
3. **Complexity**: Is the code simple and maintainable? Any overly complex logic?
4. **Documentation**: Are complex parts explained? Are docstrings adequate?
5. **Edge cases**: Are errors handled properly? Are edge cases covered?
6. **Type safety**: Are type hints used appropriately?
7. **Best practices**: Does it follow Python best practices?

Instructions:
- If you find issues, list each one starting with "- Issue:"
- Be specific: reference function names, line numbers if possible
- Focus on meaningful problems, not nitpicks
- If the code is good quality, respond with exactly: "APPROVED - Code meets quality standards"

Format your response as:
- Issue: [specific issue description]
- Issue: [another specific issue]

OR if approved:
APPROVED - Code meets quality standards
"""

    # Call Claude
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )

        review_text = response.content[0].text.strip()

        # Parse response
        if "APPROVED" in review_text.upper():
            return []  # No issues - approved!

        # Extract issues
        lines = review_text.split("\n")
        for line in lines:
            line = line.strip()
            if line.startswith("- Issue:"):
                issue_text = line.replace("- Issue:", "").strip()
                issues.append(f"Code quality: {issue_text}")
            elif line.startswith("-") and ":" in line:
                # Handle variations like "- Architecture: ..."
                issue_text = line[1:].strip()
                issues.append(f"Code quality: {issue_text}")

        # If we couldn't parse issues but it's not approved, add generic message
        if not issues and review_text:
            issues.append(f"Code quality: {review_text[:200]}")

    except Exception as e:
        issues.append(f"LLM review failed: {str(e)}")

    return issues


def get_changed_files_in_scope(phase: Dict[str, Any], repo_root: Path) -> List[Path]:
    """
    Get list of files in the phase scope.

    For MVP, this returns all files in the scope patterns.
    In production, you'd use `git diff` to find actually changed files.

    Args:
        phase: Phase configuration
        repo_root: Repository root path

    Returns:
        List of file paths to review
    """
    scope = phase.get("scope", {})
    include_patterns = scope.get("include", [])

    changed_files = []

    for pattern in include_patterns:
        # Simple glob matching (for MVP)
        # Remove wildcards for basic matching
        if "**" in pattern:
            # Handle patterns like "src/mvp/**"
            base_pattern = pattern.replace("**", "*")
            for file_path in repo_root.glob(base_pattern):
                if file_path.is_file():
                    changed_files.append(file_path)
        else:
            # Handle specific files or simple globs
            for file_path in repo_root.glob(pattern):
                if file_path.is_file():
                    changed_files.append(file_path)

    return changed_files
