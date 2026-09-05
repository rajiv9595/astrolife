"""
Rule Evaluator — Astrolife V2 Phase 5A

Deterministic rule evaluation engine. Evaluates RuleDefinition against RuleContext.
No astronomy calculations, no randomness, no datetime.now() - pure deterministic logic.
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .models import (
    RuleDefinition, RuleResult, RuleContextModel, Evidence, EvaluationResult,
    FormationStatus, StrengthStatus, ActivationStatus, CancellationStatus,
    MitigationStatus, ConfidenceLevel, Provenance, RuleEvaluationTrace,
    ConditionEvaluationResult
)
from .enums import RuleCategory, RuleTradition, EvidenceType
from .conditions import BaseCondition, ConditionRegistry
from .context import RuleContext


@dataclass
class EvaluationConfig:
    """Configuration for rule evaluation"""
    evaluate_formation: bool = True
    evaluate_strength: bool = True
    evaluate_activation: bool = True
    evaluate_cancellation: bool = True
    evaluate_mitigation: bool = True
    collect_evidence: bool = True
    collect_trace: bool = False


class RuleEvaluator:
    """
    Deterministic rule evaluator.
    
    Same inputs (RuleDefinition + RuleContext) ALWAYS produce identical outputs.
    No external dependencies, no randomness, no time-dependent logic.
    """
    
    def __init__(
        self,
        config: Optional[EvaluationConfig] = None,
        custom_evaluators: Optional[Dict[str, Callable]] = None
    ):
        self.config = config or EvaluationConfig()
        self.custom_evaluators = custom_evaluators or {}
        self._condition_registry = ConditionRegistry()
    
    def evaluate(self, rule: RuleDefinition, context: RuleContext) -> RuleResult:
        """
        Evaluate a single rule against context.
        Returns complete RuleResult with all statuses and evidence.
        """
        # Initialize result
        result = RuleResult(
            rule_id=rule.metadata.rule_id,
            rule_name=rule.metadata.name,
            category=rule.metadata.category,
            tradition=rule.metadata.tradition,
            method=rule.metadata.school_method,
            confidence=rule.metadata.confidence,
            provenance=rule.metadata.provenance,
            rule_version=rule.metadata.rule_version
        )
        
        trace = RuleEvaluationTrace(rule_id=rule.metadata.rule_id)
        
        # 1. Evaluate FORMATION conditions
        if self.config.evaluate_formation:
            formation_passed, formation_evidence, formation_trace = self._evaluate_conditions(
                rule.formation_conditions, context, "formation"
            )
            result.formation_status = FormationStatus.FORMED if formation_passed else FormationStatus.NOT_FORMED
            result.evidence.extend(formation_evidence)
            trace.formation_trace = formation_trace
            result.relevant_planets.extend(self._extract_planets_from_evidence(formation_evidence))
            result.relevant_houses.extend(self._extract_houses_from_evidence(formation_evidence))
            result.relevant_vargas.extend(self._extract_vargas_from_evidence(formation_evidence))
        
        # 2. Evaluate STRENGTH conditions (only if formed)
        if self.config.evaluate_strength and result.formation_status == FormationStatus.FORMED:
            strength_passed, strength_evidence, strength_trace = self._evaluate_conditions(
                rule.strength_conditions, context, "strength"
            )
            result.strength_status = StrengthStatus.STRONG if strength_passed else StrengthStatus.WEAK
            result.evidence.extend(strength_evidence)
            trace.strength_trace = strength_trace
        
        # 3. Evaluate ACTIVATION rules
        if self.config.evaluate_activation and result.formation_status == FormationStatus.FORMED:
            activation_status, activation_evidence, activation_trace = self._evaluate_activation(
                rule, context, result
            )
            result.activation_status = activation_status
            result.evidence.extend(activation_evidence)
            trace.activation_trace = activation_trace
        
        # 4. Evaluate CANCELLATION rules
        if self.config.evaluate_cancellation and result.formation_status == FormationStatus.FORMED:
            cancellation_status, cancellation_evidence, cancellation_trace = self._evaluate_cancellation(
                rule, context, result
            )
            result.cancellation_status = cancellation_status
            result.evidence.extend(cancellation_evidence)
            trace.cancellation_trace = cancellation_trace
        
        # 5. Evaluate MITIGATION rules
        if self.config.evaluate_mitigation and result.formation_status == FormationStatus.FORMED:
            mitigation_status, mitigation_evidence, mitigation_trace = self._evaluate_mitigation(
                rule, context, result
            )
            result.mitigation_status = mitigation_status
            result.evidence.extend(mitigation_evidence)
            trace.mitigation_trace = mitigation_trace
        
        # Deduplicate evidence
        result.evidence = self._deduplicate_evidence(result.evidence)
        result.relevant_planets = list(set(result.relevant_planets))
        result.relevant_houses = list(set(result.relevant_houses))
        result.relevant_vargas = list(set(result.relevant_vargas))
        
        return result
    
    def evaluate_all(self, rules: List[RuleDefinition], context: RuleContext) -> EvaluationResult:
        """Evaluate multiple rules against context"""
        results = []
        for rule in rules:
            if not rule.metadata.enabled:
                continue
            result = self.evaluate(rule, context)
            results.append(result)
        
        # Build summary
        formed = sum(1 for r in results if r.formation_status == FormationStatus.FORMED)
        active = sum(1 for r in results if r.activation_status == ActivationStatus.ACTIVE)
        cancelled = sum(1 for r in results if r.cancellation_status == CancellationStatus.FULL)
        mitigated = sum(1 for r in results if r.mitigation_status != MitigationStatus.NONE)
        
        return EvaluationResult(
            rule_results=results,
            total_rules=len(results),
            formed_count=formed,
            active_count=active,
            cancelled_count=cancelled,
            mitigated_count=mitigated
        )
    
    def _evaluate_conditions(
        self,
        conditions: List[Any],
        context: RuleContext,
        phase: str
    ) -> tuple[bool, List[Evidence], List[ConditionEvaluationResult]]:
        """Evaluate a list of conditions (can be Condition models or BaseCondition objects)"""
        all_passed = True
        all_evidence = []
        all_traces = []
        
        for cond in conditions:
            if isinstance(cond, BaseCondition):
                trace = cond.evaluate(context)
                all_traces.append(trace)
                if not trace.passed:
                    all_passed = False
                if self.config.collect_evidence:
                    all_evidence.extend(trace.evidence)
            elif hasattr(cond, 'type') and hasattr(cond, 'params'):
                # Handle Pydantic Condition model
                trace = self._evaluate_pydantic_condition(cond, context, phase)
                all_traces.append(trace)
                if not trace.passed:
                    all_passed = False
                if self.config.collect_evidence:
                    all_evidence.extend(trace.evidence)
        
        return all_passed, all_evidence, all_traces
    
    def _evaluate_pydantic_condition(
        self,
        cond: Any,
        context: RuleContext,
        phase: str
    ) -> ConditionEvaluationResult:
        """Evaluate a Pydantic Condition model"""
        cond_type = cond.type
        params = cond.params
        cond_id = f"{phase}_{cond_type}_{hash(str(params))}"
        
        # Try to get from registry
        factory = self._condition_registry.get(cond_type)
        if factory:
            base_cond = factory(condition_id=cond_id, **params)
            return base_cond.evaluate(context)
        
        # Try custom evaluator
        if cond_type in self.custom_evaluators:
            evaluator = self.custom_evaluators[cond_type]
            passed, evidence = evaluator(context, params)
            return ConditionEvaluationResult(
                condition_id=cond_id,
                condition_type=cond_type,
                passed=passed,
                evidence=evidence
            )
        
        # Unknown condition - fail
        return ConditionEvaluationResult(
            condition_id=cond_id,
            condition_type=cond_type,
            passed=False,
            evidence=[Evidence(
                evidence_type=EvidenceType.CUSTOM,
                subject="Unknown Condition",
                value=cond_type,
                expected="Known condition type",
                actual=f"Unknown: {cond_type}",
                source="RuleEvaluator",
                significance=f"Condition type '{cond_type}' not registered"
            )]
        )
    
    def _evaluate_activation(
        self,
        rule: RuleDefinition,
        context: RuleContext,
        result: RuleResult
    ) -> tuple[ActivationStatus, List[Evidence], List[ConditionEvaluationResult]]:
        """Evaluate activation rules (Dasha, Transit, etc.)"""
        if not rule.activation_rules:
            return ActivationStatus.NOT_EVALUATED, [], []
        
        all_passed = True
        all_evidence = []
        all_traces = []
        
        for act_rule in rule.activation_rules:
            evaluator_name = act_rule.evaluator or f"activation_{act_rule.rule_id}"
            
            if evaluator_name in self.custom_evaluators:
                evaluator = self.custom_evaluators[evaluator_name]
                passed, evidence = evaluator(context, result, act_rule.params if hasattr(act_rule, 'params') else {})
                trace = ConditionEvaluationResult(
                    condition_id=evaluator_name,
                    condition_type="ActivationRule",
                    passed=passed,
                    evidence=evidence
                )
                all_traces.append(trace)
                if not passed:
                    all_passed = False
                all_evidence.extend(evidence)
            else:
                # Default: check if Dasha lord matches relevant planets
                passed, evidence = self._default_activation_check(context, result, act_rule)
                trace = ConditionEvaluationResult(
                    condition_id=evaluator_name,
                    condition_type="ActivationRule",
                    passed=passed,
                    evidence=evidence
                )
                all_traces.append(trace)
                if not passed:
                    all_passed = False
                all_evidence.extend(evidence)
        
        if all_passed:
            return ActivationStatus.ACTIVE, all_evidence, all_traces
        else:
            return ActivationStatus.INACTIVE, all_evidence, all_traces
    
    def _default_activation_check(
        self,
        context: RuleContext,
        result: RuleResult,
        act_rule: Any
    ) -> tuple[bool, List[Evidence]]:
        """Default activation: check if relevant planet is in Dasha"""
        mahadasha = context.get_current_mahadasha()
        antardasha = context.get_current_antardasha()
        
        relevant_in_dasha = any(
            p in (mahadasha, antardasha) for p in result.relevant_planets
        )
        
        evidence = [Evidence(
            evidence_type=EvidenceType.DASHA_PERIOD,
            subject="Dasha Activation",
            value={"mahadasha": mahadasha, "antardasha": antardasha},
            expected="Relevant planet in Dasha",
            actual={"relevant_planets": result.relevant_planets, "in_dasha": relevant_in_dasha},
            source="DynamicState",
            significance=f"Dasha: {mahadasha}-{antardasha}, Relevant: {result.relevant_planets}, Match: {relevant_in_dasha}"
        )]
        
        return relevant_in_dasha, evidence
    
    def _evaluate_cancellation(
        self,
        rule: RuleDefinition,
        context: RuleContext,
        result: RuleResult
    ) -> tuple[CancellationStatus, List[Evidence], List[ConditionEvaluationResult]]:
        """Evaluate cancellation rules"""
        if not rule.cancellation_rules:
            return CancellationStatus.NONE, [], []
        
        full_cancelled = False
        partial_cancelled = False
        all_evidence = []
        all_traces = []
        
        for cancel_rule in rule.cancellation_rules:
            evaluator_name = cancel_rule.evaluator or f"cancellation_{cancel_rule.rule_id}"
            
            if evaluator_name in self.custom_evaluators:
                evaluator = self.custom_evaluators[evaluator_name]
                passed, evidence = evaluator(context, result, cancel_rule)
                trace = ConditionEvaluationResult(
                    condition_id=evaluator_name,
                    condition_type="CancellationRule",
                    passed=passed,
                    evidence=evidence
                )
                all_traces.append(trace)
                if passed:
                    if cancel_rule.is_partial:
                        partial_cancelled = True
                    else:
                        full_cancelled = True
                all_evidence.extend(evidence)
        
        if full_cancelled:
            return CancellationStatus.FULL, all_evidence, all_traces
        elif partial_cancelled:
            return CancellationStatus.PARTIAL, all_evidence, all_traces
        return CancellationStatus.NONE, all_evidence, all_traces
    
    def _evaluate_mitigation(
        self,
        rule: RuleDefinition,
        context: RuleContext,
        result: RuleResult
    ) -> tuple[MitigationStatus, List[Evidence], List[ConditionEvaluationResult]]:
        """Evaluate mitigation rules"""
        if not rule.mitigation_rules:
            return MitigationStatus.NONE, [], []
        
        significant = False
        partial = False
        all_evidence = []
        all_traces = []
        
        for mit_rule in rule.mitigation_rules:
            evaluator_name = mit_rule.evaluator or f"mitigation_{mit_rule.rule_id}"
            
            if evaluator_name in self.custom_evaluators:
                evaluator = self.custom_evaluators[evaluator_name]
                passed, evidence = evaluator(context, result, mit_rule)
                trace = ConditionEvaluationResult(
                    condition_id=evaluator_name,
                    condition_type="MitigationRule",
                    passed=passed,
                    evidence=evidence
                )
                all_traces.append(trace)
                if passed:
                    if mit_rule.strength_impact == "significant":
                        significant = True
                    else:
                        partial = True
                all_evidence.extend(evidence)
        
        if significant:
            return MitigationStatus.SIGNIFICANT, all_evidence, all_traces
        elif partial:
            return MitigationStatus.PARTIAL, all_evidence, all_traces
        return MitigationStatus.NONE, all_evidence, all_traces
    
    def _extract_planets_from_evidence(self, evidence: List[Evidence]) -> List[str]:
        planets = []
        for e in evidence:
            if e.subject:
                # Extract planet names from subject
                for planet in ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"]:
                    if planet in e.subject:
                        planets.append(planet)
        return planets
    
    def _extract_houses_from_evidence(self, evidence: List[Evidence]) -> List[int]:
        houses = []
        for e in evidence:
            if e.evidence_type in (EvidenceType.PLANET_IN_HOUSE, EvidenceType.HOUSE_LORD_POSITION):
                if isinstance(e.value, int) and 1 <= e.value <= 12:
                    houses.append(e.value)
                if isinstance(e.expected, int) and 1 <= e.expected <= 12:
                    houses.append(e.expected)
        return houses
    
    def _extract_vargas_from_evidence(self, evidence: List[Evidence]) -> List[int]:
        vargas = []
        for e in evidence:
            if e.evidence_type == EvidenceType.VARGA_POSITION and "D" in str(e.subject):
                try:
                    varga_num = int(e.subject.split("D")[1].split("_")[0].split(" ")[0])
                    if 1 <= varga_num <= 60:
                        vargas.append(varga_num)
                except:
                    pass
        return vargas
    
    def _deduplicate_evidence(self, evidence: List[Evidence]) -> List[Evidence]:
        seen = set()
        unique = []
        for e in evidence:
            key = (e.evidence_type, e.subject, str(e.value))
            if key not in seen:
                seen.add(key)
                unique.append(e)
        return unique


def create_default_evaluator() -> RuleEvaluator:
    """Create evaluator with default activation/cancellation/mitigation evaluators"""
    from .activation import DefaultActivationEvaluator
    from .cancellation import DefaultCancellationEvaluator
    from .mitigation import DefaultMitigationEvaluator
    
    custom = {
        "default_activation": DefaultActivationEvaluator.evaluate,
        "default_cancellation": DefaultCancellationEvaluator.evaluate,
        "default_mitigation": DefaultMitigationEvaluator.evaluate,
    }
    
    return RuleEvaluator(custom_evaluators=custom)