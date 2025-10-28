#!/usr/bin/env python3
"""
File Locking Utilities: Centralized file locking for concurrent access safety.
Provides consistent file locking and atomic writes across all protocol operations.
"""

import fcntl
import os
import tempfile
import json
from pathlib import Path
from typing import Generator, ContextManager, Any, Dict
from contextlib import contextmanager

@contextmanager
def acquire_file_lock(file_path: Path, mode: str = "exclusive", timeout: int = None) -> Generator[None, None, None]:
    """
    Acquire a file lock for safe concurrent access.
    
    Args:
        file_path: Path to the file to lock
        mode: Lock mode - "exclusive" (default) or "shared"
        timeout: Maximum time to wait for lock (seconds). None = no timeout
    
    Yields:
        None - Lock is held during context
        
    Raises:
        OSError: If lock cannot be acquired
        TimeoutError: If timeout is exceeded
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Open file for locking (create if doesn't exist)
    lock_file = open(file_path, 'a+')
    
    try:
        # Acquire lock with optional timeout
        if timeout is None:
            # No timeout - blocking lock
            if mode == "exclusive":
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            elif mode == "shared":
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
            else:
                raise ValueError(f"Invalid lock mode: {mode}")
        else:
            # Timeout - non-blocking with retry loop
            import time
            start_time = time.time()
            lock_flags = fcntl.LOCK_EX if mode == "exclusive" else fcntl.LOCK_SH
            
            while True:
                try:
                    fcntl.flock(lock_file.fileno(), lock_flags | fcntl.LOCK_NB)
                    break  # Lock acquired successfully
                except OSError:
                    # Lock not available, check timeout
                    if time.time() - start_time >= timeout:
                        raise TimeoutError(f"Could not acquire lock on {file_path} within {timeout}s")
                    time.sleep(0.1)  # Wait 100ms before retry
        
        yield
        
    finally:
        # Release lock and close file
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        finally:
            lock_file.close()

def safe_write_json(file_path: Path, data: Dict[str, Any], **kwargs) -> None:
    """
    Atomically write JSON data with file locking.
    
    Uses tempfile + os.replace for atomic writes, preventing corruption
    if the process is interrupted during write.
    
    Args:
        file_path: Path to write JSON to
        data: Dictionary to serialize as JSON
        **kwargs: Additional arguments for json.dump
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary file in same directory for atomic rename
    with tempfile.NamedTemporaryFile(
        mode='w', 
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix='.tmp',
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)
        
        try:
            # Write JSON to temporary file
            json.dump(data, temp_file, **kwargs)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ensure data is written to disk
            
        except Exception:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            raise
    
    # Atomically replace target file with temp file
    try:
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        temp_path.unlink(missing_ok=True)
        raise

def safe_append_line(file_path: Path, line: str) -> None:
    """
    Safely append a line to a file with file locking.
    
    Args:
        file_path: Path to append to
        line: Line to append (should include newline if desired)
    """
    with acquire_file_lock(file_path):
        with open(file_path, 'a') as f:
            f.write(line)
            f.flush()  # Ensure data is written

def safe_read_json(file_path: Path) -> dict:
    """
    Safely read JSON data with file locking.
    
    Args:
        file_path: Path to read JSON from
        
    Returns:
        Dictionary from JSON file
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    import json
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with acquire_file_lock(file_path, mode="shared"):
        with open(file_path, 'r') as f:
            return json.load(f)

def safe_read_lines(file_path: Path) -> list[str]:
    """
    Safely read all lines from a file with file locking.
    
    Args:
        file_path: Path to read from
        
    Returns:
        List of lines from file
        
    Raises:
        FileNotFoundError: If file doesn't exist
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with acquire_file_lock(file_path, mode="shared"):
        with open(file_path, 'r') as f:
            return f.readlines()


def safe_write_text(file_path: Path, content: str) -> None:
    """
    Atomically write text content to a file.
    
    Args:
        file_path: Path to write text to
        content: Text content to write
    """
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary file in same directory for atomic rename
    with tempfile.NamedTemporaryFile(
        mode='w', 
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix='.tmp',
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)
        
        try:
            # Write content to temporary file
            temp_file.write(content)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ensure data is written to disk
            
        except Exception:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            raise
    
    # Atomically replace target file with temp file
    try:
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        temp_path.unlink(missing_ok=True)
        raise


def safe_write_yaml(file_path: Path, data: Dict[str, Any], **kwargs) -> None:
    """
    Atomically write YAML data to a file.
    
    Args:
        file_path: Path to write YAML to
        data: Dictionary to serialize as YAML
        **kwargs: Additional arguments for yaml.dump
    """
    import yaml
    
    # Ensure parent directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create temporary file in same directory for atomic rename
    with tempfile.NamedTemporaryFile(
        mode='w', 
        dir=file_path.parent,
        prefix=f".{file_path.name}.",
        suffix='.tmp',
        delete=False
    ) as temp_file:
        temp_path = Path(temp_file.name)
        
        try:
            # Write YAML to temporary file
            yaml.dump(data, temp_file, **kwargs)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ensure data is written to disk
            
        except Exception:
            # Clean up temp file on error
            temp_path.unlink(missing_ok=True)
            raise
    
    # Atomically replace target file with temp file
    try:
        os.replace(temp_path, file_path)
    except Exception:
        # Clean up temp file on error
        temp_path.unlink(missing_ok=True)
        raise