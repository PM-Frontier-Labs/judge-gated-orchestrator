#!/usr/bin/env python3
"""
LLM-based semantic code review for judge system.

Uses git diff to find actually changed files, then reviews them with Claude.
"""

import os
from typing import List, Dict, Any
from pathlib import Path

# Import shared utilities
from lib.git_ops import get_changed_files as get_changed_files_raw


def llm_code_review(phase: Dict[str, Any], repo_root: Path, plan: Dict[str, Any] = None, baseline_sha: str = None) -> List[str]:
    """
    Use Claude to review code quality semantically.

    Reviews all files changed in this phase (committed + uncommitted).
    Uses same change basis as other gates for consistency.
    """
    # Check if LLM review is enabled
    llm_gate = phase.get("gates", {}).get("llm_review", {})
    if not llm_gate.get("enabled", False):
        return []

    # Check API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ["LLM review enabled but ANTHROPIC_API_KEY not set in environment"]

    # Check anthropic package
    try:
        from anthropic import Anthropic
    except ImportError:
        return ["LLM review enabled but anthropic package not installed. Run: pip install anthropic"]

    # Get LLM configuration from plan (with defaults)
    llm_config = {}
    if plan:
        llm_config = plan.get("plan", {}).get("llm_review_config", {})
        base_branch = plan.get("plan", {}).get("base_branch", "main")
    else:
        base_branch = "main"

    # Extract config with defaults
    model = llm_config.get("model", "claude-sonnet-4-20250514")
    max_tokens = llm_config.get("max_tokens", 2000)
    temperature = llm_config.get("temperature", 0)
    timeout_seconds = llm_config.get("timeout_seconds", 60)
    # budget_usd = llm_config.get("budget_usd")  # Reserved for future cost tracking
    fail_on_error = llm_config.get("fail_on_transport_error", False)
    include_extensions = llm_config.get("include_extensions", [".py"])
    exclude_patterns = llm_config.get("exclude_patterns", [])

    # Get changed files (committed + uncommitted, same as other gates)
    changed_file_strs = get_changed_files_raw(
        repo_root,
        include_committed=True,  # FIXED: Include committed changes
        base_branch=base_branch,
        baseline_sha=baseline_sha  # NEW: Use same baseline as other gates
    )

    # Convert to Path objects and filter to existing files
    changed_files = []
    for file_str in changed_file_strs:
        file_path = repo_root / file_str
        if file_path.exists() and file_path.is_file():
            changed_files.append(file_path)

    if not changed_files:
        # No changes detected - approve
        return []

    # Filter files by configured extensions
    code_files = []
    for f in changed_files:
        # Check if extension matches
        if f.suffix in include_extensions:
            # Check if not excluded by patterns
            relative_path = str(f.relative_to(repo_root))
            excluded = False
            for pattern in exclude_patterns:
                import fnmatch
                if fnmatch.fnmatch(relative_path, pattern):
                    excluded = True
                    break
            if not excluded:
                code_files.append(f)

    if not code_files:
        # No matching files changed - approve
        return []

    # Build code context
    code_context = ""
    for file_path in code_files:
        try:
            code_context += f"\n{'='*60}\n"
            code_context += f"# File: {file_path.relative_to(repo_root)}\n"
            code_context += f"{'='*60}\n"
            code_context += file_path.read_text()
            code_context += "\n"
        except Exception:
            continue

    if not code_context:
        return []

    # Call Claude for review
    client = Anthropic(api_key=api_key)

    prompt = f"""You are a senior code reviewer. Review this code for phase: "{phase.get('description', 'unknown')}"

Changed files ({len(code_files)}):
{code_context}

Review criteria:
1. Architecture: Good design patterns? Well-structured?
2. Naming: Clear and consistent variable/function names?
3. Complexity: Simple and maintainable? Any overly complex logic?
4. Documentation: Complex parts explained? Adequate docstrings?
5. Edge cases: Errors handled properly? Edge cases covered?

Instructions:
- If you find issues, list each as "- Issue: [description]"
- Be specific: reference function names
- Focus on meaningful problems, not nitpicks
- If code is good quality, respond: "APPROVED - Code meets quality standards"
"""

    try:
        # Use configured model and parameters
        response = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout_seconds,
            messages=[{"role": "user", "content": prompt}]
        )

        review_text = response.content[0].text.strip()

        # Parse response (look for APPROVED or LGTM)
        if "APPROVED" in review_text.upper() or "LGTM" in review_text.upper():
            return []

        # Extract issues
        issues = []
        for line in review_text.split("\n"):
            line = line.strip()
            if line.startswith("- Issue:"):
                issue = line.replace("- Issue:", "").strip()
                issues.append(f"Code quality: {issue}")
            elif line.startswith("-") and len(line) > 2:
                # Handle variations
                issue = line[1:].strip()
                if issue:
                    issues.append(f"Code quality: {issue}")

        return issues

    except Exception as e:
        if fail_on_error:
            return [f"LLM review failed: {str(e)}"]
        else:
            print(f"⚠️  LLM review skipped due to error: {e}")
            return []  # Don't block on transport errors if configured
