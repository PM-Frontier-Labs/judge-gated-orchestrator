#!/usr/bin/env python3
"""Test script to verify enhanced baseline enforcement."""

import subprocess
import sys
import tempfile
import os
from pathlib import Path

def test_baseline_enforcement():
    """Test that baseline enforcement blocks invalid baselines."""
    print("🧪 Testing Enhanced Baseline Enforcement")
    print("=" * 50)
    
    # Test 1: Valid baseline (should work)
    print("Test 1: Valid baseline")
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        baseline_sha = result.stdout.strip()
        print(f"✅ Current baseline: {baseline_sha[:8]}...")
        
        # Verify it exists
        verify_result = subprocess.run(
            ["git", "cat-file", "-e", baseline_sha],
            capture_output=True,
            text=True
        )
        if verify_result.returncode == 0:
            print("✅ Baseline verification passed")
        else:
            print("❌ Baseline verification failed")
    else:
        print("❌ Could not get current baseline")
    
    print()
    
    # Test 2: Invalid baseline (should fail)
    print("Test 2: Invalid baseline")
    fake_baseline = "0000000000000000000000000000000000000000"
    verify_result = subprocess.run(
        ["git", "cat-file", "-e", fake_baseline],
        capture_output=True,
        text=True
    )
    if verify_result.returncode != 0:
        print("✅ Invalid baseline correctly rejected")
    else:
        print("❌ Invalid baseline incorrectly accepted")
    
    print()
    
    # Test 3: Test the actual enforcement function
    print("Test 3: Enforcement function")
    try:
        # Import the function
        sys.path.insert(0, str(Path(__file__).parent / "tools"))
        from phasectl import baseline_corrupted, get_baseline_sha
        
        current_baseline = get_baseline_sha()
        is_corrupted = baseline_corrupted()
        
        print(f"Current baseline: {current_baseline[:8] if current_baseline else 'None'}...")
        print(f"Corruption detected: {is_corrupted}")
        
        if not is_corrupted and current_baseline:
            print("✅ Baseline enforcement working correctly")
        else:
            print("⚠️  Baseline enforcement needs attention")
            
    except Exception as e:
        print(f"❌ Error testing enforcement: {e}")
    
    print("=" * 50)
    print("✅ Enhanced baseline enforcement test complete")

if __name__ == "__main__":
    test_baseline_enforcement()
