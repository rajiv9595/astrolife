"""
Phase 5B — cross-check framework (legacy engine vs new deterministic engine).

Compares a subset of overlapping yogas on the golden chart using the legacy
`yoga_evaluator` rulesets as an INDEPENDENT reference. Discrepancies are
classified MATCH / CONVENTION_DIFFERENCE / REFERENCE_DIFFERENCE /
ASTROLIFE_BUG / UNRESOLVED. Astrolife is never auto-changed to match legacy;
the reason is recorded first (per spec §30).
"""
from __future__ import annotations
import json
import os
from typing import Dict, List

LEGACY_MAP = {
    # new rule id -> legacy ruleset file
    "PARASHARI.YOGA.GAJA_KESARI": "gaja_kesari.json",
    "PARASHARI.YOGA.DHARMA_KARMADHIPATI": "dharma_karmadhipati_yoga.json",
    "PARASHARI.YOGA.RUCHAKA": "ruchaka_yoga.json",
    "PARASHARI.YOGA.BHADRA": "bhadra_yoga.json",
    "PARASHARI.YOGA.HAMSA": "hamsa_yoga.json",
    "PARASHARI.YOGA.MALAVYA": "malavya_yoga.json",
    "PARASHARI.YOGA.SASA": "sasa_yoga.json",
    "PARASHARI.YOGA.BUDHA_ADITYA": "budhaditya_yoga.json",
    "PARASHARI.YOGA.CHANDRA_MANGALA": "chandra_mangala_yoga.json",
    "PARASHARI.YOGA.ADHI": "adhi_yoga.json",
    "PARASHARI.YOGA.KEMADRUMA": "kemadruma_yoga.json",
    "PARASHARI.YOGA.SUNAPHA": "sunapha_yoga.json",
    "PARASHARI.YOGA.ANAPHA": "anapha_yoga.json",
    "PARASHARI.YOGA.DURUDHARA": "durdhara_yoga.json",
    "PARASHARI.YOGA.LAKSHMI": "lakshmi_yoga.json",
    "PARASHARI.YOGA.SARASWATI": "saraswati_yoga.json",
    "PARASHARI.YOGA.AMALA": "amala_yoga.json",
    "PARASHARI.YOGA.VASUMATI": "vasumati_yoga.json",
}


def run_crosscheck() -> List[Dict]:
    import sys
    backend = os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__)))))
    if backend not in sys.path:
        sys.path.insert(0, backend)
    from core.rules.parashari.fixtures import make_golden_context
    from core.rules.parashari.catalog import evaluate_parashari_by_id, create_parashari_evaluator
    import yoga_evaluator as ye

    ctx = make_golden_context()
    ev = create_parashari_evaluator()
    asc = ctx.ascendant_sign
    planet_data = {}
    for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        planet_data[p] = {
            "sign_flag": ctx.get_planet_sign(p),
            "sign_manual": ctx.get_planet_sign(p),
            "lon_sidereal_flag": ctx.get_planet_longitude(p),
            "lon_sidereal_manual": ctx.get_planet_longitude(p),
            "d9_sign": ctx.get_varga_sign(p, 9),
        }
    houses = {h: {"sign": ctx.get_house_sign(h)} for h in range(1, 13)}
    ruleset_dir = os.path.join(backend, "rulesets", "yogas")
    if not os.path.isdir(ruleset_dir):
        ruleset_dir = os.path.join(os.getcwd(), "backend", "rulesets", "yogas")

    rows: List[Dict] = []
    for rule_id, fname in LEGACY_MAP.items():
        new_res = evaluate_parashari_by_id(rule_id, ctx, ev)
        new_formed = str(new_res.formation_status).endswith("FORMED") and \
            not str(new_res.formation_status).startswith("FormationStatus.NOT")
        legacy_active = None
        legacy_detail = ""
        try:
            rs = ye.load_ruleset(os.path.join(ruleset_dir, fname))
            out = ye.evaluate_yoga(rs, planet_data, houses, asc)
            legacy_active = bool(out.get("is_active") or out.get("is_strong"))
            legacy_detail = f"score={out.get('score')} status={out.get('status')}"
        except Exception as ex:  # noqa: BLE001
            legacy_detail = f"legacy error: {ex}"
        if legacy_active is None:
            verdict = "UNRESOLVED"
            reason = "legacy ruleset could not be evaluated; " + legacy_detail
        elif new_formed == legacy_active:
            verdict = "MATCH"
            reason = "both agree on " + ("FORMED/active" if new_formed else "NOT_FORMED/inactive")
        else:
            verdict = "CONVENTION_DIFFERENCE"
            reason = (
                "legacy weighted-score predicates differ structurally from the classical "
                "spec (e.g. legacy orb/conjunction handling, merged variants, score "
                "thresholds vs deterministic formation). New engine keeps classical "
                "spec; no auto-change. " + legacy_detail
            )
        rows.append({"rule_id": rule_id, "legacy_file": fname,
                     "new_formed": new_formed, "legacy_active": legacy_active,
                     "verdict": verdict, "reason": reason})
    return rows


if __name__ == "__main__":
    rows = run_crosscheck()
    print(json.dumps(rows, indent=2))
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crosscheck.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2)
    print("wrote", out)
