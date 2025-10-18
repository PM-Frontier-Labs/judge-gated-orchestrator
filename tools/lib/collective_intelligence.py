"""
Collective Intelligence System for Judge-Gated Protocol

This module provides file-based storage and retrieval of execution patterns,
enabling the protocol to learn from completed plans and improve future execution.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum


class PatternType(Enum):
    """Types of execution patterns"""
    SUCCESS = "success"
    FAILURE = "failure"
    ANTI_PATTERN = "anti_pattern"
    OPTIMIZATION = "optimization"
    INTEGRATION = "integration"


class PhaseOutcome(Enum):
    """Outcomes of phase execution"""
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIAL = "partial"
    BLOCKED = "blocked"


@dataclass
class ExecutionPattern:
    """Represents an execution pattern"""
    id: str
    pattern_type: PatternType
    phase_id: str
    description: str
    context: Dict[str, Any]
    success_factors: List[str]
    failure_factors: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    version: int = 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['pattern_type'] = self.pattern_type.value
        data['created_at'] = self.created_at.isoformat()
        data['updated_at'] = self.updated_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ExecutionPattern':
        """Create from dictionary"""
        data['pattern_type'] = PatternType(data['pattern_type'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        data['updated_at'] = datetime.fromisoformat(data['updated_at'])
        return cls(**data)


class CollectiveIntelligence:
    """Core collective intelligence system"""
    
    def __init__(self, repo_root: Union[str, Path] = "."):
        self.repo_root = Path(repo_root)
        self.patterns_dir = self.repo_root / ".repo" / "collective_intelligence"
        self.patterns_file = self.patterns_dir / "patterns.json"
        self._ensure_storage_exists()
    
    def _ensure_storage_exists(self) -> None:
        """Ensure storage directory and files exist"""
        self.patterns_dir.mkdir(parents=True, exist_ok=True)
        if not self.patterns_file.exists():
            self._initialize_storage()
    
    def _initialize_storage(self) -> None:
        """Initialize empty pattern storage"""
        initial_data = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "patterns": [],
            "metadata": {
                "total_patterns": 0,
                "last_updated": datetime.now().isoformat()
            }
        }
        with open(self.patterns_file, 'w') as f:
            json.dump(initial_data, f, indent=2)
    
    def store_pattern(self, pattern: ExecutionPattern) -> bool:
        """Store an execution pattern"""
        try:
            # Load existing patterns
            patterns_data = self._load_patterns_data()
            
            # Add new pattern
            patterns_data["patterns"].append(pattern.to_dict())
            patterns_data["metadata"]["total_patterns"] = len(patterns_data["patterns"])
            patterns_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save back to file
            self._save_patterns_data(patterns_data)
            return True
            
        except Exception as e:
            print(f"Error storing pattern: {e}")
            return False
    
    def retrieve_patterns(self, 
                         pattern_type: Optional[PatternType] = None,
                         phase_id: Optional[str] = None,
                         limit: Optional[int] = None) -> List[ExecutionPattern]:
        """Retrieve patterns with optional filtering"""
        try:
            patterns_data = self._load_patterns_data()
            patterns = []
            
            for pattern_dict in patterns_data["patterns"]:
                pattern = ExecutionPattern.from_dict(pattern_dict)
                
                # Apply filters
                if pattern_type and pattern.pattern_type != pattern_type:
                    continue
                if phase_id and pattern.phase_id != phase_id:
                    continue
                
                patterns.append(pattern)
            
            # Sort by updated_at (most recent first)
            patterns.sort(key=lambda p: p.updated_at, reverse=True)
            
            # Apply limit
            if limit is not None and limit >= 0:
                patterns = patterns[:limit]
            
            return patterns
            
        except Exception as e:
            print(f"Error retrieving patterns: {e}")
            return []
    
    def search_patterns(self, query: str, pattern_type: Optional[PatternType] = None) -> List[ExecutionPattern]:
        """Search patterns by description and context"""
        try:
            patterns_data = self._load_patterns_data()
            matching_patterns = []
            query_lower = query.lower()
            
            for pattern_dict in patterns_data["patterns"]:
                pattern = ExecutionPattern.from_dict(pattern_dict)
                
                # Apply pattern type filter
                if pattern_type and pattern.pattern_type != pattern_type:
                    continue
                
                # Search in description and context
                if (query_lower in pattern.description.lower() or
                    any(query_lower in str(value).lower() for value in pattern.context.values())):
                    matching_patterns.append(pattern)
            
            # Sort by relevance (simple: most recent first)
            matching_patterns.sort(key=lambda p: p.updated_at, reverse=True)
            return matching_patterns
            
        except Exception as e:
            print(f"Error searching patterns: {e}")
            return []
    
    def get_pattern_by_id(self, pattern_id: str) -> Optional[ExecutionPattern]:
        """Get a specific pattern by ID"""
        try:
            patterns_data = self._load_patterns_data()
            
            for pattern_dict in patterns_data["patterns"]:
                if pattern_dict["id"] == pattern_id:
                    return ExecutionPattern.from_dict(pattern_dict)
            
            return None
            
        except Exception as e:
            print(f"Error getting pattern by ID: {e}")
            return None
    
    def update_pattern(self, pattern_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing pattern"""
        try:
            patterns_data = self._load_patterns_data()
            
            for i, pattern_dict in enumerate(patterns_data["patterns"]):
                if pattern_dict["id"] == pattern_id:
                    # Update the pattern
                    pattern = ExecutionPattern.from_dict(pattern_dict)
                    for key, value in updates.items():
                        if hasattr(pattern, key):
                            setattr(pattern, key, value)
                    
                    pattern.updated_at = datetime.now()
                    pattern.version += 1
                    
                    patterns_data["patterns"][i] = pattern.to_dict()
                    patterns_data["metadata"]["last_updated"] = datetime.now().isoformat()
                    
                    self._save_patterns_data(patterns_data)
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error updating pattern: {e}")
            return False
    
    def delete_pattern(self, pattern_id: str) -> bool:
        """Delete a pattern by ID"""
        try:
            patterns_data = self._load_patterns_data()
            
            original_count = len(patterns_data["patterns"])
            patterns_data["patterns"] = [
                p for p in patterns_data["patterns"] 
                if p["id"] != pattern_id
            ]
            
            if len(patterns_data["patterns"]) < original_count:
                patterns_data["metadata"]["total_patterns"] = len(patterns_data["patterns"])
                patterns_data["metadata"]["last_updated"] = datetime.now().isoformat()
                self._save_patterns_data(patterns_data)
                return True
            
            return False
            
        except Exception as e:
            print(f"Error deleting pattern: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored patterns"""
        try:
            patterns_data = self._load_patterns_data()
            patterns = patterns_data["patterns"]
            
            stats = {
                "total_patterns": len(patterns),
                "by_type": {},
                "by_phase": {},
                "recent_patterns": 0
            }
            
            # Count by type and phase
            for pattern_dict in patterns:
                pattern_type = pattern_dict["pattern_type"]
                phase_id = pattern_dict["phase_id"]
                
                stats["by_type"][pattern_type] = stats["by_type"].get(pattern_type, 0) + 1
                stats["by_phase"][phase_id] = stats["by_phase"].get(phase_id, 0) + 1
                
                # Count recent patterns (last 7 days)
                updated_at = datetime.fromisoformat(pattern_dict["updated_at"])
                if (datetime.now() - updated_at).days <= 7:
                    stats["recent_patterns"] += 1
            
            return stats
            
        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {}
    
    def _load_patterns_data(self) -> Dict[str, Any]:
        """Load patterns data from file"""
        with open(self.patterns_file, 'r') as f:
            return json.load(f)
    
    def _save_patterns_data(self, data: Dict[str, Any]) -> None:
        """Save patterns data to file"""
        with open(self.patterns_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def backup_patterns(self, backup_path: Optional[Path] = None) -> bool:
        """Create a backup of patterns"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.patterns_dir / f"patterns_backup_{timestamp}.json"
            
            patterns_data = self._load_patterns_data()
            with open(backup_path, 'w') as f:
                json.dump(patterns_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_patterns(self, backup_path: Path) -> bool:
        """Restore patterns from backup"""
        try:
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            with open(self.patterns_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"Error restoring backup: {e}")
            return False
