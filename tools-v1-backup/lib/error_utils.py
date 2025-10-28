#!/usr/bin/env python3
"""
Error Utilities: Simple, consistent error handling.
"""

import logging
from typing import List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class ProtocolError(Exception):
    """Base exception for protocol errors."""
    pass

class ConfigurationError(ProtocolError):
    """Configuration-related errors."""
    pass

class ValidationError(ProtocolError):
    """Validation-related errors."""
    pass

class ExecutionError(ProtocolError):
    """Execution-related errors."""
    pass

def log_error(message: str, error_type: str = "ERROR"):
    """Log error message consistently."""
    logging.error(f"{error_type}: {message}")

def log_warning(message: str):
    """Log warning message consistently."""
    logging.warning(f"WARNING: {message}")

def log_info(message: str):
    """Log info message consistently."""
    logging.info(f"INFO: {message}")

def format_error_with_suggestions(error: str, suggestions: List[str]) -> str:
    """Format error with actionable suggestions."""
    formatted = f"❌ {error}\n"
    if suggestions:
        formatted += "\n💡 Suggestions:\n"
        for suggestion in suggestions:
            formatted += f"   - {suggestion}\n"
    return formatted
