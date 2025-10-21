#!/usr/bin/env python3
"""
LLM Configuration: Centralized configuration for all LLM operations.
Provides single source of truth for model defaults, pricing, and API handling.
"""

from typing import Dict, Any, Optional

# Default model configuration
DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MAX_TOKENS = 2000
DEFAULT_TEMPERATURE = 0
DEFAULT_TIMEOUT = 60.0

# Pricing constants (as of 2025-01-15)
# Claude Sonnet 4: $3.00 per 1M input tokens, $15.00 per 1M output tokens
PRICING = {
    "input_per_1k": 0.003,   # $3.00 per 1M tokens = $0.003 per 1K tokens
    "output_per_1k": 0.015,  # $15.00 per 1M tokens = $0.015 per 1K tokens
}

def get_llm_config(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Get LLM configuration from plan, with defaults."""
    llm_config = plan.get("plan", {}).get("llm_review_config", {})
    
    return {
        "model": llm_config.get("model", DEFAULT_MODEL),
        "max_tokens": llm_config.get("max_tokens", DEFAULT_MAX_TOKENS),
        "temperature": llm_config.get("temperature", DEFAULT_TEMPERATURE),
        "timeout_seconds": llm_config.get("timeout_seconds", DEFAULT_TIMEOUT),
        "budget_usd": llm_config.get("budget_usd", 2.0),
        "fail_on_transport_error": llm_config.get("fail_on_transport_error", False),
        "llm_review_scope": llm_config.get("llm_review_scope", "scope"),
        "include_extensions": llm_config.get("include_extensions", [".py", ".tsx", ".ts", ".md"]),
        "exclude_patterns": llm_config.get("exclude_patterns", [
            "tests/**",
            "**/__pycache__/**",
            "runs/**",
            ".repo/**"
        ])
    }

def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate cost for given token usage."""
    return (
        input_tokens / 1000 * PRICING["input_per_1k"] +
        output_tokens / 1000 * PRICING["output_per_1k"]
    )

def format_cost_message(cost: float, input_tokens: int, output_tokens: int) -> str:
    """Format cost information for display."""
    return f"💰 LLM review cost: ${cost:.4f} (input: {input_tokens} tokens, output: {output_tokens} tokens)"

def get_api_client(api_key: Optional[str] = None):
    """Get configured Anthropic API client."""
    import os
    from anthropic import Anthropic
    
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set")
    
    return Anthropic(api_key=api_key)
