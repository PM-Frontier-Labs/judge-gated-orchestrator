"""File locking utilities for concurrent execution."""
import time
from pathlib import Path
from contextlib import contextmanager


@contextmanager
def file_lock(lock_file: Path, timeout: int = 30):
    """
    Acquire an exclusive file lock.

    Args:
        lock_file: Path to lock file
        timeout: Maximum seconds to wait for lock

    Raises:
        TimeoutError: If lock cannot be acquired within timeout
    """
    import sys

    # Create lock file directory if needed
    lock_file.parent.mkdir(parents=True, exist_ok=True)

    # Try fcntl first (Unix/Linux/Mac)
    try:
        import fcntl
        lock_fd = None
        lock_acquired = False

        try:
            # Open/create lock file
            lock_fd = open(lock_file, 'w')

            # Try to acquire lock with timeout
            start_time = time.time()
            while True:
                try:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    lock_acquired = True
                    break
                except (IOError, OSError):
                    # Lock held by another process
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Could not acquire lock on {lock_file} within {timeout}s")
                    time.sleep(0.1)

            # Write PID to lock file for debugging
            lock_fd.write(f"{sys.platform}:{time.time()}\n")
            lock_fd.flush()

            yield

        finally:
            if lock_acquired and lock_fd:
                try:
                    fcntl.flock(lock_fd.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass
            if lock_fd:
                try:
                    lock_fd.close()
                except Exception:
                    pass
            # Clean up lock file
            try:
                if lock_file.exists():
                    lock_file.unlink()
            except Exception:
                pass

    except ImportError:
        # fcntl not available (Windows) - fall back to file-based locking
        lock_acquired = False
        start_time = time.time()

        try:
            while True:
                try:
                    # Try to create lock file exclusively
                    lock_fd = lock_file.open('x')
                    lock_fd.write(f"{sys.platform}:{time.time()}\n")
                    lock_fd.close()
                    lock_acquired = True
                    break
                except FileExistsError:
                    # Lock held by another process
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Could not acquire lock on {lock_file} within {timeout}s")

                    # Check if lock file is stale (>60s old)
                    # Note: Stale lock cleanup has been removed to prevent race conditions.
                    # The TOCTOU (time-of-check to time-of-use) vulnerability between checking
                    # the file age and unlinking it could allow multiple processes to acquire
                    # the lock simultaneously. Instead, rely on the timeout mechanism and
                    # manual cleanup if needed.

                    time.sleep(0.1)

            yield

        finally:
            if lock_acquired:
                try:
                    if lock_file.exists():
                        lock_file.unlink()
                except Exception:
                    pass
