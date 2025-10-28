#!/usr/bin/env python3
"""
Gate Interface: Pluggable gate system for the Judge-Gated Protocol.

This module provides a clean interface for implementing gates, enabling
easier testing and future extensibility.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path


class GateInterface(ABC):
    """Abstract base class for all gates."""
    
    @abstractmethod
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """
        Run the gate and return list of issues (empty if passed).
        
        Args:
            phase: Phase configuration from plan.yaml
            plan: Complete plan configuration
            context: Execution context (changed_files, baseline_sha, etc.)
            
        Returns:
            List of issue messages (empty list if gate passed)
        """
        pass
    
    @abstractmethod
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """
        Check if this gate is enabled for the given phase.
        
        Args:
            phase: Phase configuration from plan.yaml
            
        Returns:
            True if gate should run, False otherwise
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the gate name (used for results tracking)."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Return human-readable description of what this gate does."""
        pass


class ArtifactsGate(GateInterface):
    """Gate that checks for required artifacts."""
    
    @property
    def name(self) -> str:
        return "artifacts"
    
    @property
    def description(self) -> str:
        return "Check for required artifacts"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """Artifacts gate is always enabled."""
        return True
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Check for required artifacts."""
        from .gates import check_artifacts
        return check_artifacts(phase)


class TestsGate(GateInterface):
    """Gate that checks test execution results."""
    
    @property
    def name(self) -> str:
        return "tests"
    
    @property
    def description(self) -> str:
        return "Check test execution results"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """Tests gate is always enabled."""
        return True
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Check test execution results."""
        traces_dir = context.get("traces_dir")
        if not traces_dir:
            return ["Tests gate: traces_dir not provided in context"]
        from .traces import check_gate_trace
        return check_gate_trace("tests", traces_dir, "Tests")


class LintGate(GateInterface):
    """Gate that checks linting results."""
    
    @property
    def name(self) -> str:
        return "lint"
    
    @property
    def description(self) -> str:
        return "Check linting results"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """Lint gate is enabled if must_pass is True."""
        lint_gate = phase.get("gates", {}).get("lint", {})
        return lint_gate.get("must_pass", False)
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Check linting results."""
        traces_dir = context.get("traces_dir")
        if not traces_dir:
            return ["Lint gate: traces_dir not provided in context"]
        from .traces import check_gate_trace
        return check_gate_trace("lint", traces_dir, "Linting")


class DocsGate(GateInterface):
    """Gate that checks documentation requirements."""
    
    @property
    def name(self) -> str:
        return "docs"
    
    @property
    def description(self) -> str:
        return "Check documentation requirements"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """Docs gate is always enabled."""
        return True
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Check documentation requirements."""
        from .gates import check_docs
        changed_files = context.get("changed_files", [])
        return check_docs(phase, changed_files)


class DriftGate(GateInterface):
    """Gate that checks for plan drift."""
    
    @property
    def name(self) -> str:
        return "drift"
    
    @property
    def description(self) -> str:
        return "Check for plan drift"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """Drift gate is enabled if drift gate is configured (disabled by default for simplified protocol)."""
        drift_gate = phase.get("gates", {}).get("drift", {})
        return drift_gate.get("enabled", False)  # Disabled by default
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Check for plan drift."""
        from .gates import check_drift
        baseline_sha = context.get("baseline_sha")
        repo_root = context.get("repo_root")
        return check_drift(phase, plan, baseline_sha, repo_root)


class LLMReviewGate(GateInterface):
    """Gate that performs LLM-based code review."""
    
    @property
    def name(self) -> str:
        return "llm_review"
    
    @property
    def description(self) -> str:
        return "LLM-based code review"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """LLM review gate is enabled if enabled is True."""
        llm_gate = phase.get("gates", {}).get("llm_review", {})
        return llm_gate.get("enabled", False)
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Perform LLM-based code review."""
        try:
            import sys
            from pathlib import Path
            tools_dir = Path(__file__).parent.parent
            sys.path.insert(0, str(tools_dir))
            from llm_judge import llm_code_review
            repo_root = context.get("repo_root")
            baseline_sha = context.get("baseline_sha")
            return llm_code_review(phase, repo_root, plan, baseline_sha)
        except ImportError:
            return ["LLM review enabled but llm_judge not available"]


class IntegrityGate(GateInterface):
    """Gate that checks protocol integrity."""
    
    @property
    def name(self) -> str:
        return "integrity"
    
    @property
    def description(self) -> str:
        return "Check protocol integrity"
    
    def is_enabled(self, phase: Dict[str, Any]) -> bool:
        """Integrity gate is always enabled."""
        return True
    
    def run(self, phase: Dict[str, Any], plan: Dict[str, Any], 
            context: Dict[str, Any]) -> List[str]:
        """Check protocol integrity."""
        from .protocol_guard import verify_protocol_lock
        repo_root = context.get("repo_root")
        baseline_sha = context.get("baseline_sha")
        phase_id = phase.get("id", "unknown")
        return verify_protocol_lock(repo_root, plan, phase_id, baseline_sha)


# Gate Registry
GATE_REGISTRY = {
    "artifacts": ArtifactsGate(),
    "tests": TestsGate(),
    "lint": LintGate(),
    "docs": DocsGate(),
    "drift": DriftGate(),
    "llm_review": LLMReviewGate(),
    "integrity": IntegrityGate(),
}


def get_gate(gate_name: str) -> Optional[GateInterface]:
    """Get a gate by name."""
    return GATE_REGISTRY.get(gate_name)


def get_all_gates() -> Dict[str, GateInterface]:
    """Get all registered gates."""
    return GATE_REGISTRY.copy()


def register_gate(gate_name: str, gate: GateInterface) -> None:
    """Register a new gate."""
    GATE_REGISTRY[gate_name] = gate


def run_gates(phase: Dict[str, Any], plan: Dict[str, Any], 
              context: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Run all enabled gates for a phase.
    
    Args:
        phase: Phase configuration
        plan: Complete plan configuration
        context: Execution context
        
    Returns:
        Dictionary mapping gate names to their issue lists
    """
    results = {}
    
    for gate_name, gate in GATE_REGISTRY.items():
        if gate.is_enabled(phase):
            try:
                issues = gate.run(phase, plan, context)
                results[gate_name] = issues
            except Exception as e:
                results[gate_name] = [f"Gate {gate_name} failed: {str(e)}"]
    
    return results
