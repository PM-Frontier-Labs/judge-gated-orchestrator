#!/usr/bin/env python3
"""
Path Utilities: Simple path operations to reduce duplication.
"""

from pathlib import Path
from typing import Union

def get_relative_path(file_path: Union[str, Path], base_path: Union[str, Path]) -> str:
    """Get relative path with safe fallback."""
    try:
        return str(Path(file_path).relative_to(Path(base_path)))
    except ValueError:
        return str(file_path)

def ensure_dir(path: Union[str, Path]) -> Path:
    """Ensure directory exists and return Path object."""
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj
