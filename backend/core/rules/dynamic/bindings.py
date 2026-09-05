"""
Phase 6B — primitive bindings to canonical fact paths.

Every 6A primitive maps to explicit resolver paths (templates instantiated
with params). `required_paths(op, params)` drives declared-dependency
validation: a rule must declare every path its trees can touch. No primitive
computes astronomy; all values are canonical reads.
"""
from __future__ import annotations

from typing import Any, Dict, List

_ALL_PLANETS = ["Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus",
                "Saturn", "Rahu", "Ketu"]


def required_paths(op: str, params: Dict[str, Any]) -> List[str]:
    P = params
    if op == "planet_in_sign":
        return [f"natal.{P['planet']}.sign"]
    if op == "planet_in_house":
        return [f"natal.{P['planet']}.house"]
    if op == "planet_in_varga_sign":
        return [f"varga.{P['varga']}.{P['planet']}"]
    if op == "planet_owns_house":
        return [f"houses.{P['house']}.lord"]
    if op == "planets_conjunct":
        return [f"natal.{P['a']}.sign", f"natal.{P['b']}.sign"]
    if op == "planets_aspect":
        return [f"aspects.{P['a']}"]
    if op == "rashi_drishti":
        return ["jaimini.drishti"]
    if op == "karaka_equals":
        return [f"jaimini.karaka.{P['karaka']}"]
    if op == "pada_equals":
        return [f"jaimini.pada.{P['house']}"]
    if op in ("planet_exalted", "planet_debilitated", "planet_in_own_sign",
              "planet_in_moolatrikona"):
        return [f"strength.dignity.{P['planet']}"]
    if op in ("house_is_kendra", "house_is_trikona"):
        return []
    if op == "lord_in_house":
        # The lord is data-dependent: declare the lordship plus every
        # planet-house path the primitive may touch (explicit, no glob).
        return [f"houses.{P['house']}.lord"] + [f"natal.{pl}.house" for pl in _ALL_PLANETS]
    if op == "lord_of_house":
        return [f"houses.{P['house']}.lord"]
    if op == "dasha_active":
        return [f"dasha.{P['system']}.active_sign"]
    if op == "transit_in_sign":
        return [f"transit.{P['planet']}.sign"]
    if op == "transit_conjunct_natal":
        return [f"transit.{P['transit_planet']}.sign", f"natal.{P['natal_planet']}.sign"]
    if op == "strength_threshold":
        return [f"strength.{P['metric']}.{P['planet']}"]
    if op == "rule_formed":
        return [f"rule:{P['rule_id']}"]
    return []


PRIMITIVE_BINDINGS: Dict[str, str] = {
    "planet_in_sign": "natal.{planet}.sign",
    "planet_in_house": "natal.{planet}.house",
    "planet_in_varga_sign": "varga.{varga}.{planet}",
    "planet_owns_house": "houses.{house}.lord",
    "planets_conjunct": "natal.{a}.sign + natal.{b}.sign",
    "planets_aspect": "aspects.{a}",
    "rashi_drishti": "jaimini.drishti",
    "karaka_equals": "jaimini.karaka.{karaka}",
    "pada_equals": "jaimini.pada.{house}",
    "planet_exalted": "strength.dignity.{planet}",
    "planet_debilitated": "strength.dignity.{planet}",
    "planet_in_own_sign": "strength.dignity.{planet}",
    "planet_in_moolatrikona": "strength.dignity.{planet}",
    "house_is_kendra": "(pure set)",
    "house_is_trikona": "(pure set)",
    "lord_in_house": "houses.{house}.lord + natal lord house",
    "lord_of_house": "houses.{house}.lord",
    "dasha_active": "dasha.{system}.active_sign",
    "transit_in_sign": "transit.{planet}.sign",
    "transit_conjunct_natal": "transit.{transit_planet}.sign + natal.{natal_planet}.sign",
    "strength_threshold": "strength.{metric}.{planet}",
    "rule_formed": "rule:{rule_id}",
}
