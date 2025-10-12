"""Trace file operations for gate commands."""

import time
import subprocess
from pathlib import Path
from typing import List, Optional


def run_command_with_trace(
    gate_name: str,
    command: List[str],
    repo_root: Path,
    traces_dir: Path
) -> Optional[int]:
    """
    Run command and save trace. Returns exit code or None if tool missing.
    """
    # Check if tool exists
    tool_name = command[0]
    version_cmd = ["ruff", "--version"] if tool_name == "ruff" else [tool_name, "--version"]

    try:
        subprocess.run(version_cmd, capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

    # Run command
    result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)

    # Save trace
    traces_dir.mkdir(parents=True, exist_ok=True)
    trace_file = traces_dir / f"last_{gate_name}.txt"
    trace_file.write_text(
        f"Exit code: {result.returncode}\n"
        f"Timestamp: {time.time()}\n"
        f"\n=== STDOUT ===\n{result.stdout}\n"
        f"\n=== STDERR ===\n{result.stderr}\n"
    )

    return result.returncode


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
