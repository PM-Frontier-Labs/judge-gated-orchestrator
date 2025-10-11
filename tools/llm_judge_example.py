#!/usr/bin/env python3
"""
Example: LLM-based semantic code review (optional enhancement)

This shows how to add Claude as a code reviewer to the judge.
"""

import os
from typing import List, Dict, Any
from pathlib import Path
from anthropic import Anthropic


def llm_code_review(phase: Dict[str, Any], changed_files: List[Path]) -> List[str]:
    """
    Use Claude to review code quality semantically.

    This is OPTIONAL - the rule-based judge works fine without it.
    But adding this gives you architecture/style/pattern review.
    """
    # Check if LLM review is enabled for this phase
    llm_gate = phase.get("gates", {}).get("llm_review", {})
    if not llm_gate.get("enabled", False):
        return []  # Skip if not enabled

    # Require API key
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        return ["LLM review enabled but ANTHROPIC_API_KEY not set"]

    client = Anthropic(api_key=api_key)
    issues = []

    # Gather code to review
    code_context = ""
    for file_path in changed_files:
        if file_path.suffix == ".py":
            code_context += f"\n# {file_path}\n"
            code_context += file_path.read_text()

    if not code_context:
        return []  # No code to review

    # Build review prompt
    prompt = f"""Review this code for a phase: {phase['description']}

Code to review:
{code_context}

Check for:
1. Architecture: Does it follow good patterns?
2. Naming: Are names clear and consistent?
3. Complexity: Is it simple and maintainable?
4. Documentation: Are complex parts explained?
5. Edge cases: Are errors handled?

If you find issues, list them as:
- Issue description

If code looks good, respond with: "APPROVED"
"""

    # Call Claude
    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )

        review_text = response.content[0].text

        # Parse response
        if "APPROVED" in review_text.upper():
            return []  # No issues
        else:
            # Extract issues (simple parsing - could be more sophisticated)
            lines = review_text.split("\n")
            for line in lines:
                if line.strip().startswith("-"):
                    issues.append(f"LLM Review: {line.strip()[1:].strip()}")

    except Exception as e:
        issues.append(f"LLM review failed: {str(e)}")

    return issues


# Example integration into judge.py:
#
# In judge_phase() function, add:
#
# print("  🔍 Running LLM code review...")
# all_issues.extend(llm_code_review(phase, changed_files))
