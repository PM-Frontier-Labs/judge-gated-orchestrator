"""
Tests for Collective Intelligence System

Tests the file-based pattern storage and retrieval system for the Judge-Gated Protocol.
"""

import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import pytest
import sys
import os

# Add tools directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from tools.lib.collective_intelligence import (
    CollectiveIntelligence, ExecutionPattern, PatternType
)
from tools.lib.execution_patterns import ExecutionPatternManager


class TestCollectiveIntelligence:
    """Test the core collective intelligence system"""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def ci(self, temp_repo):
        """Create CollectiveIntelligence instance with temp repo"""
        return CollectiveIntelligence(temp_repo)
    
    @pytest.fixture
    def sample_pattern(self):
        """Create a sample execution pattern"""
        return ExecutionPattern(
            id="test_pattern_001",
            pattern_type=PatternType.SUCCESS,
            phase_id="P01-test-phase",
            description="Test pattern for unit testing",
            context={"test": True, "phase": "P01"},
            success_factors=["Good planning", "Clear scope"],
            failure_factors=[],
            recommendations=["Test thoroughly", "Document well"],
            metadata={"test": True},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_initialization(self, temp_repo):
        """Test that CI initializes correctly"""
        ci = CollectiveIntelligence(temp_repo)
        
        # Check that storage directory exists
        assert ci.patterns_dir.exists()
        assert ci.patterns_file.exists()
        
        # Check that initial file is created
        with open(ci.patterns_file, 'r') as f:
            data = json.load(f)
        
        assert "version" in data
        assert "patterns" in data
        assert "metadata" in data
        assert data["patterns"] == []
    
    def test_store_pattern(self, ci, sample_pattern):
        """Test storing a pattern"""
        result = ci.store_pattern(sample_pattern)
        assert result is True
        
        # Verify pattern was stored
        patterns = ci.retrieve_patterns()
        assert len(patterns) == 1
        assert patterns[0].id == sample_pattern.id
    
    def test_retrieve_patterns(self, ci, sample_pattern):
        """Test retrieving patterns"""
        # Store a pattern
        ci.store_pattern(sample_pattern)
        
        # Retrieve all patterns
        patterns = ci.retrieve_patterns()
        assert len(patterns) == 1
        assert patterns[0].id == sample_pattern.id
        
        # Retrieve by type
        success_patterns = ci.retrieve_patterns(pattern_type=PatternType.SUCCESS)
        assert len(success_patterns) == 1
        
        failure_patterns = ci.retrieve_patterns(pattern_type=PatternType.FAILURE)
        assert len(failure_patterns) == 0
        
        # Retrieve by phase
        phase_patterns = ci.retrieve_patterns(phase_id="P01-test-phase")
        assert len(phase_patterns) == 1
        
        # Retrieve with limit
        limited_patterns = ci.retrieve_patterns(limit=0)
        assert len(limited_patterns) == 0
    
    def test_search_patterns(self, ci, sample_pattern):
        """Test searching patterns"""
        ci.store_pattern(sample_pattern)
        
        # Search by description
        results = ci.search_patterns("test pattern")
        assert len(results) == 1
        assert results[0].id == sample_pattern.id
        
        # Search by context
        results = ci.search_patterns("test")
        assert len(results) == 1
        
        # Search with pattern type filter
        results = ci.search_patterns("test", pattern_type=PatternType.SUCCESS)
        assert len(results) == 1
        
        results = ci.search_patterns("test", pattern_type=PatternType.FAILURE)
        assert len(results) == 0
    
    def test_get_pattern_by_id(self, ci, sample_pattern):
        """Test getting pattern by ID"""
        ci.store_pattern(sample_pattern)
        
        pattern = ci.get_pattern_by_id(sample_pattern.id)
        assert pattern is not None
        assert pattern.id == sample_pattern.id
        
        # Test non-existent ID
        pattern = ci.get_pattern_by_id("non_existent")
        assert pattern is None
    
    def test_update_pattern(self, ci, sample_pattern):
        """Test updating a pattern"""
        ci.store_pattern(sample_pattern)
        
        # Update pattern
        updates = {
            "description": "Updated description",
            "success_factors": ["Updated factor"]
        }
        
        result = ci.update_pattern(sample_pattern.id, updates)
        assert result is True
        
        # Verify update
        updated_pattern = ci.get_pattern_by_id(sample_pattern.id)
        assert updated_pattern.description == "Updated description"
        assert updated_pattern.success_factors == ["Updated factor"]
        assert updated_pattern.version == 2
    
    def test_delete_pattern(self, ci, sample_pattern):
        """Test deleting a pattern"""
        ci.store_pattern(sample_pattern)
        
        # Verify pattern exists
        patterns = ci.retrieve_patterns()
        assert len(patterns) == 1
        
        # Delete pattern
        result = ci.delete_pattern(sample_pattern.id)
        assert result is True
        
        # Verify deletion
        patterns = ci.retrieve_patterns()
        assert len(patterns) == 0
        
        # Test deleting non-existent pattern
        result = ci.delete_pattern("non_existent")
        assert result is False
    
    def test_get_statistics(self, ci, sample_pattern):
        """Test getting statistics"""
        ci.store_pattern(sample_pattern)
        
        stats = ci.get_statistics()
        assert stats["total_patterns"] == 1
        assert stats["by_type"]["success"] == 1
        assert stats["by_phase"]["P01-test-phase"] == 1
        assert stats["recent_patterns"] == 1
    
    def test_backup_and_restore(self, ci, sample_pattern):
        """Test backup and restore functionality"""
        ci.store_pattern(sample_pattern)
        
        # Create backup
        backup_path = ci.patterns_dir / "test_backup.json"
        result = ci.backup_patterns(backup_path)
        assert result is True
        assert backup_path.exists()
        
        # Clear patterns
        ci.delete_pattern(sample_pattern.id)
        patterns = ci.retrieve_patterns()
        assert len(patterns) == 0
        
        # Restore from backup
        result = ci.restore_patterns(backup_path)
        assert result is True
        
        # Verify restoration
        patterns = ci.retrieve_patterns()
        assert len(patterns) == 1
        assert patterns[0].id == sample_pattern.id


class TestExecutionPatternManager:
    """Test the execution pattern manager"""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def manager(self, temp_repo):
        """Create ExecutionPatternManager instance"""
        return ExecutionPatternManager(temp_repo)
    
    def test_record_phase_success(self, manager):
        """Test recording phase success"""
        pattern_id = manager.record_phase_success(
            phase_id="P02-test",
            description="Test phase success",
            success_factors=["Good planning", "Clear implementation"],
            context={"test": True},
            recommendations=["Continue good practices"]
        )
        
        assert pattern_id != ""
        
        # Verify pattern was stored
        patterns = manager.ci.retrieve_patterns()
        assert len(patterns) == 1
        assert patterns[0].pattern_type == PatternType.SUCCESS
        assert patterns[0].phase_id == "P02-test"
    
    def test_record_phase_failure(self, manager):
        """Test recording phase failure"""
        pattern_id = manager.record_phase_failure(
            phase_id="P02-test",
            description="Test phase failure",
            failure_factors=["Poor planning", "Unclear scope"],
            context={"test": True},
            recommendations=["Improve planning", "Define scope clearly"]
        )
        
        assert pattern_id != ""
        
        # Verify pattern was stored
        patterns = manager.ci.retrieve_patterns()
        assert len(patterns) == 1
        assert patterns[0].pattern_type == PatternType.FAILURE
        assert patterns[0].phase_id == "P02-test"
    
    def test_record_anti_pattern(self, manager):
        """Test recording anti-pattern"""
        pattern_id = manager.record_anti_pattern(
            phase_id="P02-test",
            description="Test anti-pattern",
            anti_pattern_factors=["Over-engineering", "Scope creep"],
            context={"test": True},
            recommendations=["Keep it simple", "Stick to scope"]
        )
        
        assert pattern_id != ""
        
        # Verify pattern was stored
        patterns = manager.ci.retrieve_patterns()
        assert len(patterns) == 1
        assert patterns[0].pattern_type == PatternType.ANTI_PATTERN
        assert patterns[0].phase_id == "P02-test"
    
    def test_get_phase_recommendations(self, manager):
        """Test getting phase recommendations"""
        # Record some patterns
        manager.record_phase_success(
            phase_id="P02-test",
            description="Success pattern",
            success_factors=["Good planning"],
            context={},
            recommendations=["Plan well"]
        )
        
        manager.record_phase_failure(
            phase_id="P02-test",
            description="Failure pattern",
            failure_factors=["Poor planning"],
            context={},
            recommendations=["Improve planning"]
        )
        
        # Get recommendations
        recommendations = manager.get_phase_recommendations("P02-test")
        
        assert recommendations["phase_id"] == "P02-test"
        assert recommendations["success_patterns"] == 1
        assert recommendations["failure_patterns"] == 1
        assert "Good planning" in recommendations["success_factors"]
        assert "Poor planning" in recommendations["failure_factors"]
        assert "Plan well" in recommendations["recommendations"]
        assert "Improve planning" in recommendations["recommendations"]
    
    def test_analyze_execution_trends(self, manager):
        """Test analyzing execution trends"""
        # Record some patterns
        manager.record_phase_success(
            phase_id="P01-test",
            description="Success 1",
            success_factors=["Factor 1", "Factor 2"],
            context={}
        )
        
        manager.record_phase_success(
            phase_id="P02-test",
            description="Success 2",
            success_factors=["Factor 1", "Factor 3"],
            context={}
        )
        
        manager.record_phase_failure(
            phase_id="P03-test",
            description="Failure 1",
            failure_factors=["Factor 4", "Factor 5"],
            context={}
        )
        
        # Analyze trends
        trends = manager.analyze_execution_trends()
        
        assert trends["total_patterns"] == 3
        assert trends["by_type"]["success"] == 2
        assert trends["by_type"]["failure"] == 1
        assert trends["success_rate"] == 2/3
        assert "Factor 1" in trends["common_success_factors"]
        assert "Factor 4" in trends["common_failure_factors"]
    
    def test_export_import_patterns(self, manager, temp_repo):
        """Test exporting and importing patterns"""
        # Record a pattern
        manager.record_phase_success(
            phase_id="P01-test",
            description="Test pattern",
            success_factors=["Test factor"],
            context={}
        )
        
        # Export patterns
        export_path = Path(temp_repo) / "exported_patterns.json"
        result = manager.export_patterns(export_path)
        assert result is True
        assert export_path.exists()
        
        # Create new manager with different temp directory
        import tempfile
        new_temp_dir = tempfile.mkdtemp()
        try:
            new_manager = ExecutionPatternManager(new_temp_dir)
            patterns_before = new_manager.ci.retrieve_patterns()
            assert len(patterns_before) == 0
            
            result = new_manager.import_patterns(export_path)
            assert result is True
            
            patterns_after = new_manager.ci.retrieve_patterns()
            assert len(patterns_after) == 1
            assert patterns_after[0].phase_id == "P01-test"
        finally:
            import shutil
            shutil.rmtree(new_temp_dir)
    
    def test_cleanup_old_patterns(self, manager):
        """Test cleaning up old patterns"""
        # Record a pattern
        manager.record_phase_success(
            phase_id="P01-test",
            description="Test pattern",
            success_factors=["Test factor"],
            context={}
        )
        
        # Cleanup patterns older than 0 days (should remove all)
        removed_count = manager.cleanup_old_patterns(days_old=0)
        assert removed_count == 1
        
        # Verify cleanup
        patterns = manager.ci.retrieve_patterns()
        assert len(patterns) == 0


if __name__ == "__main__":
    pytest.main([__file__])
