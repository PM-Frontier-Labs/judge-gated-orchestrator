"""Trace file operations for gate commands and collective intelligence."""

import time
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


def run_command_with_trace(
    gate_name: str,
    command: List[str],
    repo_root: Path,
    traces_dir: Path
) -> Optional[int]:
    """
    Run command and save trace. Returns exit code or None if tool missing.
    """
    # Run command directly, catch FileNotFoundError if tool missing
    try:
        result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True)
    except FileNotFoundError:
        return None

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
                # Use more robust path resolution - show relative to repo root
                try:
                    repo_root = traces_dir.parent.parent  # .repo/traces -> .repo -> repo_root
                    relative_path = trace_file.relative_to(repo_root)
                except ValueError:
                    # Fallback to absolute path if relative resolution fails
                    relative_path = trace_file
                
                return [
                    f"{error_prefix} failed with exit code {exit_code}. "
                    f"See {relative_path} for details."
                ]
            except (ValueError, IndexError):
                pass

    return [f"Could not parse {gate_name} exit code from trace"]


# Collective Intelligence Functions

def store_pattern(pattern: Dict[str, Any], repo_root: str = ".") -> None:
    """Store a pattern in JSONL format with file locking to prevent concurrent writes"""
    patterns_file = Path(repo_root) / ".repo" / "collective_intelligence" / "patterns.jsonl"
    patterns_file.parent.mkdir(parents=True, exist_ok=True)
    
    pattern["timestamp"] = datetime.now().isoformat()
    
    # Use file locking to prevent concurrent writes
    import fcntl
    with open(patterns_file, 'a') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        try:
            f.write(json.dumps(pattern) + '\n')
            f.flush()  # Ensure data is written
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Release lock

def find_matching_patterns(context: Dict[str, Any], repo_root: str = ".") -> List[Dict[str, Any]]:
    """Find patterns that match the current context"""
    patterns_file = Path(repo_root) / ".repo" / "collective_intelligence" / "patterns.jsonl"
    
    if not patterns_file.exists():
        return []
    
    matches = []
    with open(patterns_file, 'r') as f:
        for line in f:
            pattern = json.loads(line.strip())
            if _pattern_matches(pattern, context):
                matches.append(pattern)
    
    # Sort by confidence and recency
    matches.sort(key=lambda p: (p.get("confidence", 0), p.get("timestamp", "")), reverse=True)
    
    return matches

def propose_amendments_from_patterns(context: Dict[str, Any], repo_root: str = ".") -> List[Dict[str, Any]]:
    """Propose amendments based on matching patterns"""
    patterns = find_matching_patterns(context, repo_root)
    proposals = []
    
    for pattern in patterns:
        if pattern.get("kind") == "fix":
            action = pattern.get("action", {})
            if action.get("amend"):
                proposals.append({
                    "type": action["amend"],
                    "value": action["value"],
                    "reason": f"Pattern match: {pattern.get('description', 'Unknown')}",
                    "confidence": pattern.get("confidence", 0.5)
                })
    
    return proposals

def _pattern_matches(pattern: Dict[str, Any], context: Dict[str, Any]) -> bool:
    """Check if pattern matches context"""
    when = pattern.get("when", {})
    
    # Check pytest error match
    if "pytest_error" in when:
        test_output = context.get("test_output", "")
        if when["pytest_error"] in test_output:
            return True
    
    # Check lint error match
    if "lint_error" in when:
        lint_output = context.get("lint_output", "")
        if when["lint_error"] in lint_output:
            return True
    
    # Check file changed match
    if "file_changed" in when:
        changed_files = context.get("changed_files", [])
        for file_path in changed_files:
            if when["file_changed"] in file_path:
                return True
    
    return False


# Outer Loop Functions

def write_micro_retro(phase_id: str, execution_data: Dict[str, Any], repo_root: str = ".") -> str:
    """Write a micro-retrospective for a phase"""
    traces_dir = Path(repo_root) / ".repo" / "traces"
    traces_dir.mkdir(parents=True, exist_ok=True)
    
    retro_data = {
        "phase": phase_id,
        "timestamp": datetime.now().isoformat(),
        "retries": execution_data.get("retries", 0),
        "amendments": execution_data.get("amendments", []),
        "llm_score": execution_data.get("llm_score", 0.0),
        "root_cause": execution_data.get("root_cause", "unknown"),
        "what_helped": execution_data.get("what_helped", []),
        "success": execution_data.get("success", False),
        "execution_time": execution_data.get("execution_time", "unknown")
    }
    
    retro_file = traces_dir / f"{phase_id}.outer.json"
    with open(retro_file, 'w') as f:
        json.dump(retro_data, f, indent=2)
    
    return str(retro_file)

def read_micro_retro(phase_id: str, repo_root: str = ".") -> Optional[Dict[str, Any]]:
    """Read a micro-retrospective for a phase"""
    retro_file = Path(repo_root) / ".repo" / "traces" / f"{phase_id}.outer.json"
    
    if not retro_file.exists():
        return None
    
    with open(retro_file, 'r') as f:
        return json.load(f)

def get_phase_hints(phase_id: str, lookback_count: int = 3, repo_root: str = ".") -> List[str]:
    """Get hints from recent phase executions"""
    traces_dir = Path(repo_root) / ".repo" / "traces"
    
    if not traces_dir.exists():
        return []
    
    hints = []
    retro_files = sorted(traces_dir.glob("*.outer.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    
    for retro_file in retro_files[:lookback_count]:
        with open(retro_file, 'r') as f:
            retro = json.load(f)
        
        if retro.get("success") and retro.get("what_helped"):
            hints.extend(retro["what_helped"])
    
    return hints[:5]  # Limit to 5 hints
