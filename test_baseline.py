#!/usr/bin/env python3
"""Test script to verify baseline enforcement works."""

import subprocess
import sys
from pathlib import Path

# Add tools directory to path
sys.path.insert(0, str(Path(__file__).parent / "tools"))

from phasectl import baseline_corrupted, get_baseline_sha

def test_baseline_verification():
    """Test that baseline verification works correctly."""
    print("🧪 Testing Baseline Verification")
    print("=" * 40)
    
    # Test 1: Check current baseline
    current_baseline = get_baseline_sha()
    print(f"Current baseline: {current_baseline}")
    
    # Test 2: Check if baseline is corrupted
    is_corrupted = baseline_corrupted()
    print(f"Baseline corrupted: {is_corrupted}")
    
    # Test 3: Verify baseline exists
    if current_baseline:
        result = subprocess.run(
            ["git", "cat-file", "-e", current_baseline],
            capture_output=True,
            text=True
        )
        print(f"Baseline verification: {'✅ Valid' if result.returncode == 0 else '❌ Invalid'}")
    
    print("=" * 40)
    print("✅ Baseline verification test complete")

if __name__ == "__main__":
    test_baseline_verification()




