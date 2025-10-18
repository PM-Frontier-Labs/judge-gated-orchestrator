"""Trace file operations for gate commands."""

import time
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command_with_trace(
    gate_name: str,
    command: List[str],
    repo_root: Path,
    traces_dir: Path,
    timeout_seconds: int = 600,
) -> Optional[int]:
    """
    Run command and save trace. Returns exit code or None if tool missing.
    """
    # Check if tool exists
    tool_name = command[0]
    version_cmd = ["ruff", "--version"] if tool_name == "ruff" else [tool_name, "--version"]

    try:
        subprocess.run(version_cmd, capture_output=True, check=True, timeout=30)
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return None

    # Run command with timeout; capture timeout distinctly
    timed_out = False
    try:
        result = subprocess.run(
            command,
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        return_code = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as e:
        timed_out = True
        return_code = 124  # conventional timeout code
        stdout = e.stdout or ""
        stderr = (e.stderr or "") + f"\n[timeout] Command exceeded {timeout_seconds}s and was terminated."

    # Save trace
    traces_dir.mkdir(parents=True, exist_ok=True)
    trace_file = traces_dir / f"last_{gate_name}.txt"
    trace_file.write_text(
        f"Exit code: {return_code}\n"
        f"Timestamp: {time.time()}\n"
        f"\n=== STDOUT ===\n{stdout}\n"
        f"\n=== STDERR ===\n{stderr}\n"
        + ("\n[Note] Process timed out.\n" if timed_out else "")
    )

    return return_code


def check_gate_trace(gate_name: str, traces_dir: Path, error_prefix: str) -> List[str]:
    """Read trace and return issues if failed."""
    trace_file = traces_dir / f"last_{gate_name}.txt"

    if not trace_file.exists():
        return [f"No {gate_name} results found. {error_prefix} may not have run."]

    # Parse exit code
    for line in trace_file.read_text().split("\n"):
        if line.startswith("Exit code:"):
            try:
                exit_code = int(line.split(":")[1].strip())
                if exit_code == 0:
                    return []
                return [
                    f"{error_prefix} failed with exit code {exit_code}. "
                    f"See {trace_file.relative_to(trace_file.parent.parent.parent)} for details."
                ]
            except (ValueError, IndexError):
                pass

    return [f"Could not parse {gate_name} exit code from trace"]
