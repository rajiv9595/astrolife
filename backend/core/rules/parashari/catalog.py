"""
Phase 5B — Parashari catalogue: builders, manifest, registry wiring,
deterministic evaluator (formation via custom evaluators, strength graded
separately, cancellation/mitigation via exceptions module).
"""
from __future__ import annotations
from typing import Dict, List, Optional

from ..evaluator import RuleEvaluator, EvaluationConfig
from ..registry import RuleRegistry
from ..enums import RuleCategory, RuleTradition
from . import raja_yoga, dhana_yoga, mahapurusha, major_yogas, parivartana, viparita, neecha_bhanga
from .exceptions import CANCELLATION_EVALUATORS, MITIGATION_EVALUATORS
from .strength import evaluate_yoga_strength


def _collect_formation_evaluators() -> Dict:
    ev: Dict = {}
    for mod in (raja_yoga, dhana_yoga, mahapurusha, major_yogas,
                parivartana, viparita, neecha_bhanga):
        ev.update(getattr(mod, "FORMATION_EVALUATORS", {}))
    return ev


FORMATION_EVALUATORS: Dict = _collect_formation_evaluators()


def build_parashari_catalog() -> List:
    return [
        # Raja (3)
        raja_yoga.build_raja_kendra_trikona(),
        raja_yoga.build_dharma_karmadhipati(),
        raja_yoga.build_yogakaraka_raja(),
        # Dhana (3)
        dhana_yoga.build_dhana_2_11(),
        dhana_yoga.build_dhana_5_9(),
        dhana_yoga.build_dhana_lagna(),
        # Mahapurusha (5)
        mahapurusha.build_ruchaka(),
        mahapurusha.build_bhadra(),
        mahapurusha.build_hamsa(),
        mahapurusha.build_malavya(),
        mahapurusha.build_sasa(),
        # Major (12)
        major_yogas.build_gaja_kesari(),
        major_yogas.build_budha_aditya(),
        major_yogas.build_chandra_mangala(),
        major_yogas.build_adhi(),
        major_yogas.build_lakshmi(),
        major_yogas.build_saraswati(),
        major_yogas.build_amala(),
        major_yogas.build_vasumati(),
        major_yogas.build_sunapha(),
        major_yogas.build_anapha(),
        major_yogas.build_durudhara(),
        major_yogas.build_kemadruma(),
        # Parivartana (3)
        parivartana.build_maha(),
        parivartana.build_khala(),
        parivartana.build_dainya(),
        # Viparita (3)
        viparita.build_harsha(),
        viparita.build_sarala(),
        viparita.build_vimala(),
        # Neecha bhanga (2)
        neecha_bhanga.build_neecha_bhanga(),
        neecha_bhanga.build_neecha_bhanga_raja(),
    ]


PARASHARI_RULE_IDS: List[str] = [r.metadata.rule_id for r in build_parashari_catalog()]


def get_parashari_rules() -> List:
    return build_parashari_catalog()


def create_parashari_evaluator() -> RuleEvaluator:
    custom = dict(FORMATION_EVALUATORS)
    custom.update(CANCELLATION_EVALUATORS)
    custom.update(MITIGATION_EVALUATORS)
    config = EvaluationConfig(
        evaluate_formation=True,
        evaluate_strength=False,  # graded separately via strength.py
        evaluate_activation=False,  # NOT_EVALUATED by design (no prediction yet)
        evaluate_cancellation=True,
        evaluate_mitigation=True,
        collect_evidence=True,
        collect_trace=False,
    )
    return RuleEvaluator(config=config, custom_evaluators=custom)


def _relevant_planets_from_result(result) -> List[str]:
    planets = []
    for e in result.evidence or []:
        subj = getattr(e, "subject", "") or ""
        for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
            if p in subj and p not in planets:
                planets.append(p)
    det_planets = []
    for e in result.evidence or []:
        details = getattr(e, "details", {}) or {}
        for key in ("lord1", "lord2", "lord"):
            if details.get(key) and details[key] not in det_planets:
                det_planets.append(details[key])
    for p in det_planets:
        if p not in planets:
            planets.append(p)
    return planets


def evaluate_parashari_by_id(rule_id: str, context, evaluator=None):
    evaluator = evaluator or create_parashari_evaluator()
    rules = {r.metadata.rule_id: r for r in build_parashari_catalog()}
    rule = rules.get(rule_id)
    if rule is None:
        return None
    result = evaluator.evaluate(rule, context)
    # graded strength (separate from formation)
    if str(result.formation_status) == "FormationStatus.FORMED" or \
            getattr(result.formation_status, "value", "") == "FORMED":
        planets = _relevant_planets_from_result(result)
        status, sev = evaluate_yoga_strength(context, planets, rule.metadata.name)
        result.strength_status = status
        result.evidence.extend(sev)
        result.relevant_planets = sorted(set(list(result.relevant_planets) + planets))
    return result


def evaluate_all_parashari(context, evaluator=None):
    evaluator = evaluator or create_parashari_evaluator()
    rules = build_parashari_catalog()
    out = []
    for rule in rules:
        result = evaluator.evaluate(rule, context)
        if getattr(result.formation_status, "value", str(result.formation_status)) == "FORMED":
            planets = _relevant_planets_from_result(result)
            status, sev = evaluate_yoga_strength(context, planets, rule.metadata.name)
            result.strength_status = status
            result.evidence.extend(sev)
            result.relevant_planets = sorted(set(list(result.relevant_planets) + planets))
        out.append(result)
    return out


def register_parashari_rules(registry: Optional[RuleRegistry] = None) -> int:
    registry = registry or RuleRegistry()
    n = 0
    for rule in build_parashari_catalog():
        try:
            if registry.register(rule, source="parashari_5b"):
                n += 1
        except ValueError:
            pass
    return n


def build_manifest() -> List[Dict]:
    items = []
    for r in build_parashari_catalog():
        m = r.metadata
        items.append({
            "rule_id": m.rule_id,
            "name": m.name,
            "category": m.category.value if hasattr(m.category, "value") else str(m.category),
            "tradition": m.tradition.value if hasattr(m.tradition, "value") else str(m.tradition),
            "method": m.provenance.method,
            "version": m.rule_version,
            "status": m.status.value if hasattr(m.status, "value") else str(m.status),
            "source": m.provenance.source_name,
            "source_reference": m.provenance.source_reference,
            "confidence": m.confidence.value if hasattr(m.confidence, "value") else str(m.confidence),
        })
    return items
