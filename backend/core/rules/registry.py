"""
Rule Registry — Astrolife V2 Phase 5A

Central registry for rule definitions with versioning, tradition separation,
and deterministic evaluation.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from threading import RLock

from .models import RuleDefinition, RuleResult, RuleContextModel, EvaluationResult, Provenance
from .enums import RuleCategory, RuleTradition, RuleStatus
from .evaluator import RuleEvaluator, create_default_evaluator
from .context import RuleContext


@dataclass
class RegistryEntry:
    """Registry entry with metadata"""
    rule: RuleDefinition
    registered_at: str
    source: str = "manual"


class RuleRegistry:
    """
    Central rule registry with thread-safe operations.
    
    Features:
    - Unique rule IDs with versioning
    - Category and tradition indexing
    - Duplicate detection
    - Deterministic evaluation
    """
    
    def __init__(self):
        self._rules: Dict[str, RegistryEntry] = {}  # rule_id -> entry
        self._by_category: Dict[RuleCategory, List[str]] = {}
        self._by_tradition: Dict[RuleTradition, List[str]] = {}
        self._by_id_version: Dict[str, RegistryEntry] = {}  # "rule_id@v" -> entry
        self._lock = RLock()
        self._evaluator = create_default_evaluator()
    
    def register(self, rule: RuleDefinition, source: str = "manual") -> bool:
        """
        Register a rule.
        
        Returns True if registered, False if duplicate ID+version exists.
        Raises ValueError if rule_id exists with different version.
        """
        with self._lock:
            rule_id = rule.metadata.rule_id
            version = rule.metadata.rule_version
            key = f"{rule_id}@{version}"
            
            # Check for exact duplicate
            if key in self._by_id_version:
                existing = self._by_id_version[key]
                if existing.rule.metadata.name == rule.metadata.name:
                    return False  # Exact duplicate
                else:
                    raise ValueError(f"Rule ID '{rule_id}' version '{version}' already exists with different definition")
            
            # Check for same ID different version
            existing_versions = [k for k in self._by_id_version.keys() if k.startswith(f"{rule_id}@")]
            if existing_versions:
                # Allow new version, but warn
                pass
            
            # Create entry
            from datetime import datetime
            entry = RegistryEntry(
                rule=rule,
                registered_at=datetime.utcnow().isoformat(),
                source=source
            )
            
            # Store
            self._rules[rule_id] = entry
            self._by_id_version[key] = entry
            
            # Index by category
            cat = rule.metadata.category
            if cat not in self._by_category:
                self._by_category[cat] = []
            if rule_id not in self._by_category[cat]:
                self._by_category[cat].append(rule_id)
            
            # Index by tradition
            trad = rule.metadata.tradition
            if trad not in self._by_tradition:
                self._by_tradition[trad] = []
            if rule_id not in self._by_tradition[trad]:
                self._by_tradition[trad].append(rule_id)
            
            return True
    
    def get(self, rule_id: str, version: str = None) -> Optional[RuleDefinition]:
        """Get rule by ID (latest version if version not specified)"""
        with self._lock:
            if version:
                key = f"{rule_id}@{version}"
                entry = self._by_id_version.get(key)
                return entry.rule if entry else None
            
            # Get latest version
            versions = [k for k in self._by_id_version.keys() if k.startswith(f"{rule_id}@")]
            if not versions:
                return None
            
            # Sort by version (semantic versioning)
            latest_key = max(versions, key=lambda k: self._parse_version(k.split("@")[1]))
            return self._by_id_version[latest_key].rule
    
    def _parse_version(self, version: str) -> tuple:
        """Parse semantic version for comparison"""
        try:
            parts = version.split(".")
            return tuple(int(p) for p in parts)
        except:
            return (0, 0, 0)
    
    def get_latest_version(self, rule_id: str) -> Optional[str]:
        """Get latest version string for a rule ID"""
        with self._lock:
            versions = [k for k in self._by_id_version.keys() if k.startswith(f"{rule_id}@")]
            if not versions:
                return None
            latest_key = max(versions, key=lambda k: self._parse_version(k.split("@")[1]))
            return latest_key.split("@")[1]
    
    def list_by_category(self, category: RuleCategory) -> List[RuleDefinition]:
        """List all rules in a category (latest versions)"""
        with self._lock:
            rule_ids = self._by_category.get(category, [])
            return [self.get(rid) for rid in rule_ids if self.get(rid)]
    
    def list_by_tradition(self, tradition: RuleTradition) -> List[RuleDefinition]:
        """List all rules in a tradition (latest versions)"""
        with self._lock:
            rule_ids = self._by_tradition.get(tradition, [])
            return [self.get(rid) for rid in rule_ids if self.get(rid)]
    
    def list_all(self) -> List[RuleDefinition]:
        """List all rules (latest versions)"""
        with self._lock:
            return [entry.rule for entry in self._rules.values()]
    
    def list_all_versions(self) -> List[RuleDefinition]:
        """List all rule versions"""
        with self._lock:
            return [entry.rule for entry in self._by_id_version.values()]
    
    def evaluate(self, rule_id: str, context: RuleContext, version: str = None) -> Optional[RuleResult]:
        """Evaluate a single rule by ID"""
        rule = self.get(rule_id, version)
        if not rule:
            return None
        return self._evaluator.evaluate(rule, context)
    
    def evaluate_all(self, context: RuleContext) -> EvaluationResult:
        """Evaluate all registered rules"""
        rules = self.list_all()
        return self._evaluator.evaluate_all(rules, context)
    
    def evaluate_by_category(self, category: RuleCategory, context: RuleContext) -> EvaluationResult:
        """Evaluate all rules in a category"""
        rules = self.list_by_category(category)
        return self._evaluator.evaluate_all(rules, context)
    
    def evaluate_by_tradition(self, tradition: RuleTradition, context: RuleContext) -> EvaluationResult:
        """Evaluate all rules in a tradition"""
        rules = self.list_by_tradition(tradition)
        return self._evaluator.evaluate_all(rules, context)
    
    def unregister(self, rule_id: str, version: str = None) -> bool:
        """Unregister a rule"""
        with self._lock:
            if version:
                key = f"{rule_id}@{version}"
                if key not in self._by_id_version:
                    return False
                entry = self._by_id_version.pop(key)
            else:
                if rule_id not in self._rules:
                    return False
                entry = self._rules.pop(rule_id)
                # Remove all versions
                keys_to_remove = [k for k in self._by_id_version.keys() if k.startswith(f"{rule_id}@")]
                for k in keys_to_remove:
                    self._by_id_version.pop(k)
            
            # Update indices
            cat = entry.rule.metadata.category
            if cat in self._by_category and rule_id in self._by_category[cat]:
                self._by_category[cat].remove(rule_id)
            
            trad = entry.rule.metadata.tradition
            if trad in self._by_tradition and rule_id in self._by_tradition[trad]:
                self._by_tradition[trad].remove(rule_id)
            
            return True
    
    def clear(self):
        """Clear all rules"""
        with self._lock:
            self._rules.clear()
            self._by_category.clear()
            self._by_tradition.clear()
            self._by_id_version.clear()
    
    def count(self) -> int:
        return len(self._rules)
    
    def count_versions(self) -> int:
        return len(self._by_id_version)
    
    def get_evaluator(self) -> RuleEvaluator:
        return self._evaluator
    
    def set_evaluator(self, evaluator: RuleEvaluator):
        self._evaluator = evaluator


# Global registry instance
_global_registry: Optional[RuleRegistry] = None


def get_registry() -> RuleRegistry:
    """Get global registry instance (singleton)"""
    global _global_registry
    if _global_registry is None:
        _global_registry = RuleRegistry()
    return _global_registry


def set_registry(registry: RuleRegistry):
    """Set global registry instance"""
    global _global_registry
    _global_registry = registry