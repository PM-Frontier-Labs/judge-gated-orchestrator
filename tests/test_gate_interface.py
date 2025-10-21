#!/usr/bin/env python3
"""
Tests for the Gate Interface System.

Tests the pluggable gate system, gate implementations, and gate registry.
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Add tools/lib to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))

from lib.gate_interface import (
    GateInterface, ArtifactsGate, TestsGate, LintGate, DocsGate, 
    DriftGate, LLMReviewGate, IntegrityGate, GATE_REGISTRY, run_gates
)


class TestGateInterface:
    """Test the abstract gate interface."""
    
    def test_gate_interface_abstract(self):
        """Test that GateInterface cannot be instantiated directly."""
        with pytest.raises(TypeError):
            GateInterface()


class TestArtifactsGate:
    """Test the ArtifactsGate implementation."""
    
    def test_artifacts_gate_properties(self):
        """Test gate properties."""
        gate = ArtifactsGate()
        assert gate.name == "artifacts"
        assert gate.description == "Check for required artifacts"
        assert gate.is_enabled({}) == True  # Always enabled
    
    def test_artifacts_gate_no_artifacts(self):
        """Test gate with no required artifacts."""
        gate = ArtifactsGate()
        phase = {"artifacts": []}
        plan = {}
        context = {}
        
        issues = gate.run(phase, plan, context)
        assert issues == []
    
    def test_artifacts_gate_missing_artifacts(self):
        """Test gate with missing artifacts."""
        gate = ArtifactsGate()
        phase = {"artifacts": ["missing_file.txt", "another_missing.py"]}
        plan = {}
        context = {}
        
        with patch('pathlib.Path.exists', return_value=False):
            issues = gate.run(phase, plan, context)
            assert len(issues) == 2
            assert "Missing required artifact: missing_file.txt" in issues
            assert "Missing required artifact: another_missing.py" in issues
    
    def test_artifacts_gate_existing_artifacts(self):
        """Test gate with existing artifacts."""
        gate = ArtifactsGate()
        phase = {"artifacts": ["existing_file.txt"]}
        plan = {}
        context = {}
        
        with patch('pathlib.Path.exists', return_value=True):
            issues = gate.run(phase, plan, context)
            assert issues == []


class TestTestsGate:
    """Test the TestsGate implementation."""
    
    def test_tests_gate_properties(self):
        """Test gate properties."""
        gate = TestsGate()
        assert gate.name == "tests"
        assert gate.description == "Check test execution results"
        assert gate.is_enabled({}) == True  # Always enabled
    
    def test_tests_gate_missing_traces_dir(self):
        """Test gate with missing traces directory."""
        gate = TestsGate()
        phase = {}
        plan = {}
        context = {}  # No traces_dir
        
        issues = gate.run(phase, plan, context)
        assert len(issues) == 1
        assert "Tests gate: traces_dir not provided in context" in issues
    
    def test_tests_gate_success(self):
        """Test gate with successful test execution."""
        gate = TestsGate()
        phase = {}
        plan = {}
        context = {"traces_dir": "/path/to/traces"}
        
        with patch('lib.traces.check_gate_trace', return_value=[]):
            issues = gate.run(phase, plan, context)
            assert issues == []


class TestLintGate:
    """Test the LintGate implementation."""
    
    def test_lint_gate_properties(self):
        """Test gate properties."""
        gate = LintGate()
        assert gate.name == "lint"
        assert gate.description == "Check linting results"
    
    def test_lint_gate_disabled(self):
        """Test gate when lint is disabled."""
        gate = LintGate()
        phase = {"gates": {"lint": {"must_pass": False}}}
        assert gate.is_enabled(phase) == False
    
    def test_lint_gate_enabled(self):
        """Test gate when lint is enabled."""
        gate = LintGate()
        phase = {"gates": {"lint": {"must_pass": True}}}
        assert gate.is_enabled(phase) == True
    
    def test_lint_gate_default_disabled(self):
        """Test gate default state (disabled)."""
        gate = LintGate()
        phase = {}
        assert gate.is_enabled(phase) == False


class TestDocsGate:
    """Test the DocsGate implementation."""
    
    def test_docs_gate_properties(self):
        """Test gate properties."""
        gate = DocsGate()
        assert gate.name == "docs"
        assert gate.description == "Check documentation requirements"
        assert gate.is_enabled({}) == True  # Always enabled
    
    def test_docs_gate_no_requirements(self):
        """Test gate with no documentation requirements."""
        gate = DocsGate()
        phase = {"gates": {"docs": {"must_update": []}}}
        plan = {}
        context = {"changed_files": ["src/foo.py"]}
        
        issues = gate.run(phase, plan, context)
        assert issues == []
    
    def test_docs_gate_missing_docs(self):
        """Test gate with missing documentation updates."""
        gate = DocsGate()
        phase = {"gates": {"docs": {"must_update": ["docs/api/"]}}}
        plan = {}
        context = {"changed_files": ["src/foo.py"]}  # No docs changes
        
        issues = gate.run(phase, plan, context)
        assert len(issues) == 1
        assert "Documentation gate failed: docs/api/ not updated" in issues
    
    def test_docs_gate_success(self):
        """Test gate with successful documentation updates."""
        gate = DocsGate()
        phase = {"gates": {"docs": {"must_update": ["docs/api/"]}}}
        plan = {}
        context = {"changed_files": ["docs/api/endpoints.md"]}
        
        issues = gate.run(phase, plan, context)
        assert issues == []


class TestDriftGate:
    """Test the DriftGate implementation."""
    
    def test_drift_gate_properties(self):
        """Test gate properties."""
        gate = DriftGate()
        assert gate.name == "drift"
        assert gate.description == "Check for plan drift"
        assert gate.is_enabled({}) == True  # Always enabled
    
    def test_drift_gate_disabled(self):
        """Test gate when drift checking is disabled."""
        gate = DriftGate()
        phase = {}  # No drift gate config
        plan = {}
        context = {}
        
        issues = gate.run(phase, plan, context)
        assert issues == []
    
    def test_drift_gate_no_changes(self):
        """Test gate with no file changes."""
        gate = DriftGate()
        phase = {"gates": {"drift": {"allowed_out_of_scope_changes": 5}}}
        plan = {"plan": {"base_branch": "main"}}
        context = {}
        
        with patch('lib.git_ops.get_changed_files', return_value=([], [])):
            issues = gate.run(phase, plan, context)
            assert issues == []
    
    def test_drift_gate_within_limits(self):
        """Test gate with drift within allowed limits."""
        gate = DriftGate()
        phase = {
            "gates": {"drift": {"allowed_out_of_scope_changes": 5}},
            "scope": {"include": ["src/"], "exclude": []}
        }
        plan = {"plan": {"base_branch": "main"}}
        context = {}
        
        changed_files = ["src/foo.py", "docs/readme.md", "tests/test.py"]
        
        with patch('lib.git_ops.get_changed_files', return_value=(changed_files, [])):
            with patch('lib.scope.classify_files', return_value=(["src/foo.py"], ["docs/readme.md", "tests/test.py"])):
                issues = gate.run(phase, plan, context)
                assert issues == []
    
    def test_drift_gate_exceeds_limits(self):
        """Test gate with drift exceeding allowed limits."""
        gate = DriftGate()
        phase = {
            "gates": {"drift": {"allowed_out_of_scope_changes": 1}},
            "scope": {"include": ["src/"], "exclude": []}
        }
        plan = {"plan": {"base_branch": "main"}}
        context = {}
        
        changed_files = ["src/foo.py", "docs/readme.md", "tests/test.py", "config/settings.yml"]
        
        with patch('lib.git_ops.get_changed_files', return_value=(changed_files, [])):
            with patch('lib.scope.classify_files', return_value=(["src/foo.py"], ["docs/readme.md", "tests/test.py", "config/settings.yml"])):
                issues = gate.run(phase, plan, context)
                assert len(issues) == 1
                assert "Plan drift detected: 3 out-of-scope files changed (limit: 1)" in issues[0]


class TestLLMReviewGate:
    """Test the LLMReviewGate implementation."""
    
    def test_llm_gate_properties(self):
        """Test gate properties."""
        gate = LLMReviewGate()
        assert gate.name == "llm_review"
        assert gate.description == "LLM-based code review"
    
    def test_llm_gate_disabled(self):
        """Test gate when LLM review is disabled."""
        gate = LLMReviewGate()
        phase = {"gates": {"llm_review": {"enabled": False}}}
        assert gate.is_enabled(phase) == False
    
    def test_llm_gate_enabled(self):
        """Test gate when LLM review is enabled."""
        gate = LLMReviewGate()
        phase = {"gates": {"llm_review": {"enabled": True}}}
        assert gate.is_enabled(phase) == True
    
    def test_llm_gate_default_disabled(self):
        """Test gate default state (disabled)."""
        gate = LLMReviewGate()
        phase = {}
        assert gate.is_enabled(phase) == False
    
    def test_llm_gate_import_error(self):
        """Test gate when llm_judge is not available."""
        gate = LLMReviewGate()
        phase = {"gates": {"llm_review": {"enabled": True}}}
        plan = {}
        context = {"repo_root": "/path/to/repo", "baseline_sha": "abc123"}
        
        with patch('builtins.__import__', side_effect=ImportError):
            issues = gate.run(phase, plan, context)
            assert len(issues) == 1
            assert "LLM review enabled but llm_judge not available" in issues


class TestIntegrityGate:
    """Test the IntegrityGate implementation."""
    
    def test_integrity_gate_properties(self):
        """Test gate properties."""
        gate = IntegrityGate()
        assert gate.name == "integrity"
        assert gate.description == "Check protocol integrity"
        assert gate.is_enabled({}) == True  # Always enabled
    
    def test_integrity_gate_success(self):
        """Test gate with successful integrity check."""
        gate = IntegrityGate()
        phase = {}
        plan = {}
        context = {"repo_root": "/path/to/repo", "baseline_sha": "abc123"}
        
        with patch('lib.protocol_guard.verify_protocol_lock', return_value=[]):
            issues = gate.run(phase, plan, context)
            assert issues == []


class TestGateRegistry:
    """Test the gate registry system."""
    
    def test_gate_registry_contains_all_gates(self):
        """Test that registry contains all expected gates."""
        expected_gates = {
            "artifacts", "tests", "lint", "docs", 
            "drift", "llm_review", "integrity"
        }
        assert set(GATE_REGISTRY.keys()) == expected_gates
    
    def test_gate_registry_types(self):
        """Test that all gates implement GateInterface."""
        for gate_name, gate in GATE_REGISTRY.items():
            assert isinstance(gate, GateInterface)
            assert hasattr(gate, 'name')
            assert hasattr(gate, 'description')
            assert hasattr(gate, 'is_enabled')
            assert hasattr(gate, 'run')
            assert gate.name == gate_name


class TestRunGates:
    """Test the run_gates function."""
    
    def test_run_gates_all_enabled(self):
        """Test running all enabled gates."""
        phase = {
            "gates": {
                "lint": {"must_pass": True},
                "llm_review": {"enabled": True}
            }
        }
        plan = {}
        context = {"traces_dir": "/path/to/traces"}
        
        with patch('lib.gate_interface.ArtifactsGate.run', return_value=[]) as mock_artifacts, \
             patch('lib.gate_interface.TestsGate.run', return_value=[]) as mock_tests, \
             patch('lib.gate_interface.LintGate.run', return_value=[]) as mock_lint, \
             patch('lib.gate_interface.DocsGate.run', return_value=[]) as mock_docs, \
             patch('lib.gate_interface.DriftGate.run', return_value=[]) as mock_drift, \
             patch('lib.gate_interface.LLMReviewGate.run', return_value=[]) as mock_llm, \
             patch('lib.gate_interface.IntegrityGate.run', return_value=[]) as mock_integrity:
            
            results = run_gates(phase, plan, context)
            
            # All gates should have been called
            assert "artifacts" in results
            assert "tests" in results
            assert "lint" in results
            assert "docs" in results
            assert "drift" in results
            assert "llm_review" in results
            assert "integrity" in results
    
    def test_run_gates_some_disabled(self):
        """Test running gates with some disabled."""
        phase = {
            "gates": {
                "lint": {"must_pass": False},
                "llm_review": {"enabled": False}
            }
        }
        plan = {}
        context = {"traces_dir": "/path/to/traces"}
        
        with patch('lib.gate_interface.ArtifactsGate.run', return_value=[]) as mock_artifacts, \
             patch('lib.gate_interface.TestsGate.run', return_value=[]) as mock_tests, \
             patch('lib.gate_interface.DocsGate.run', return_value=[]) as mock_docs, \
             patch('lib.gate_interface.DriftGate.run', return_value=[]) as mock_drift, \
             patch('lib.gate_interface.IntegrityGate.run', return_value=[]) as mock_integrity:
            
            results = run_gates(phase, plan, context)
            
            # Only enabled gates should be in results
            assert "artifacts" in results
            assert "tests" in results
            assert "docs" in results
            assert "drift" in results
            assert "integrity" in results
            assert "lint" not in results
            assert "llm_review" not in results
    
    def test_run_gates_with_issues(self):
        """Test running gates that return issues."""
        phase = {}
        plan = {}
        context = {"traces_dir": "/path/to/traces"}
        
        with patch('lib.gate_interface.ArtifactsGate.run', return_value=["Missing artifact"]) as mock_artifacts, \
             patch('lib.gate_interface.TestsGate.run', return_value=[]) as mock_tests, \
             patch('lib.gate_interface.DocsGate.run', return_value=["Docs not updated"]) as mock_docs, \
             patch('lib.gate_interface.DriftGate.run', return_value=[]) as mock_drift, \
             patch('lib.gate_interface.IntegrityGate.run', return_value=[]) as mock_integrity:
            
            results = run_gates(phase, plan, context)
            
            assert results["artifacts"] == ["Missing artifact"]
            assert results["tests"] == []
            assert results["docs"] == ["Docs not updated"]
            assert results["drift"] == []
            assert results["integrity"] == []
    
    def test_run_gates_exception_handling(self):
        """Test that exceptions in gates are handled gracefully."""
        phase = {}
        plan = {}
        context = {"traces_dir": "/path/to/traces"}
        
        with patch('lib.gate_interface.ArtifactsGate.run', side_effect=Exception("Gate failed")) as mock_artifacts, \
             patch('lib.gate_interface.TestsGate.run', return_value=[]) as mock_tests, \
             patch('lib.gate_interface.DocsGate.run', return_value=[]) as mock_docs, \
             patch('lib.gate_interface.DriftGate.run', return_value=[]) as mock_drift, \
             patch('lib.gate_interface.IntegrityGate.run', return_value=[]) as mock_integrity:
            
            results = run_gates(phase, plan, context)
            
            assert "artifacts" in results
            assert len(results["artifacts"]) == 1
            assert "Gate artifacts failed: Gate failed" in results["artifacts"][0]
