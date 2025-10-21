#!/usr/bin/env python3
"""
Tests for Atomic Write Utilities.

Tests the file locking and atomic write functionality.
"""

import sys
import pytest
import tempfile
import json
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

# Add tools/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.file_lock import (
    safe_write_json, safe_write_text, safe_write_yaml,
    safe_read_json, safe_append_line, safe_read_lines
)


class TestSafeWriteJson:
    """Test atomic JSON writing."""
    
    def test_safe_write_json_basic(self):
        """Test basic JSON writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value", "number": 42}
            
            safe_write_json(file_path, data)
            
            assert file_path.exists()
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == data
    
    def test_safe_write_json_with_indent(self):
        """Test JSON writing with indentation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value", "nested": {"inner": "data"}}
            
            safe_write_json(file_path, data, indent=2)
            
            assert file_path.exists()
            content = file_path.read_text()
            assert "  " in content  # Should have indentation
    
    def test_safe_write_json_overwrite(self):
        """Test overwriting existing JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            
            # Write initial data
            initial_data = {"old": "data"}
            safe_write_json(file_path, initial_data)
            
            # Overwrite with new data
            new_data = {"new": "data"}
            safe_write_json(file_path, new_data)
            
            # Verify overwrite
            with open(file_path, 'r') as f:
                loaded_data = json.load(f)
            assert loaded_data == new_data
            assert loaded_data != initial_data
    
    def test_safe_write_json_creates_directory(self):
        """Test that parent directory is created if needed."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "subdir" / "test.json"
            data = {"key": "value"}
            
            safe_write_json(file_path, data)
            
            assert file_path.exists()
            assert file_path.parent.exists()
    
    def test_safe_write_json_atomic(self):
        """Test that writes are atomic (no partial files)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value"}
            
            # Mock os.replace to simulate failure
            with patch('os.replace', side_effect=OSError("Simulated failure")):
                with pytest.raises(OSError):
                    safe_write_json(file_path, data)
            
            # File should not exist after failed write
            assert not file_path.exists()


class TestSafeWriteText:
    """Test atomic text writing."""
    
    def test_safe_write_text_basic(self):
        """Test basic text writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello, World!\nThis is a test."
            
            safe_write_text(file_path, content)
            
            assert file_path.exists()
            assert file_path.read_text() == content
    
    def test_safe_write_text_empty(self):
        """Test writing empty content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            
            safe_write_text(file_path, "")
            
            assert file_path.exists()
            assert file_path.read_text() == ""
    
    def test_safe_write_text_unicode(self):
        """Test writing Unicode content."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Hello 世界! 🌍"
            
            safe_write_text(file_path, content)
            
            assert file_path.exists()
            assert file_path.read_text() == content


class TestSafeWriteYaml:
    """Test atomic YAML writing."""
    
    def test_safe_write_yaml_basic(self):
        """Test basic YAML writing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.yaml"
            data = {"key": "value", "list": [1, 2, 3]}
            
            safe_write_yaml(file_path, data)
            
            assert file_path.exists()
            with open(file_path, 'r') as f:
                loaded_data = yaml.safe_load(f)
            assert loaded_data == data
    
    def test_safe_write_yaml_with_default_flow_style(self):
        """Test YAML writing with flow style."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.yaml"
            data = {"key": "value", "list": [1, 2, 3]}
            
            safe_write_yaml(file_path, data, default_flow_style=False)
            
            assert file_path.exists()
            content = file_path.read_text()
            assert "key: value" in content


class TestSafeReadJson:
    """Test safe JSON reading."""
    
    def test_safe_read_json_basic(self):
        """Test basic JSON reading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            data = {"key": "value", "number": 42}
            
            # Write file first
            with open(file_path, 'w') as f:
                json.dump(data, f)
            
            # Read it back
            loaded_data = safe_read_json(file_path)
            assert loaded_data == data
    
    def test_safe_read_json_file_not_found(self):
        """Test reading non-existent JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.json"
            
            with pytest.raises(FileNotFoundError):
                safe_read_json(file_path)
    
    def test_safe_read_json_invalid_json(self):
        """Test reading invalid JSON file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "invalid.json"
            
            # Write invalid JSON
            with open(file_path, 'w') as f:
                f.write("{ invalid json }")
            
            with pytest.raises(json.JSONDecodeError):
                safe_read_json(file_path)


class TestSafeAppendLine:
    """Test safe line appending."""
    
    def test_safe_append_line_basic(self):
        """Test basic line appending."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            
            # Append first line
            safe_append_line(file_path, "First line\n")
            assert file_path.read_text() == "First line\n"
            
            # Append second line
            safe_append_line(file_path, "Second line\n")
            assert file_path.read_text() == "First line\nSecond line\n"
    
    def test_safe_append_line_creates_file(self):
        """Test that appending creates file if it doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "new_file.txt"
            
            safe_append_line(file_path, "New line\n")
            
            assert file_path.exists()
            assert file_path.read_text() == "New line\n"


class TestSafeReadLines:
    """Test safe line reading."""
    
    def test_safe_read_lines_basic(self):
        """Test basic line reading."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.txt"
            content = "Line 1\nLine 2\nLine 3\n"
            
            # Write file
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Read lines
            lines = safe_read_lines(file_path)
            assert lines == ["Line 1\n", "Line 2\n", "Line 3\n"]
    
    def test_safe_read_lines_file_not_found(self):
        """Test reading non-existent file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "nonexistent.txt"
            
            with pytest.raises(FileNotFoundError):
                safe_read_lines(file_path)


class TestConcurrencySafety:
    """Test concurrency safety of file operations."""
    
    def test_concurrent_writes_same_file(self):
        """Test that concurrent writes to same file are handled safely."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "concurrent.json"
            
            # This test would require actual concurrent execution
            # For now, just test that the functions don't crash
            data1 = {"process": 1, "data": "first"}
            data2 = {"process": 2, "data": "second"}
            
            safe_write_json(file_path, data1)
            safe_write_json(file_path, data2)
            
            # Final file should exist and be valid JSON
            assert file_path.exists()
            with open(file_path, 'r') as f:
                json.load(f)  # Should not raise JSONDecodeError


class TestErrorHandling:
    """Test error handling in file operations."""
    
    def test_write_permission_error(self):
        """Test handling of permission errors."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Make the entire directory read-only
            temp_path = Path(temp_dir)
            temp_path.chmod(0o444)  # Read-only directory
            
            try:
                file_path = temp_path / "test.json"
                
                with pytest.raises(PermissionError):
                    safe_write_json(file_path, {"key": "value"})
            finally:
                # Restore permissions for cleanup
                temp_path.chmod(0o755)
    
    def test_temp_file_cleanup_on_error(self):
        """Test that temp files are cleaned up on error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = Path(temp_dir) / "test.json"
            
            # Mock tempfile.NamedTemporaryFile to raise error
            with patch('tempfile.NamedTemporaryFile', side_effect=OSError("Simulated error")):
                with pytest.raises(OSError):
                    safe_write_json(file_path, {"key": "value"})
            
            # No temp files should be left behind
            temp_files = list(Path(temp_dir).glob(".*"))
            assert len(temp_files) == 0
