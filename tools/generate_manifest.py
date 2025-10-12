#!/usr/bin/env python3
"""Generate protocol integrity manifest."""
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
MANIFEST_PATH = REPO_ROOT / ".repo/protocol_manifest.json"

PROTOCOL_FILES = [
    "tools/judge.py",
    "tools/phasectl.py",
    "tools/llm_judge.py",
    ".repo/plan.yaml",
    "tools/lib/__init__.py",
    "tools/lib/git_ops.py",
    "tools/lib/scope.py",
    "tools/lib/traces.py",
    "tools/lib/protocol_guard.py",
]


def sha256(filepath: Path) -> str:
    """Compute SHA256 hash of file."""
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def main():
    """Generate manifest with hashes of all protocol files."""
    print("Generating protocol manifest...")
    print()

    manifest = {"version": 1, "files": {}}

    for rel_path in PROTOCOL_FILES:
        abs_path = REPO_ROOT / rel_path
        if abs_path.exists():
            file_hash = sha256(abs_path)
            manifest["files"][rel_path] = file_hash
            print(f"✓ {rel_path}")
            print(f"  {file_hash}")
        else:
            print(f"⚠ {rel_path} not found")

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n")

    print()
    print(f"✅ Generated {MANIFEST_PATH.relative_to(REPO_ROOT)}")
    print(f"   {len(manifest['files'])} files protected")


if __name__ == "__main__":
    main()
