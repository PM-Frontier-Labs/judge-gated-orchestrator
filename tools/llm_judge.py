#!/usr/bin/env python3
"""
LLM-based semantic code review for judge system.

Uses git diff to find actually changed files, then reviews them with Claude.
"""

import os
from typing import List, Dict, Any, Tuple
from pathlib import Path

# Import shared utilities
from lib.git_ops import get_changed_files as get_changed_files_raw
from lib.llm_config import get_llm_config, get_api_client, calculate_cost, format_cost_message


def _filter_code_files(
    changed_files: List[Path],
    include_extensions: List[str],
    exclude_patterns: List[str],
    repo_root: Path
) -> List[Path]:
    """Filter files by extension and exclusion patterns."""
    code_files = []
    for f in changed_files:
        # Check extension match
        if f.suffix not in include_extensions:
            continue
        
        # Check exclusion patterns
        relative_path = str(f.relative_to(repo_root))
        excluded = False
        for pattern in exclude_patterns:
            import fnmatch
            if fnmatch.fnmatch(relative_path, pattern):
                excluded = True
                break
        
        if not excluded:
            code_files.append(f)
    
    return code_files


def _build_code_context(
    code_files: List[Path],
    repo_root: Path,
    baseline_sha: str = None,
    max_file_size: int = 50 * 1024,
    max_total_size: int = 200 * 1024
) -> Tuple[str, int, int]:
    """
    Build code context from files with size limits.
    
    Returns: (context_string, files_included, files_skipped)
    """
    code_context = ""
    total_size = 0
    files_included = 0
    files_skipped = 0
    
    for file_path in code_files:
        try:
            file_size = file_path.stat().st_size
            
            # Skip files that are too large
            if file_size > max_file_size:
                files_skipped += 1
                code_context += f"\n{'='*60}\n"
                code_context += f"# File: {file_path.relative_to(repo_root)} [SKIPPED - {file_size//1024}KB exceeds {max_file_size//1024}KB limit]\n"
                code_context += f"# Consider using: git diff {baseline_sha or 'HEAD'} -- {file_path.relative_to(repo_root)}\n"
                code_context += f"{'='*60}\n\n"
                continue
            
            # Check total context size
            if total_size + file_size > max_total_size:
                files_skipped += 1
                code_context += f"\n[... {len(code_files) - files_included} more files skipped due to total context size limit ...]\n"
                break
            
            # Read file content
            code_context += f"\n{'='*60}\n"
            code_context += f"# File: {file_path.relative_to(repo_root)} ({file_size//1024}KB)\n"
            code_context += f"{'='*60}\n"
            file_content = file_path.read_text()
            code_context += file_content
            code_context += "\n"
            
            total_size += file_size
            files_included += 1
        
        except Exception:
            # Silently skip files that can't be read
            continue
    
    return code_context, files_included, files_skipped


def _call_claude_for_review(
    code_context: str,
    phase_description: str,
    model: str,
    max_tokens: int,
    temperature: float,
    timeout_seconds: int
) -> Tuple[str, Dict[str, int]]:
    """
    Call Claude API for code review.
    
    Returns: (review_text, usage_dict)
    """
    from anthropic import Anthropic
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    client = Anthropic(api_key=api_key)
    
    prompt = f"""You are a senior code reviewer. Review this code for phase: "{phase_description}"

Changed files:
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
    
    response = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        timeout=timeout_seconds,
        messages=[{"role": "user", "content": prompt}]
    )
    
    review_text = response.content[0].text.strip()
    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens
    }
    
    return review_text, usage


def _parse_review_response(review_text: str, budget_usd: float = None, usage: Dict[str, int] = None) -> List[str]:
    """Parse Claude's review response into issues list."""
    issues = []
    
    # Check budget if configured
    if budget_usd is not None and usage:
        estimated_cost = calculate_cost(usage["input_tokens"], usage["output_tokens"])
        print(format_cost_message(estimated_cost, usage["input_tokens"], usage["output_tokens"]))
        
        if estimated_cost > budget_usd:
            issues.append(f"LLM review cost ${estimated_cost:.4f} exceeds budget ${budget_usd:.2f}")
            return issues
    
    # Check for approval
    if "APPROVED" in review_text.upper() or "LGTM" in review_text.upper():
        return []
    
    # Extract issues
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
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return ["LLM review enabled but ANTHROPIC_API_KEY not set in environment"]
    except Exception:
        return ["LLM review enabled but ANTHROPIC_API_KEY not set in environment"]
    
    # Check anthropic package
    try:
        from anthropic import Anthropic
    except ImportError:
        return ["LLM review enabled but anthropic package not installed. Run: pip install anthropic"]
    
    # Get LLM configuration from plan (with defaults)
    if plan:
        llm_config = get_llm_config(plan)
        base_branch = plan.get("plan", {}).get("base_branch", "main")
    else:
        llm_config = get_llm_config({})  # Use defaults
        base_branch = "main"
    
    # Extract config with defaults
    model = llm_config["model"]
    max_tokens = llm_config["max_tokens"]
    temperature = llm_config["temperature"]
    timeout_seconds = llm_config["timeout_seconds"]
    budget_usd = llm_config["budget_usd"]
    fail_on_transport_error = llm_config["fail_on_transport_error"]
    include_extensions = llm_config["include_extensions"]
    exclude_patterns = llm_config["exclude_patterns"]
    
    # Get changed files (committed + uncommitted)
    changed_file_strs, warnings = get_changed_files_raw(
        repo_root,
        include_committed=True,
        base_branch=base_branch,
        baseline_sha=baseline_sha
    )
    
    # Display warnings if any
    for warning in warnings:
        print(f"  ⚠️  {warning}")
    
    # Convert to Path objects and filter to existing files
    changed_files = []
    for file_str in changed_file_strs:
        file_path = repo_root / file_str
        if file_path.exists() and file_path.is_file():
            changed_files.append(file_path)
    
    if not changed_files:
        return []  # No changes detected
    
    # Filter files by extension and exclusion patterns
    code_files = _filter_code_files(changed_files, include_extensions, exclude_patterns, repo_root)
    
    if not code_files:
        return []  # No matching files
    
    # Build code context with size limits
    code_context, files_included, files_skipped = _build_code_context(
        code_files,
        repo_root,
        baseline_sha
    )
    
    if not code_context or files_included == 0:
        if files_skipped > 0:
            return [f"LLM review skipped: All {files_skipped} changed files exceed size limits. Use manual review."]
        return []
    
    # Call Claude for review
    try:
        review_text, usage = _call_claude_for_review(
            code_context,
            phase.get("description", "unknown"),
            model,
            max_tokens,
            temperature,
            timeout_seconds
        )
        
        # Parse response
        return _parse_review_response(review_text, budget_usd, usage)
    
    except Exception as e:
        if fail_on_transport_error:
            return [f"LLM review failed: {str(e)}"]
        else:
            print(f"⚠️  LLM review skipped due to error: {e}")
            return []  # Don't block on transport errors if configured
