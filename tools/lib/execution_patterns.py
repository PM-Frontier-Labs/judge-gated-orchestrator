"""
Execution Patterns Management for Judge-Gated Protocol

This module provides high-level pattern management and analysis capabilities
for the collective intelligence system.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from .collective_intelligence import (
    CollectiveIntelligence, ExecutionPattern, PatternType, PhaseOutcome
)


class ExecutionPatternManager:
    """High-level manager for execution patterns"""
    
    def __init__(self, repo_root: Union[str, Path] = "."):
        self.ci = CollectiveIntelligence(repo_root)
    
    def record_phase_success(self, 
                           phase_id: str,
                           description: str,
                           success_factors: List[str],
                           context: Dict[str, Any],
                           recommendations: Optional[List[str]] = None) -> str:
        """Record a successful phase execution"""
        pattern_id = f"success_{phase_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pattern = ExecutionPattern(
            id=pattern_id,
            pattern_type=PatternType.SUCCESS,
            phase_id=phase_id,
            description=description,
            context=context,
            success_factors=success_factors,
            failure_factors=[],
            recommendations=recommendations or [],
            metadata={
                "outcome": PhaseOutcome.APPROVED.value,
                "recorded_at": datetime.now().isoformat(),
                "source": "phase_execution"
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if self.ci.store_pattern(pattern):
            return pattern_id
        return ""
    
    def record_phase_failure(self,
                           phase_id: str,
                           description: str,
                           failure_factors: List[str],
                           context: Dict[str, Any],
                           recommendations: Optional[List[str]] = None) -> str:
        """Record a failed phase execution"""
        pattern_id = f"failure_{phase_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pattern = ExecutionPattern(
            id=pattern_id,
            pattern_type=PatternType.FAILURE,
            phase_id=phase_id,
            description=description,
            context=context,
            success_factors=[],
            failure_factors=failure_factors,
            recommendations=recommendations or [],
            metadata={
                "outcome": PhaseOutcome.REJECTED.value,
                "recorded_at": datetime.now().isoformat(),
                "source": "phase_execution"
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if self.ci.store_pattern(pattern):
            return pattern_id
        return ""
    
    def record_anti_pattern(self,
                          phase_id: str,
                          description: str,
                          anti_pattern_factors: List[str],
                          context: Dict[str, Any],
                          recommendations: Optional[List[str]] = None) -> str:
        """Record an anti-pattern to avoid"""
        pattern_id = f"antipattern_{phase_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        pattern = ExecutionPattern(
            id=pattern_id,
            pattern_type=PatternType.ANTI_PATTERN,
            phase_id=phase_id,
            description=description,
            context=context,
            success_factors=[],
            failure_factors=anti_pattern_factors,
            recommendations=recommendations or [],
            metadata={
                "outcome": PhaseOutcome.BLOCKED.value,
                "recorded_at": datetime.now().isoformat(),
                "source": "pattern_analysis"
            },
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        if self.ci.store_pattern(pattern):
            return pattern_id
        return ""
    
    def get_phase_recommendations(self, phase_id: str) -> Dict[str, Any]:
        """Get recommendations for a specific phase based on historical patterns"""
        success_patterns = self.ci.retrieve_patterns(
            pattern_type=PatternType.SUCCESS,
            phase_id=phase_id
        )
        
        failure_patterns = self.ci.retrieve_patterns(
            pattern_type=PatternType.FAILURE,
            phase_id=phase_id
        )
        
        anti_patterns = self.ci.retrieve_patterns(
            pattern_type=PatternType.ANTI_PATTERN,
            phase_id=phase_id
        )
        
        recommendations = {
            "phase_id": phase_id,
            "success_patterns": len(success_patterns),
            "failure_patterns": len(failure_patterns),
            "anti_patterns": len(anti_patterns),
            "success_factors": [],
            "failure_factors": [],
            "recommendations": [],
            "patterns": []
        }
        
        # Collect success factors
        for pattern in success_patterns:
            recommendations["success_factors"].extend(pattern.success_factors)
            recommendations["recommendations"].extend(pattern.recommendations)
            recommendations["patterns"].append({
                "id": pattern.id,
                "type": "success",
                "description": pattern.description,
                "factors": pattern.success_factors
            })
        
        # Collect failure factors
        for pattern in failure_patterns:
            recommendations["failure_factors"].extend(pattern.failure_factors)
            recommendations["recommendations"].extend(pattern.recommendations)
            recommendations["patterns"].append({
                "id": pattern.id,
                "type": "failure",
                "description": pattern.description,
                "factors": pattern.failure_factors
            })
        
        # Collect anti-patterns
        for pattern in anti_patterns:
            recommendations["failure_factors"].extend(pattern.failure_factors)
            recommendations["recommendations"].extend(pattern.recommendations)
            recommendations["patterns"].append({
                "id": pattern.id,
                "type": "anti_pattern",
                "description": pattern.description,
                "factors": pattern.failure_factors
            })
        
        # Remove duplicates and limit
        recommendations["success_factors"] = list(set(recommendations["success_factors"]))[:10]
        recommendations["failure_factors"] = list(set(recommendations["failure_factors"]))[:10]
        recommendations["recommendations"] = list(set(recommendations["recommendations"]))[:15]
        
        return recommendations
    
    def get_similar_phase_patterns(self, phase_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get patterns from similar phases"""
        # Simple similarity based on phase ID prefix (e.g., P01, P02, etc.)
        phase_prefix = phase_id.split('-')[0] if '-' in phase_id else phase_id
        
        all_patterns = self.ci.retrieve_patterns()
        similar_patterns = []
        
        for pattern in all_patterns:
            pattern_prefix = pattern.phase_id.split('-')[0] if '-' in pattern.phase_id else pattern.phase_id
            if pattern_prefix == phase_prefix and pattern.phase_id != phase_id:
                similar_patterns.append({
                    "id": pattern.id,
                    "phase_id": pattern.phase_id,
                    "type": pattern.pattern_type.value,
                    "description": pattern.description,
                    "success_factors": pattern.success_factors,
                    "failure_factors": pattern.failure_factors,
                    "recommendations": pattern.recommendations
                })
        
        return similar_patterns[:limit]
    
    def analyze_execution_trends(self) -> Dict[str, Any]:
        """Analyze trends across all execution patterns"""
        all_patterns = self.ci.retrieve_patterns()
        
        analysis = {
            "total_patterns": len(all_patterns),
            "by_type": {},
            "by_phase": {},
            "success_rate": 0,
            "common_success_factors": [],
            "common_failure_factors": [],
            "trends": {}
        }
        
        success_count = 0
        success_factors = []
        failure_factors = []
        
        for pattern in all_patterns:
            # Count by type
            pattern_type = pattern.pattern_type.value
            analysis["by_type"][pattern_type] = analysis["by_type"].get(pattern_type, 0) + 1
            
            # Count by phase
            analysis["by_phase"][pattern.phase_id] = analysis["by_phase"].get(pattern.phase_id, 0) + 1
            
            # Count successes
            if pattern.pattern_type == PatternType.SUCCESS:
                success_count += 1
                success_factors.extend(pattern.success_factors)
            else:
                failure_factors.extend(pattern.failure_factors)
        
        # Calculate success rate
        if all_patterns:
            analysis["success_rate"] = success_count / len(all_patterns)
        
        # Find common factors
        from collections import Counter
        success_counter = Counter(success_factors)
        failure_counter = Counter(failure_factors)
        
        analysis["common_success_factors"] = [factor for factor, count in success_counter.most_common(10)]
        analysis["common_failure_factors"] = [factor for factor, count in failure_counter.most_common(10)]
        
        return analysis
    
    def export_patterns(self, export_path: Path, format: str = "json") -> bool:
        """Export patterns to external file"""
        try:
            patterns_data = self.ci._load_patterns_data()
            
            if format.lower() == "json":
                with open(export_path, 'w') as f:
                    json.dump(patterns_data, f, indent=2)
            else:
                return False
            
            return True
            
        except Exception as e:
            print(f"Error exporting patterns: {e}")
            return False
    
    def import_patterns(self, import_path: Path) -> bool:
        """Import patterns from external file"""
        try:
            with open(import_path, 'r') as f:
                imported_data = json.load(f)
            
            # Validate imported data structure
            if "patterns" not in imported_data:
                return False
            
            # Merge with existing patterns
            existing_data = self.ci._load_patterns_data()
            existing_ids = {p["id"] for p in existing_data["patterns"]}
            
            new_patterns = []
            for pattern in imported_data["patterns"]:
                if pattern["id"] not in existing_ids:
                    new_patterns.append(pattern)
            
            existing_data["patterns"].extend(new_patterns)
            existing_data["metadata"]["total_patterns"] = len(existing_data["patterns"])
            existing_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            self.ci._save_patterns_data(existing_data)
            return True
            
        except Exception as e:
            print(f"Error importing patterns: {e}")
            return False
    
    def cleanup_old_patterns(self, days_old: int = 90) -> int:
        """Remove patterns older than specified days"""
        try:
            patterns_data = self.ci._load_patterns_data()
            cutoff_date = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            original_count = len(patterns_data["patterns"])
            patterns_data["patterns"] = [
                p for p in patterns_data["patterns"]
                if datetime.fromisoformat(p["created_at"]).timestamp() > cutoff_date
            ]
            
            removed_count = original_count - len(patterns_data["patterns"])
            
            if removed_count > 0:
                patterns_data["metadata"]["total_patterns"] = len(patterns_data["patterns"])
                patterns_data["metadata"]["last_updated"] = datetime.now().isoformat()
                self.ci._save_patterns_data(patterns_data)
            
            return removed_count
            
        except Exception as e:
            print(f"Error cleaning up old patterns: {e}")
            return 0
