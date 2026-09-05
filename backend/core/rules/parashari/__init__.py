"""
Astrolife V2 — Phase 5B: Parashari Classical Yoga Engine.

Deterministic formation -> strength -> cancellation/mitigation -> evidence.
No AI, no astronomy, no Western aspects. Consumes RuleContext only.
"""
from .structural import (
    KENDRA_HOUSES, TRIKONA_HOUSES, DUSTHANA_HOUSES, UPACHAYA_HOUSES,
    SIGN_LORDS, NATURAL_BENEFICS, NATURAL_MALEFICS,
    house_of, sign_of, lord_of_house, houses_ruled_by,
    is_kendra_house, is_trikona_house, is_dusthana_house,
    sambandha_kind, parivartana_pairs, house_from_moon,
    is_kendra_from_moon, planets_in_house_from_moon,
)
from .strength import evaluate_yoga_strength
from .exceptions import (
    evaluate_cancellation, evaluate_mitigation,
    CANCELLATION_EVALUATORS, MITIGATION_EVALUATORS,
)
from .catalog import (
    build_parashari_catalog, get_parashari_rules, PARASHARI_RULE_IDS,
    register_parashari_rules, create_parashari_evaluator,
    evaluate_all_parashari, evaluate_parashari_by_id,
)
from .fixtures import make_synthetic_context, GOLDEN_BIRTH

__all__ = [
    "KENDRA_HOUSES", "TRIKONA_HOUSES", "DUSTHANA_HOUSES", "UPACHAYA_HOUSES",
    "SIGN_LORDS", "NATURAL_BENEFICS", "NATURAL_MALEFICS",
    "house_of", "sign_of", "lord_of_house", "houses_ruled_by",
    "is_kendra_house", "is_trikona_house", "is_dusthana_house",
    "sambandha_kind", "parivartana_pairs", "house_from_moon",
    "is_kendra_from_moon", "planets_in_house_from_moon",
    "evaluate_yoga_strength",
    "evaluate_cancellation", "evaluate_mitigation",
    "CANCELLATION_EVALUATORS", "MITIGATION_EVALUATORS",
    "build_parashari_catalog", "get_parashari_rules", "PARASHARI_RULE_IDS",
    "register_parashari_rules", "create_parashari_evaluator",
    "evaluate_all_parashari", "evaluate_parashari_by_id",
    "make_synthetic_context", "GOLDEN_BIRTH",
]

__version__ = "5.1.0"
