#!/usr/bin/env python3
"""
LLM Pipeline: Critic → Verifier → Arbiter
Implements the LLM judge pipeline that proposes amendments.
"""

import os
import json
from typing import List, Dict, Any, Optional

def review_phase_with_llm(phase: Dict[str, Any], changed_files: List[str], 
                         test_output: str, lint_output: str) -> Dict[str, Any]:
    """Run complete LLM pipeline"""
    # Step 1: Critic analyzes
    critic_output = _critic_analyze(phase, changed_files, test_output, lint_output)
    
    # Step 2: Verifier checks evidence
    verified_output = _verifier_check(critic_output, changed_files, test_output)
    
    # Step 3: Arbiter makes final decision
    final_output = _arbiter_decide(verified_output, phase)
    
    return final_output

def _critic_analyze(phase: Dict[str, Any], changed_files: List[str], 
                   test_output: str, lint_output: str) -> Dict[str, Any]:
    """Critic analyzes code and suggests must-fix items and amendments"""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        # Deterministic no-op when not configured
        return {"must_fix": [], "proposed_amendments": []}
    
    try:
        from anthropic import Anthropic
        client = Anthropic(api_key=api_key)
        
        prompt = f"""
You are a code critic analyzing a phase implementation.

Phase: {phase.get('id', 'unknown')}
Objective: {phase.get('description', 'unknown')}

Changed Files: {', '.join(changed_files)}
Test Output: {test_output}
Lint Output: {lint_output}

Analyze the code and identify:
1. Must-fix items (critical issues that block progression)
2. Proposed amendments (specific fixes that can be applied)

For amendments, suggest specific types:
- set_test_cmd: "python -m pytest -q" (fix test command)
- add_scope: ["tests/**"] (add files to scope)
- note_baseline_shift: "new_sha" (update baseline)

Respond in JSON format:
{{
  "must_fix": ["issue1", "issue2"],
  "proposed_amendments": [
    {{"type": "set_test_cmd", "value": "python -m pytest -q", "reason": "fix test command"}}
  ]
}}
"""
        
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        
        try:
            return json.loads(response.content[0].text)
        except Exception:
            # Guard against unexpected model output
            return {"must_fix": [], "proposed_amendments": []}
        
    except Exception as e:
        print(f"⚠️ LLM critic failed: {e}")
        return {"must_fix": [], "proposed_amendments": []}

def _verifier_check(critic_output: Dict[str, Any], changed_files: List[str], test_output: str) -> Dict[str, Any]:
    """Verifier rejects claims without evidence"""
    verified = {
        "must_fix": [],
        "proposed_amendments": []
    }
    
    # Verify must-fix items have evidence
    for item in critic_output.get("must_fix", []):
        if _has_evidence(item, test_output, changed_files):
            verified["must_fix"].append(item)
    
    # Verify proposed amendments have evidence
    for amendment in critic_output.get("proposed_amendments", []):
        if _has_amendment_evidence(amendment, test_output):
            verified["proposed_amendments"].append(amendment)
    
    return verified

def _arbiter_decide(verified_output: Dict[str, Any], phase: Dict[str, Any]) -> Dict[str, Any]:
    """Arbiter outputs score and pass boolean"""
    must_fix_count = len(verified_output.get("must_fix", []))
    
    # Calculate score (0.0 to 1.0)
    if must_fix_count == 0:
        score = 1.0
    else:
        score = max(0.0, 1.0 - (must_fix_count * 0.3))
    
    # Determine pass/fail
    pass_phase = must_fix_count == 0
    
    return {
        "score": score,
        "pass": pass_phase,
        "must_fix": verified_output.get("must_fix", []),
        "proposed_amendments": verified_output.get("proposed_amendments", [])
    }

def _has_evidence(item: str, test_output: str, changed_files: List[str]) -> bool:
    """Check if item has supporting evidence"""
    return any(keyword in test_output.lower() for keyword in 
             ["error", "failed", "exception", "traceback"])

def _has_amendment_evidence(amendment: Dict[str, Any], test_output: str) -> bool:
    """Check if amendment has supporting evidence"""
    amendment_type = amendment.get("type", "")
    
    if amendment_type == "set_test_cmd":
        return "usage:" in test_output.lower() or "command not found" in test_output.lower()
    
    return True  # Default to allowing
