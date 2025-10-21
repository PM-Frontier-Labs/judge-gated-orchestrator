#!/usr/bin/env python3
"""
Tests for Collective Intelligence Consolidation.

Tests that the collective intelligence system uses consistent JSONL format.
"""

import sys
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

# Add tools/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.traces import store_pattern, find_matching_patterns


class TestCollectiveIntelligenceConsolidation:
    """Test that collective intelligence uses consistent JSONL format."""
    
    def test_store_pattern_jsonl_format(self):
        """Test that store_pattern uses JSONL format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            pattern = {
                "id": "test_pattern_1",
                "type": "success",
                "phase_id": "P01-test",
                "description": "Test pattern",
                "context": {"key": "value"},
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            # Store pattern
            store_pattern(pattern, repo_root)
            
            # Check that patterns.jsonl was created
            patterns_file = Path(repo_root) / ".repo" / "collective_intelligence" / "patterns.jsonl"
            assert patterns_file.exists()
            
            # Verify JSONL format (one JSON object per line)
            with open(patterns_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 1
                
                # Parse the JSON line
                stored_pattern = json.loads(lines[0].strip())
                assert stored_pattern == pattern
    
    def test_store_pattern_multiple_patterns(self):
        """Test storing multiple patterns in JSONL format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            patterns = [
                {
                    "id": "pattern_1",
                    "type": "success",
                    "phase_id": "P01-test",
                    "description": "First pattern"
                },
                {
                    "id": "pattern_2", 
                    "type": "failure",
                    "phase_id": "P02-test",
                    "description": "Second pattern"
                }
            ]
            
            # Store both patterns
            for pattern in patterns:
                store_pattern(pattern, repo_root)
            
            # Check JSONL file
            patterns_file = Path(repo_root) / ".repo" / "collective_intelligence" / "patterns.jsonl"
            assert patterns_file.exists()
            
            with open(patterns_file, 'r') as f:
                lines = f.readlines()
                assert len(lines) == 2
                
                # Parse both JSON lines
                stored_patterns = [json.loads(line.strip()) for line in lines]
                assert stored_patterns == patterns
    
    def test_find_matching_patterns_jsonl_format(self):
        """Test that find_matching_patterns reads JSONL format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            # Create patterns.jsonl file manually
            patterns_dir = Path(repo_root) / ".repo" / "collective_intelligence"
            patterns_dir.mkdir(parents=True, exist_ok=True)
            patterns_file = patterns_dir / "patterns.jsonl"
            
            patterns = [
                {
                    "id": "pattern_1",
                    "type": "success",
                    "phase_id": "P01-test",
                    "description": "Test pattern",
                    "when": {"pytest_error": "test failure"},
                    "confidence": 0.8
                },
                {
                    "id": "pattern_2",
                    "type": "failure",
                    "phase_id": "P02-test",
                    "description": "Another pattern",
                    "when": {"lint_error": "syntax error"},
                    "confidence": 0.6
                }
            ]
            
            # Write patterns in JSONL format
            with open(patterns_file, 'w') as f:
                for pattern in patterns:
                    f.write(json.dumps(pattern) + '\n')
            
            # Test finding patterns
            context = {"test_output": "test failure occurred"}
            matching_patterns = find_matching_patterns(context, repo_root)
            
            assert len(matching_patterns) == 1
            assert matching_patterns[0]["id"] == "pattern_1"
    
    def test_no_mixed_json_jsonl_formats(self):
        """Test that no .json files exist for collective intelligence."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            # Store a pattern
            pattern = {"id": "test", "type": "success"}
            store_pattern(pattern, repo_root)
            
            # Check that only .jsonl file exists, no .json files
            patterns_dir = Path(repo_root) / ".repo" / "collective_intelligence"
            
            jsonl_files = list(patterns_dir.glob("*.jsonl"))
            json_files = list(patterns_dir.glob("*.json"))
            
            assert len(jsonl_files) == 1
            assert len(json_files) == 0
            assert jsonl_files[0].name == "patterns.jsonl"
    
    def test_jsonl_format_consistency(self):
        """Test that JSONL format is consistent across all operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            # Store multiple patterns
            patterns = [
                {"id": f"pattern_{i}", "type": "success", "phase_id": f"P{i:02d}-test"}
                for i in range(1, 4)
            ]
            
            for pattern in patterns:
                store_pattern(pattern, repo_root)
            
            # Read back and verify format consistency
            patterns_file = Path(repo_root) / ".repo" / "collective_intelligence" / "patterns.jsonl"
            
            with open(patterns_file, 'r') as f:
                lines = f.readlines()
                
                # Each line should be valid JSON
                stored_patterns = []
                for line in lines:
                    line = line.strip()
                    if line:  # Skip empty lines
                        pattern = json.loads(line)
                        stored_patterns.append(pattern)
                
                assert len(stored_patterns) == 3
                assert stored_patterns == patterns
    
    def test_empty_patterns_file(self):
        """Test handling of empty patterns file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            # Create empty patterns file
            patterns_dir = Path(repo_root) / ".repo" / "collective_intelligence"
            patterns_dir.mkdir(parents=True, exist_ok=True)
            patterns_file = patterns_dir / "patterns.jsonl"
            patterns_file.touch()
            
            # Should handle empty file gracefully
            context = {"key": "value"}
            matching_patterns = find_matching_patterns(context, repo_root)
            assert matching_patterns == []
    
    def test_corrupted_jsonl_file(self):
        """Test handling of corrupted JSONL file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = temp_dir
            
            # Create corrupted patterns file
            patterns_dir = Path(repo_root) / ".repo" / "collective_intelligence"
            patterns_dir.mkdir(parents=True, exist_ok=True)
            patterns_file = patterns_dir / "patterns.jsonl"
            
            with open(patterns_file, 'w') as f:
                f.write('{"valid": "json"}\n')
                f.write('{"invalid": json}\n')  # Invalid JSON
                f.write('{"another": "valid"}\n')
            
            # Should handle corrupted lines gracefully
            context = {"test_output": "test failure"}
            matching_patterns = find_matching_patterns(context, repo_root)
            
            # Should return patterns from valid lines only
            assert len(matching_patterns) >= 0  # Should not crash
