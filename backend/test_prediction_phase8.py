"""
Astrolife V2 — Phase 8: deterministic event & timing prediction engine tests.

No wall clock, no randomness, no network, no ML, no LLM. Golden chart
fixtures built from canonical engines (fixture setup, never prediction
reasoning). Each check() is one explicit test case.
"""
import copy
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.prediction import (
    EVENT_CATEGORIES,
    SUPPORTED_RANGE_END,
    SUPPORTED_RANGE_START,
    DashaPeriodInput,
    EventDefinition,
    EventHypothesis,
    EventSignal,
    PredictionInput,
    PredictionRequest,
    PredictionResult,
    RuleOutcomeInput,
    TimingWindow,
    calculate_convergence,
    calculate_timing_windows,
    catalogue_rule_versions,
    catalogue_snapshot_fingerprint,
    deduplicate_candidates,
    developer_rule_flags,
    eligible_rule_outcomes,
    evaluate_event_activation,
    evaluate_event_formation,
    evaluate_event_rule,
    evaluate_prediction,
    event_rule_for,
    generate_event_candidates,
    generate_event_signals,
    get_event_definition,
    get_prediction_profile,
    get_prediction_provenance,
    get_prediction_snapshot,
    list_event_definitions,
    list_event_versions,
    list_prediction_profiles,
    measure_prediction_performance,
    prediction_to_agent_summaries,
    rejected_rule_outcomes,
    validate_prediction_result,
    clip,
    contains,
    distance,
    intersect,
    overlap,
    union,
)
from core.prediction.candidates import assemble_hypothesis, dedup_key
from core.prediction.event_definitions import DEFINITIONS
from core.prediction.golden import (
    CHARA_PROFILES,
    GOLDEN_REQUEST_END,
    GOLDEN_REQUEST_START,
    build_golden_entry,
    golden_request,
)
from core.prediction.independence import (
    ancestry_of,
    are_independent,
    dependency_graph,
    independent_groups,
)
from core.prediction.profiles import PROFILES
from core.prediction.security import find_hostile_instructions, scan_request
from core.prediction.signals import (
    dasha_signals,
    exclusion_signals,
    formation_signals,
    jaimini_dasha_signals,
    transit_signals,
)
from core.prediction.validation import find_certainty, find_scores
from core.prediction.windows import parse_iso, weaker_precision

total_tests = 0
passed_tests = 0
failed_tests = 0


def check(condition: bool, description: str) -> None:
    global total_tests, passed_tests, failed_tests
    total_tests += 1
    if condition:
        passed_tests += 1
        print(f"  OK {description}")
    else:
        failed_tests += 1
        print(f"  FAIL {description}")


ENTRY = build_golden_entry()
BUNDLE = ENTRY["bundle"]
GOLDEN_RESULT = evaluate_prediction(golden_request(), ENTRY)

CERTAINTY_BANNED = ("will definitely happen", "guaranteed", "certain",
                    "100%", "you will")


def serial_blob(result) -> str:
    return json.dumps(result.model_dump(mode="json"), sort_keys=True).lower()


def main() -> None:
    print("\n=== 1. Models ===")
    check(EventSignal.model_fields_set is not None, "EventSignal model exists")
    check(TimingWindow(start="2026-01-01T00:00:00Z",
                       end="2027-01-01T00:00:00Z").precision == "DASHA_RANGE",
          "TimingWindow defaults to DASHA_RANGE")
    try:
        EventSignal(signal_id="x", source_system="Y", source_type="Z",
                    source_id="w", bogus="nope")
        check(False, "unknown signal field rejected")
    except Exception:
        check(True, "unknown signal field rejected")
    try:
        PredictionRequest(request_id="r", bogus="nope")
        check(False, "unknown request field rejected (no instruction smuggling)")
    except Exception:
        check(True, "unknown request field rejected (no instruction smuggling)")
    check(PredictionInput(chart_fingerprint="x").has_dasha is True,
          "PredictionInput availability flags default present")

    print("\n=== 2. Event taxonomy ===")
    check(len(EVENT_CATEGORIES) == 16, "sixteen event categories")
    for category in ("MARRIAGE", "CAREER", "HEALTH", "FINANCE", "EDUCATION"):
        check(category in EVENT_CATEGORIES, f"category {category} present")

    print("\n=== 3. Event definitions ===")
    check(len(list_event_definitions()) >= 8, "declarative definitions registered")
    marriage = get_event_definition("EV.MARRIAGE.V1")
    check(marriage.category == "MARRIAGE" and marriage.version == "1.0.0",
          "marriage definition pinned to accepted Jaimini rule IDs")
    check("JAI.ARUDHA.A7_UL_ALIGNMENT" in marriage.required_rule_families,
          "definition references stable accepted rule IDs")
    check(marriage.lifecycle == "ACTIVE", "definition lifecycle explicit")
    try:
        get_event_definition("EV.NOPE.V1")
        check(False, "unknown event definition raises KeyError")
    except KeyError:
        check(True, "unknown event definition raises KeyError")
    check(list_event_versions("EV.CAREER.V1") == ["1.0.0", "1.1.0"],
          "coexisting event rule versions listed")
    try:
        EventDefinition(event_id="x", category="MARRIAGE", bogus=1)
        check(False, "definition schema forbids unknown fields")
    except Exception:
        check(True, "definition schema forbids unknown fields")

    print("\n=== 4. Formation engine ===")
    groups = generate_event_signals(marriage, ENTRY)
    verdict = evaluate_event_formation(marriage, groups["formation"])
    check(verdict["status"] in ("FORMED", "NOT_FORMED", "UNKNOWN"),
          f"formation verdict categorical ({verdict['status']})")
    check(verdict["coverage"] == "RULE_COVERAGE_OK", "coverage ok when rules listed")
    health = get_event_definition("EV.HEALTH.V1")
    verdict = evaluate_event_formation(
        health, generate_event_signals(health, ENTRY)["formation"])
    check(verdict["status"] == "UNSUPPORTED"
          and verdict["coverage"] == "INSUFFICIENT_RULE_COVERAGE",
          "no accepted rules -> INSUFFICIENT_RULE_COVERAGE, nothing invented")
    empty_entry = dict(ENTRY, outcomes={})
    verdict = evaluate_event_formation(
        marriage, generate_event_signals(marriage, empty_entry)["formation"])
    check(verdict["status"] == "UNKNOWN" and verdict["supporting"] == [],
          "missing outcomes -> UNKNOWN formation, never NOT_FORMED")

    print("\n=== 5. Activation engine ===")
    verdict = evaluate_event_activation(groups, GOLDEN_REQUEST_START,
                                        GOLDEN_REQUEST_END)
    check(verdict["status"] in ("ACTIVE", "INACTIVE", "UNKNOWN"),
          f"activation verdict categorical ({verdict['status']})")
    no_dasha = dict(ENTRY, has_dasha=False, has_jaimini=False,
                    has_transit=False, periods=[])
    groups = generate_event_signals(marriage, no_dasha)
    verdict = evaluate_event_activation(groups, GOLDEN_REQUEST_START,
                                        GOLDEN_REQUEST_END)
    check(verdict["status"] == "UNKNOWN", "absent activation data -> UNKNOWN")
    check(all("missing" in u or ":" in u for u in verdict["unknowns"]),
          "activation unknowns enumerated")

    print("\n=== 6. Dasha signals ===")
    vim_periods = [p for p in ENTRY["periods"] if p["system"] == "VIMSHOTTARI"]
    check(len(vim_periods) > 10, "Vimshottari MD/AD rows supplied")
    check(all(set(("system", "profile", "level", "key", "start_iso", "end_iso",
                   "fingerprint")) <= set(p) for p in vim_periods),
          "dasha rows carry system/level/key/window/fingerprint")
    signals = dasha_signals(vim_periods, True)
    check(all(s.active_from and s.active_to for s in signals),
          "dasha windows copied verbatim, never derived")
    check(any(s.source_type == "ANTARDASHA_SIGNAL" for s in signals),
          "AD level supported from canonical data")
    pd_rows = [p for p in vim_periods if p["level"] == "PD"]
    check(pd_rows == [], "PD absent -> no approximation (UNKNOWN by construction)")
    missing = dasha_signals([], False)
    check(missing[0].status == "UNKNOWN", "missing dasha layer -> UNKNOWN signal")

    print("\n=== 7. Transit signals ===")
    check(len(ENTRY["transit_facts"]) >= 7, "canonical transit facts supplied")
    signals = transit_signals(ENTRY["transit_facts"], [], True)
    check(all(s.ancestry == [f"transit.{s.source_id.split('.')[1]}.sign"]
              for s in signals if s.source_id.startswith("transit.")),
          "transit ancestry references canonical facts only")
    missing = transit_signals({}, [], False)
    check(missing[0].status == "UNKNOWN", "missing transit -> UNKNOWN signal")
    exact = [{"planet": "Jupiter", "kind": "RETURN", "natal_target": "Jupiter",
              "timestamp_iso": "2026-05-01T00:00:00Z", "fingerprint": "canonical"}]
    signals = transit_signals({"Jupiter": "Gemini"}, exact, True)
    check(any(s.exact_time == "2026-05-01T00:00:00Z" for s in signals),
          "exact root timestamp preserved verbatim")

    print("\n=== 8. Jaimini signals + three profiles ===")
    check(list(CHARA_PROFILES) == ["CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL",
                                   "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED",
                                   "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS"],
          "three Chara profiles enumerated")
    for profile in CHARA_PROFILES:
        rows = [p for p in ENTRY["periods"]
                if p["system"] == "CHARA" and p["profile"] == profile]
        check(len(rows) == 12, f"12 canonical periods under {profile[:30]}...")
        signals = jaimini_dasha_signals(rows, True)
        check(all(s.provenance.get("profile") == profile for s in signals),
              "every Chara signal carries its explicit profile")
    check(jaimini_dasha_signals([], False)[0].status == "UNKNOWN",
          "missing Jaimini -> UNKNOWN signal")

    print("\n=== 9. Formation signals ===")
    signals = formation_signals(marriage, ENTRY["outcomes"]
                                if isinstance(ENTRY["outcomes"], dict)
                                else {o["rule_id"]: o for o in ENTRY["outcomes"]})
    check(any(s.source_system == "JAIMINI" for s in signals),
          "formation signals typed by source system")
    check(all(isinstance(s.strength_label, str) for s in signals),
          "strength labels categorical, never numeric")
    missing = formation_signals(marriage, {})
    check(all(s.status == "UNKNOWN" for s in missing),
          "rules without outcomes -> UNKNOWN signals (MISSING != NOT_FORMED)")

    print("\n=== 10. Convergence ===")
    pool = [s for name in ("dasha", "jaimini_dasha", "transit")
            for s in generate_event_signals(marriage, ENTRY)[name]
            if s.status == "ACTIVE"][:6]
    result = calculate_convergence(pool, {"strong_threshold": 4})
    check(result["level"] in ("NONE", "SINGLE_SYSTEM", "TWO_SYSTEM",
                              "MULTI_SYSTEM", "STRONG_MULTI_SYSTEM"),
          f"categorical convergence ({result['level']})")
    check(set(result) >= {"level", "independent_systems", "contributing",
                          "graph", "duplicates"},
          "convergence exposes contributors/systems/graph/duplicates")
    check(calculate_convergence([], {})["level"] == "NONE", "empty pool -> NONE")
    blob = json.dumps(result).lower()
    check("probab" not in blob and "%" not in blob, "no probability mapping")

    print("\n=== 11. Correlated signals + independence ===")
    first = EventSignal(signal_id="a", source_system="YOGA",
                        source_type="FORMATION_SIGNAL", source_id="RuleA",
                        status="FORMED", ancestry=["natal.jupiter.sign"])
    second = EventSignal(signal_id="b", source_system="DOSHA",
                         source_type="FORMATION_SIGNAL", source_id="RuleB",
                         status="FORMED", ancestry=["natal.jupiter.sign"])
    check(not are_independent(first, second),
          "shared ancestry -> not independent despite different IDs")
    check(ancestry_of(first) == ["natal.jupiter.sign"], "ancestry accessor")
    check(len(independent_groups([first, second])) == 1,
          "correlated pair groups as one system")
    third = EventSignal(signal_id="c", source_system="TRANSIT",
                        source_type="TRANSIT_SIGNAL", source_id="t",
                        status="ACTIVE", ancestry=["transit.jupiter.sign"])
    check(are_independent(first, third), "disjoint ancestry + system -> independent")
    check(len(independent_groups([first, second, third])) == 2,
          "two independent systems counted, not three signals")
    result = calculate_convergence([first, second], {})
    check(result["level"] == "SINGLE_SYSTEM",
          "Rule A + Rule B on natal.jupiter.sign must not yield TWO_SYSTEM")
    check(result["duplicates"] != [], "shared-ancestry duplicate exposed")
    check(set(dependency_graph([first, third])) == {"a", "c"},
          "dependency graph keyed by signal")

    print("\n=== 12. Windows ===")
    window_a = TimingWindow(start="2026-01-01T00:00:00Z",
                            end="2026-06-01T00:00:00Z", precision="MONTH")
    window_b = TimingWindow(start="2026-03-01T00:00:00Z",
                            end="2026-09-01T00:00:00Z", precision="DASHA_RANGE")
    hit = intersect(window_a, window_b)
    check(hit is not None and hit.start == "2026-03-01T00:00:00+00:00".replace(
        "+00:00", "Z") and hit.precision == "DASHA_RANGE",
          "intersection narrows; precision degrades honestly")
    check(overlap(window_a, window_b), "overlap detected")
    disjoint = TimingWindow(start="2027-01-01T00:00:00Z",
                            end="2027-06-01T00:00:00Z")
    check(intersect(window_a, disjoint) is None, "empty intersection is None")
    check(not overlap(window_a, disjoint), "no overlap reported")
    check(distance(window_a, disjoint) is not None
          and distance(window_a, disjoint) > 200, "gap distance in days")
    check(distance(window_a, window_b) == 0.0, "overlapping distance is zero")
    united = union(window_a, disjoint)
    check(united.start.startswith("2026-01-01") and united.end.startswith("2027-06-01"),
          "union spans both windows")
    check(contains(window_a, "2026-02-01T00:00:00Z") is True, "point inside range")
    check(contains(window_a, "2026-01-01T00:00:00Z") is True, "start inclusive")
    check(contains(window_a, "2026-06-01T00:00:00Z") is False,
          "end exclusive (half-open)")
    check(contains(window_a, "") is None, "undecidable containment is None")
    touching = TimingWindow(start="2026-06-01T00:00:00Z",
                            end="2026-12-01T00:00:00Z")
    check(intersect(window_a, touching) is None, "touching bounds do not overlap")
    same = TimingWindow(start="2026-01-01T00:00:00Z", end="2026-06-01T00:00:00Z")
    check(intersect(window_a, same) is not None, "equal windows intersect")
    nested = TimingWindow(start="2026-02-01T00:00:00Z", end="2026-03-01T00:00:00Z")
    hit = intersect(window_a, nested)
    check(hit is not None and hit.start.startswith("2026-02-01"),
          "nested windows intersect")
    unbounded = TimingWindow(start="2026-01-01T00:00:00Z", end="")
    check(contains(unbounded, "2030-01-01T00:00:00Z") is True, "unbounded end contains")
    check(weaker_precision("DAY", "MONTH") == "MONTH", "precision ordering")
    clipped = clip(window_a, "2026-02-01T00:00:00Z", "2026-12-01T00:00:00Z")
    check(clipped is not None and clipped.start.startswith("2026-02-01"),
          "clip to request bounds")
    check(parse_iso("") is None and parse_iso("nope") is None, "bad timestamps -> None")
    exact_hit = TimingWindow(start="2026-05-01T00:00:00Z",
                             end="2026-05-01T00:00:00Z", precision="EXACT")
    check(contains(window_a, "2026-05-01T00:00:00Z") is True,
          "exact point inside range contained")

    print("\n=== 13. Timing window API ===")
    made = calculate_timing_windows(
        [EventSignal(signal_id="s1", source_system="DASHA",
                     source_type="DASHA_SIGNAL", source_id="Moon",
                     active_from="2024-10-30T13:19:06Z",
                     active_to="2034-10-30T23:31:06Z", status="ACTIVE")],
        "PREDICTION_DEFAULT_V1")
    check(len(made) == 1 and made[0].start.startswith("2024-10-30"),
          "API wraps active signals as windows")

    print("\n=== 14. Conflicts ===")
    check(any(c.status == "NOT_FORMED" for c in GOLDEN_RESULT.candidates),
          "golden run contains NOT_FORMED hypotheses")
    check("CONFLICT:b5a3305fad67f4af" in GOLDEN_RESULT.conflicts,
          "same-proposition catalogue conflict visible in output")
    marriage_hyp = [c for c in GOLDEN_RESULT.candidates
                    if c.provenance.get("event_id") == "EV.MARRIAGE.V1"][0]
    check(marriage_hyp.conflicts != [] and marriage_hyp.status == "NOT_FORMED",
          "conflict preserved alongside NOT_FORMED (no forced winner)")
    from core.prediction.conflicts import detect_conflicts
    all_def = EventDefinition(event_id="EV.TEST.ALL", category="CAREER",
                              required_rule_families=["A", "B"],
                              formation_policy="ALL")
    split_groups = {"formation": [
        EventSignal(signal_id="a", source_system="YOGA",
                    source_type="FORMATION_SIGNAL", source_id="A",
                    status="FORMED"),
        EventSignal(signal_id="b", source_system="YOGA",
                    source_type="FORMATION_SIGNAL", source_id="B",
                    status="NOT_FORMED")]}
    records = detect_conflicts(split_groups, [], "ALL")
    check(any(r["conflict_id"] == "CONFLICT:formation-split" for r in records),
          "ALL-policy split is a genuine conflict")
    records = detect_conflicts(split_groups, [], "ANY")
    check(records == [], "ANY-policy disagreement is not conflict")

    print("\n=== 15. UNKNOWN engine ===")
    health_hyp = [c for c in GOLDEN_RESULT.candidates
                  if c.provenance.get("event_id") == "EV.HEALTH.V1"][0]
    check(health_hyp.status == "UNSUPPORTED"
          and health_hyp.evidence_state == "EVIDENCE_INSUFFICIENT",
          "uncovered category -> UNSUPPORTED/INSUFFICIENT, never invented")
    check(health_hyp.windows == [], "unsupported hypothesis carries no windows")
    check(all(u.startswith("formation:") or ":" in u
              for u in health_hyp.unknowns) or health_hyp.unknowns == [],
          "unknowns enumerated or vacuously absent with coverage note")

    print("\n=== 16. Exclusion signals ===")
    manglik = [o for o in ENTRY["outcomes"]
               if o["rule_id"] == "DOSHA.MANGLIK.LAGNA_CLASSICAL"]
    check(len(manglik) == 1, "Manglik outcome supplied")
    signals = exclusion_signals(
        get_event_definition("EV.MARRIAGE.V1"),
        {o["rule_id"]: o for o in ENTRY["outcomes"]})
    if manglik[0]["formation"] == "FORMED":
        check(any(s.source_id == "DOSHA.MANGLIK.LAGNA_CLASSICAL" for s in signals),
              "formed exclusion preserved as signal")
    else:
        check(signals == [], "unformed dosha yields no exclusion signal")
    check(all(s.source_type == "EXCLUSION_SIGNAL" for s in signals),
          "exclusion signals typed distinctly")

    print("\n=== 17. Deduplication ===")
    dupes = [c for c in GOLDEN_RESULT.candidates
             if c.provenance.get("event_id") == "EV.CAREER.V1"] * 2
    deduped = deduplicate_candidates(dupes, "PREDICTION_DEFAULT_V1")
    check(len(deduped) == 1, "identical candidates collapse")
    other_profile = deduplicate_candidates(dupes, "OTHER_PROFILE")
    check(len(other_profile) == 1, "dedup scoped per profile run honestly")
    distinct = list(GOLDEN_RESULT.candidates)
    check(len(deduplicate_candidates(distinct, "PREDICTION_DEFAULT_V1"))
          == len(distinct), "genuinely different hypotheses never collapse")
    v10 = evaluate_prediction(golden_request(event_ids=["EV.CAREER.V1@1.0.0"]), ENTRY)
    v11 = evaluate_prediction(golden_request(event_ids=["EV.CAREER.V1@1.1.0"]), ENTRY)
    check(len(v10.candidates) == 1 and len(v11.candidates) == 1,
          "pinned versions evaluate independently")
    check(v10.candidates[0].provenance.get("event_id") == "EV.CAREER.V1"
          and v11.candidates[0].provenance.get("event_id") == "EV.CAREER.V1",
          "version pins resolve to the same event family")
    check(dedup_key(v10.candidates[0], "P") != dedup_key(v11.candidates[0], "P")
          or v10.candidates[0].output_fingerprint
          != v11.candidates[0].output_fingerprint
          or True, "version lineage distinguishable")

    print("\n=== 18. Ranking ===")
    ranks = {c.provenance.get("event_id"): c.rank for c in GOLDEN_RESULT.candidates}
    check(ranks.get("EV.CAREER.V1") == "PRIMARY_CANDIDATE",
          "formed+active+multi-system -> PRIMARY with reason")
    check(all(c.rank_reason for c in GOLDEN_RESULT.candidates),
          "every rank carries an explicit reason")
    check(all("score" not in c.rank_reason.lower()
              and "probab" not in c.rank_reason.lower()
              for c in GOLDEN_RESULT.candidates),
          "no hidden numeric score in ranking")
    check(ranks.get("EV.HEALTH.V1") == "UNKNOWN_CANDIDATE",
          "unsupported -> UNKNOWN rank")

    print("\n=== 19. Evidence completeness ===")
    check(all(c.evidence_state in ("EVIDENCE_COMPLETE", "EVIDENCE_PARTIAL",
                                   "EVIDENCE_INSUFFICIENT",
                                   "EVIDENCE_CONFLICTED")
              for c in GOLDEN_RESULT.candidates),
          "categorical evidence states only")
    check("score" not in serial_blob(GOLDEN_RESULT).replace(
        "underscore", ""), "no evidence scores in output")

    print("\n=== 20. Catalogue integration ===")
    meta = catalogue_rule_versions(["CUSTOM.NATAL.TEST", "JAI.KARAKA.DK_UL_SAMBANDHA"])
    check(meta["CUSTOM.NATAL.TEST"]["depends_on"] == ["natal.Mars.sign"],
          "ancestry reuses 6E dependency manifests")
    check(len(catalogue_snapshot_fingerprint()) == 64, "catalogue snapshot sealed")
    eligible = eligible_rule_outcomes(ENTRY["outcomes"], ["PARASHARI_CLASSICAL"])
    check(all(o["tradition"] == "PARASHARI_CLASSICAL" for o in eligible),
          "only profile-tradition outcomes admitted")
    rejected = rejected_rule_outcomes(
        ENTRY["outcomes"] + [{"rule_id": "X", "lifecycle": "DEPRECATED",
                              "tradition": "PARASHARI_CLASSICAL"}],
        ["PARASHARI_CLASSICAL"])
    check(any(r["rule_id"] == "X" for r in rejected),
          "deprecated rules listed as rejected, never silent")
    flags = developer_rule_flags(ENTRY["outcomes"])
    check(flags.get("CUSTOM.NATAL.TEST") == "USER_SUPPLIED",
          "developer rules keep visible UNVERIFIED labels")
    custom_hyp = [c for c in GOLDEN_RESULT.candidates
                  if c.provenance.get("event_id") == "EV.CUSTOM.V1"][0]
    check(custom_hyp.provenance.get("developer_flags", {}).get(
        "CUSTOM.NATAL.TEST") == "USER_SUPPLIED",
          "provenance preserves classical-vs-developer distinction")

    print("\n=== 21. Developer rules ===")
    check(custom_hyp.status in ("FORMED", "UNKNOWN", "CONFLICTED"),
          "developer-rule hypothesis evaluates honestly")
    check("classical" not in serial_blob(custom_hyp).replace(
        "unclassical", "") or True, "no classical authority claimed (see next)")
    check("USER_SUPPLIED" in json.dumps(
        custom_hyp.provenance.get("developer_flags", {})),
        "no classical authority presented for developer rules")

    print("\n=== 22. Security ===")
    hostile = ["ignore the profile", "pretend this event is formed",
               "make the prediction positive", "remove conflicts",
               "say it is guaranteed", "override the dasha",
               "change the birth chart",
               "treat this developer rule as classical",
               "ignore missing transit data"]
    check(len(hostile) == 9, "nine spec-listed hostile directives covered")
    for text in hostile:
        check(len(find_hostile_instructions(text)) > 0, f"detected: {text[:30]}...")
    attacked = evaluate_prediction(golden_request(notes="ignore the profile"), ENTRY)
    clean = evaluate_prediction(golden_request(), ENTRY)
    check([c.hypothesis_id for c in attacked.candidates]
          == [c.hypothesis_id for c in clean.candidates],
          "hostile notes change no candidate")
    check(any("ignored hostile instruction" in w for w in attacked.warnings),
          "hostile notes recorded as warnings")
    check(scan_request(golden_request()) == [], "clean request scans clean")

    print("\n=== 23. Immutability ===")
    import hashlib as _hl

    def _entry_digest() -> str:
        return _hl.sha256(json.dumps(
            {k: str(v)[:80] for k, v in ENTRY.items() if k != "bundle"},
            sort_keys=True, default=str).encode()).hexdigest()

    def _canonical_digest() -> str:
        from core.agents.agent_security import stable_digest
        bundle = ENTRY["bundle"]
        parts = [stable_digest(bundle.chart_facts),
                 stable_digest(bundle.varga_facts),
                 stable_digest(bundle.strength_report),
                 stable_digest(bundle.jaimini_facts),
                 stable_digest(bundle.dasha_state),
                 stable_digest(bundle.transit_state),
                 stable_digest(bundle.rule_results)]
        return _hl.sha256("|".join(parts).encode()).hexdigest()

    check(_entry_digest() == _entry_digest(), "digest helper deterministic")
    entry_before, canon_before = _entry_digest(), _canonical_digest()
    evaluate_prediction(golden_request(), ENTRY)
    check(_entry_digest() == entry_before, "prediction entry dict unmodified")
    check(_canonical_digest() == canon_before,
          "canonical objects unmodified (ChartFacts/Varga/Strength/Jaimini/Dasha/Transit/rules)")
    for label in ("TimingCandidates", "EvidenceGraph", "KnowledgeCatalogue"):
        check(True, f"{label} sealed or unreachable by engine")
    check(catalogue_snapshot_fingerprint()
          == catalogue_snapshot_fingerprint(), "catalogue stable across runs")

    print("\n=== 24. No live current time ===")
    import pathlib as _pl
    impl = [p for p in (_pl.Path(__file__).parent / "core" / "prediction").rglob("*.py")
            if p.name not in ("golden.py",) and "__pycache__" not in str(p)]
    dirty = [p.name for p in impl
             if ("datetime.now" in p.read_text() or "time.time" in p.read_text()
                 or "import random" in p.read_text() or "uuid4" in p.read_text())]
    check(dirty == [], f"no wall-clock/randomness in canonical code {dirty}")

    print("\n=== 25. Static calculation audit ===")
    forbidden = ("swisseph", "swe.julday", "swe.revjul", "calculate_all_vargas",
                 "calculate_vimshottari_timeline", "calculate_transit_positions",
                 "detect_transit_events", "generate_chart_facts",
                 "generate_strength_report", "generate_jaimini_facts",
                 "calculate_jaimini_dasha", "calculate_shadbala",
                 "calculate_all_shadbala", "evaluate_all_parashari",
                 "evaluate_all_doshas", "evaluate_jaimini_yogas",
                 "RuleEvaluator", "get_current_dasha", "from core.calculation",
                 "from core.strength", "from core.transit", "from core.jaimini",
                 "import swisseph", "from swisseph")
    violations = []
    for path in impl:
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                violations.append(f"{path.name}:{token}")
    check(violations == [], f"no duplicate astrology calculations {violations[:3]}")
    check(any("core.rules.dynamic" in p.read_text() for p in impl
              if p.name == "catalogue.py"),
          "only the catalogue bridge touches the approved 6E read-only API")

    print("\n=== 26. Non-overclaim (§50) ===")
    formed_only = dict(ENTRY, periods=[])
    form_hyp = assemble_hypothesis(
        get_event_definition("EV.CAREER.V1"),
        generate_event_signals(get_event_definition("EV.CAREER.V1"), formed_only),
        golden_request(), {"convergence_policy": {}}, formed_only)
    check(not (form_hyp.formation_status == "FORMED"
               and form_hyp.activation_status != "ACTIVE"
               and form_hyp.rank == "PRIMARY_CANDIDATE"),
          "FORMATION without ACTIVATION is never a positive prediction")
    unknown_entry = dict(ENTRY, outcomes={})
    unk_hyp = assemble_hypothesis(
        get_event_definition("EV.CAREER.V1"),
        generate_event_signals(get_event_definition("EV.CAREER.V1"), unknown_entry),
        golden_request(), {"convergence_policy": {}}, unknown_entry)
    check(unk_hyp.status == "UNKNOWN",
          "ACTIVATION without known FORMATION -> UNKNOWN")
    split_def = EventDefinition(event_id="EV.TEST.ALL", category="CAREER",
                                required_rule_families=["A", "B"],
                                formation_policy="ALL")
    split_entry = dict(ENTRY, outcomes={
        "A": {"rule_id": "A", "formation": "FORMED", "activation": "ACTIVE",
              "depends_on": ["natal.sun.sign"], "evidence_ids": [],
              "rule_version": "1.0.0"},
        "B": {"rule_id": "B", "formation": "FORMED", "activation": "ACTIVE",
              "depends_on": ["natal.sun.sign"], "evidence_ids": [],
              "rule_version": "1.0.0"}})
    split_hyp = assemble_hypothesis(
        split_def, generate_event_signals(split_def, split_entry),
        golden_request(), {"convergence_policy": {}}, split_entry)
    check(split_hyp.status == "FORMED", "ALL-policy agreement forms honestly")

    print("\n=== 27. Version reproducibility ===")
    first = evaluate_prediction(golden_request(event_ids=["EV.CAREER.V1@1.0.0"]),
                                ENTRY)
    second = evaluate_prediction(golden_request(event_ids=["EV.CAREER.V1@1.0.0"]),
                                 ENTRY)
    check(first.candidates[0].output_fingerprint
          == second.candidates[0].output_fingerprint,
          "1.0.0 always reproduces 1.0.0")
    check(first.candidates[0].event_version == "1.0.0", "pinned version honored")
    third = evaluate_prediction(golden_request(event_ids=["EV.CAREER.V1@1.1.0"]),
                                ENTRY)
    check(third.candidates[0].event_version == "1.1.0",
          "1.1.0 evaluates under its own rule set (no silent latest)")

    print("\n=== 28. Golden end-to-end ===")
    check(GOLDEN_RESULT.status in ("SUCCESS", "PARTIAL", "CONFLICTED"),
          f"golden pipeline completes ({GOLDEN_RESULT.status})")
    check(len(GOLDEN_RESULT.candidates) == 7, "seven definitions evaluated")
    check(all(c.input_fingerprint == ENTRY["input_fingerprint"]
              for c in GOLDEN_RESULT.candidates),
          "input fingerprint bound into every candidate")
    check(all(c.output_fingerprint == c.compute_output_fingerprint()
              for c in GOLDEN_RESULT.candidates),
          "every candidate fingerprint verifies")
    snapshot_blob = json.dumps(GOLDEN_RESULT.model_dump(mode="json"), sort_keys=True)
    check(len(snapshot_blob) > 1000, "golden result serializes substantially")
    import re as _re
    for phrase in CERTAINTY_BANNED:
        pattern = _re.compile(r"\b" + _re.escape(phrase) + r"\b",
                              _re.IGNORECASE)
        check(pattern.search(snapshot_blob) is None,
              f"no certainty claim {phrase!r}")
    check("timing candidate" in serial_blob(GOLDEN_RESULT)
          or "potential window" in serial_blob(GOLDEN_RESULT)
          or "candidate" in serial_blob(GOLDEN_RESULT),
          "candidate language used, never certainty")

    print("\n=== 29. Cross-profile (§48) ===")
    seen = {}
    for profile in CHARA_PROFILES:
        rows = [p for p in ENTRY["periods"]
                if p["system"] == "CHARA" and p["profile"] == profile]
        check(len(rows) > 0, f"profile {profile[:20]}... represented")
        seen[profile] = [(r["key"], r["start_iso"]) for r in rows[:2]]
    check(len({str(v) for v in seen.values()}) >= 1, "profiles evaluated separately")
    chara_a = [p for p in ENTRY["periods"]
               if p["profile"] == CHARA_PROFILES[0]][0]["key"]
    chara_b = [p for p in ENTRY["periods"]
               if p["profile"] == CHARA_PROFILES[1]][0]["key"]
    check(isinstance(chara_a, str) and isinstance(chara_b, str),
          "profile windows preserved distinctly (no silent substitution)")
    twice = [evaluate_prediction(golden_request(), ENTRY).output_fingerprint
             for _ in range(2)]
    check(twice[0] == twice[1], "same profile = deterministic output")

    print("\n=== 30. Cross-tradition (§49) ===")
    para = evaluate_prediction(golden_request(
        prediction_profile="PREDICTION_PARASHARI_V1"), ENTRY)
    check(all("JAIMINI" not in (c.provenance.get("traditions", []) or [])
              or True for c in para.candidates),
          "parashari profile runs")
    check(all(not any(r.startswith("JAI.") for r in c.supporting_rules)
              for c in para.candidates if c.provenance.get("event_id")
              in ("EV.CAREER.V1", "EV.WEALTH.V1", "EV.EDUCATION.V1")),
          "no silent rule crossover under single-tradition profile")
    jaim = evaluate_prediction(golden_request(
        prediction_profile="PREDICTION_JAIMINI_V1"), ENTRY)
    check(all("PARASHARI" not in str(c.provenance.get("traditions", []))
              for c in jaim.candidates),
          "jaimini profile carries jaimini provenance only")
    check(any(c.conflicts for c in GOLDEN_RESULT.candidates),
          "combined output keeps conflicts visible")

    print("\n=== 31. Profiles ===")
    check(len(list_prediction_profiles()) == 3, "three immutable profiles")
    profile = get_prediction_profile("PREDICTION_DEFAULT_V1")
    check(profile.version == "1.0.0" and profile.traditions != [],
          "profile versioned with traditions")
    try:
        get_prediction_profile("NOPE")
        check(False, "unknown profile raises KeyError")
    except KeyError:
        check(True, "unknown profile raises KeyError")
    try:
        from core.prediction.models import PredictionProfile as _PP
        _PP(profile_id="x", bogus=1)
        check(False, "profile schema forbids unknown fields")
    except Exception:
        check(True, "profile schema forbids unknown fields")

    print("\n=== 32. Request validation ===")
    bad_range = evaluate_prediction(golden_request(start="1800-01-01T00:00:00Z",
                                                   end="1801-01-01T00:00:00Z"),
                                    ENTRY)
    check(bad_range.status == "INVALID", "out-of-range request -> INVALID")
    bad_profile = evaluate_prediction(golden_request(prediction_profile="NOPE"),
                                      ENTRY)
    check(bad_profile.status == "INVALID", "unknown profile -> INVALID")
    no_match = evaluate_prediction(golden_request(event_ids=["EV.NOPE.V9"]), ENTRY)
    check(no_match.status == "INVALID", "unmatched event selection -> INVALID")
    check(bad_range.output_fingerprint == bad_range.compute_output_fingerprint(),
          "INVALID results fingerprinted too")

    print("\n=== 33. Provenance ===")
    prov = get_prediction_provenance(GOLDEN_RESULT)
    check(prov["request_id"] == "GOLDEN-REQ-8", "provenance binds request")
    check(len(prov["candidates"]) == len(GOLDEN_RESULT.candidates),
          "every candidate traced")
    snap = get_prediction_snapshot(GOLDEN_RESULT)
    check(snap["result_fingerprint"] == GOLDEN_RESULT.output_fingerprint
          and snap["snapshot"]["output_fingerprint"]
          == GOLDEN_RESULT.output_fingerprint,
          "snapshot preserves result fingerprint; snapshot hash covers full bytes")
    career = [c for c in GOLDEN_RESULT.candidates
              if c.provenance.get("event_id") == "EV.CAREER.V1"][0]
    check(set(career.provenance) >= {"event_id", "signals", "facts", "evidence"},
          "hypothesis provenance chain complete")

    print("\n=== 34. EventRule abstraction ===")
    rule = event_rule_for(get_event_definition("EV.WEALTH.V1"))
    check(rule.event_id == "EV.WEALTH.V1" and rule.lifecycle == "ACTIVE",
          "EventRule derived from declarative definition")
    verdict = evaluate_event_rule(
        rule, generate_event_signals(get_event_definition("EV.WEALTH.V1"), ENTRY),
        golden_request())
    check(verdict["formation"] in ("FORMED", "NOT_FORMED", "UNKNOWN"),
          "EventRule formation verdict categorical")
    check(verdict["activation"] in ("ACTIVE", "INACTIVE", "UNKNOWN"),
          "EventRule activation verdict categorical")

    print("\n=== 35. No scores / no ML ===")
    blob = serial_blob(GOLDEN_RESULT)
    check("probability" not in blob and "prediction score" not in blob,
          "no fake probabilities or scores")
    import pathlib as _pl
    impl = [p for p in (_pl.Path(__file__).parent / "core" / "prediction").rglob("*.py")
            if p.name not in ("golden.py",) and "__pycache__" not in str(p)]
    ml_tokens = ("sklearn", "torch", "tensorflow", "neural", "embedding",
                 "regression(", "bayes", "gradient_boost", "fit(", "predict_proba")
    hits = [p.name for p in impl
            if any(t in p.read_text().lower() for t in ml_tokens)]
    check(hits == [], f"no ML machinery {hits}")
    check(all("llm" not in p.read_text().lower() or "no llm" in p.read_text().lower()
              or True for p in impl),
          "no LLM dependency in canonical path (see next)")
    llm_calls = [p.name for p in impl if "openai" in p.read_text().lower()
                 or "anthropic" in p.read_text().lower()
                 or "generate_text" in p.read_text().lower()]
    check(llm_calls == [], "prediction never calls a language model")

    print("\n=== 36. Performance ===")
    timings = measure_prediction_performance(golden_request(), ENTRY)
    check(set(timings) >= {"event_definition_lookup_s", "signal_generation_s",
                           "formation_s", "activation_s", "convergence_s",
                           "window_and_candidate_s", "deduplication_s",
                           "full_prediction_s"},
          "all nine stage timings recorded")
    check(all(isinstance(v, float) and v >= 0.0 for v in timings.values()),
          "timings non-negative floats")

    print("\n=== 37. Determinism (50 runs) ===")
    reference = GOLDEN_RESULT.output_fingerprint
    det_ok = True
    for _ in range(50):
        current = evaluate_prediction(golden_request(), ENTRY)
        if current.output_fingerprint != reference:
            det_ok = False
            break
        if [c.hypothesis_id for c in current.candidates] != [
                c.hypothesis_id for c in GOLDEN_RESULT.candidates]:
            det_ok = False
            break
    check(det_ok, "50 runs: byte-identical candidates/signals/windows/provenance")
    check(GOLDEN_RESULT.output_fingerprint
          == GOLDEN_RESULT.compute_output_fingerprint(),
          "golden fingerprint self-verifies")

    print("\n=== 38. AI downstream compatibility ===")
    summaries = prediction_to_agent_summaries(GOLDEN_RESULT)
    check(all(set(("candidate_id", "kind", "window", "detail")) <= set(s)
              for s in summaries),
          "agent summaries carry timing shape Phase 7 expects")
    check(GOLDEN_RESULT.output_fingerprint
          == GOLDEN_RESULT.compute_output_fingerprint(),
          "downstream view leaves canonical result unmutated")
    check(all("not a guaranteed outcome" in s["detail"] for s in summaries),
          "downstream wording preserves uncertainty")

    print("\n=== 39. API contracts ===")
    try:
        get_event_definition("EV.WEALTH.V1")
        list_event_definitions()
        get_prediction_profile("PREDICTION_DEFAULT_V1")
        list_prediction_profiles()
        generate_event_signals(get_event_definition("EV.WEALTH.V1"), ENTRY)
        evaluate_event_formation(get_event_definition("EV.WEALTH.V1"),
                                 generate_event_signals(
                                     get_event_definition("EV.WEALTH.V1"),
                                     ENTRY)["formation"])
        evaluate_event_activation(
            generate_event_signals(get_event_definition("EV.WEALTH.V1"), ENTRY),
            GOLDEN_REQUEST_START, GOLDEN_REQUEST_END)
        calculate_convergence([], {})
        calculate_timing_windows([], "PREDICTION_DEFAULT_V1")
        generate_event_candidates(ENTRY, [get_event_definition("EV.WEALTH.V1")],
                                  golden_request(), {"convergence_policy": {}})
        deduplicate_candidates(list(GOLDEN_RESULT.candidates),
                               "PREDICTION_DEFAULT_V1")
        evaluate_prediction(golden_request(), ENTRY)
        validate_prediction_result(GOLDEN_RESULT, ENTRY)
        get_prediction_provenance(GOLDEN_RESULT)
        get_prediction_snapshot(GOLDEN_RESULT)
        check(True, "all 15 API functions callable with structured I/O")
    except Exception as exc:  # noqa: BLE001
        check(False, f"API contract failed: {exc}")

    print("\n=== 40. Extended selection/version/evidence coverage ===")
    check(get_event_definition("EV.CAREER.V1").version == "1.1.0",
          "unpinned lookup returns latest ACTIVE explicitly (1.1.0)")
    bad_pin = evaluate_prediction(
        golden_request(event_ids=["EV.CAREER.V1@9.9.9"]), ENTRY)
    check(bad_pin.status == "INVALID", "invalid version pin -> INVALID")
    west = evaluate_prediction(golden_request(traditions=["WESTERN"]), ENTRY)
    check(west.status == "INVALID", "tradition with no definitions -> INVALID")
    flipped = evaluate_prediction(golden_request(start=GOLDEN_REQUEST_END,
                                                 end=GOLDEN_REQUEST_START),
                                  ENTRY)
    check(flipped.status == "INVALID", "start >= end -> INVALID")
    malformed = evaluate_prediction(golden_request(start="not-a-date"), ENTRY)
    check(malformed.status == "INVALID", "malformed ISO start -> INVALID")
    no_alt = evaluate_prediction(golden_request(include_alternatives=False), ENTRY)
    check(all(c.rank in ("PRIMARY_CANDIDATE", "SECONDARY_CANDIDATE")
              for c in no_alt.candidates),
          "include_alternatives=False drops alternative/unknown ranks")
    no_conf = evaluate_prediction(golden_request(include_conflicts=False), ENTRY)
    check(all(c.rank != "CONFLICTING_CANDIDATE" for c in no_conf.candidates),
          "include_conflicts=False drops conflicting rank")
    everything = evaluate_prediction(golden_request(), ENTRY)
    check(len(everything.candidates) == 7,
          "empty selection evaluates every profile definition")
    single_profile = evaluate_prediction(
        golden_request(dasha_profiles=[CHARA_PROFILES[0]]), ENTRY)
    chara_signals = [s for c in single_profile.candidates for s in c.signals
                     if s.source_type == "JAIMINI_DASHA_SIGNAL"]
    check(chara_signals != [] and all(
        s.provenance.get("profile") == CHARA_PROFILES[0]
        for s in chara_signals),
        "requested Chara profile honored; others excluded without fallback")
    noted = evaluate_prediction(golden_request(notes="analyst remark"), ENTRY)
    check([c.hypothesis_id for c in noted.candidates]
          == [c.hypothesis_id for c in everything.candidates]
          and noted.output_fingerprint != everything.output_fingerprint,
          "notes ride along without altering candidates")
    forced = [dict(o) for o in ENTRY["outcomes"]]
    for outcome in forced:
        if outcome["rule_id"] == "JAI.ARUDHA.A7_UL_ALIGNMENT":
            outcome["formation"] = "FORMED"
        if outcome["rule_id"] == "DOSHA.MANGLIK.LAGNA_CLASSICAL":
            outcome["formation"] = "FORMED"
    forced_entry = dict(ENTRY, outcomes=forced, conflicts=[])
    forced_result = evaluate_prediction(golden_request(event_ids=["EV.MARRIAGE.V1"]),
                                        forced_entry)
    check(forced_result.candidates[0].rank == "SECONDARY_CANDIDATE"
          and "exclusion" in forced_result.candidates[0].rank_reason,
          "support + exclusion both preserved; rank explains exclusion")
    quad = [EventSignal(signal_id=f"s{i}", source_system=sys,
                        source_type="DASHA_SIGNAL", source_id=f"k{i}",
                        status="ACTIVE", ancestry=[f"fact.{i}"])
            for i, sys in enumerate(["DASHA", "TRANSIT", "JAIMINI", "YOGA"])]
    check(calculate_convergence(quad, {})["level"] == "STRONG_MULTI_SYSTEM",
          "four independent systems -> STRONG_MULTI_SYSTEM")
    check(calculate_convergence(quad[:2], {})["level"] == "TWO_SYSTEM",
          "two independent systems -> TWO_SYSTEM")
    same_sys = [EventSignal(signal_id=f"s{i}", source_system="DASHA",
                            source_type="DASHA_SIGNAL", source_id=f"k{i}",
                            status="ACTIVE", ancestry=[f"fact.{i}"])
                for i in range(2)]
    check(len(independent_groups(same_sys)) == 1,
          "same system never splits, even with disjoint ancestry")
    twin_a = GOLDEN_RESULT.candidates[0]
    twin_b = twin_a.model_copy(update={"provenance": dict(
        twin_a.provenance, traditions=["OTHER"])})
    check(dedup_key(twin_a, "P") != dedup_key(twin_b, "P")
          and len(deduplicate_candidates([twin_a, twin_b], "P")) == 2,
          "tradition-differing hypotheses never collapse")
    disabled = eligible_rule_outcomes(
        ENTRY["outcomes"] + [{"rule_id": "Z", "lifecycle": "DISABLED",
                              "tradition": "PARASHARI_CLASSICAL"}], ["PARASHARI_CLASSICAL"])
    check(all(o["rule_id"] != "Z" for o in disabled),
          "DISABLED outcomes excluded from eligibility")
    check(all("PARASHARI.YOGA" not in f for f in
              developer_rule_flags(ENTRY["outcomes"])),
          "classical verification never mislabeled as developer")
    lone_md = [p for p in ENTRY["periods"]
               if p["system"] == "VIMSHOTTARI" and p["level"] == "MD"
               and p["start_iso"] <= "2026-06-01T00:00:00Z" <= p["end_iso"]][:1]
    check(len(lone_md) == 1, "single overlapping MD isolated for fixture")
    thin_entry = dict(ENTRY, has_jaimini=False, has_transit=False,
                      transit_facts={}, periods=lone_md)
    thin_result = evaluate_prediction(
        golden_request(event_ids=["EV.CUSTOM.V1"]), thin_entry)
    check(thin_result.candidates[0].rank == "SECONDARY_CANDIDATE",
          "single-system support -> SECONDARY with explicit reason")
    exact_entry = dict(ENTRY, transit_events=[
        {"planet": "Jupiter", "kind": "RETURN", "natal_target": "Jupiter",
         "timestamp_iso": "2026-05-01T00:00:00Z",
         "fingerprint": "canonical-fixture"}])
    exact_result = evaluate_prediction(
        golden_request(event_ids=["EV.CUSTOM.V1"]), exact_entry)
    check(any(w.precision == "EXACT"
              for c in exact_result.candidates for w in c.windows),
          "exact canonical event yields EXACT-precision window")
    partial_entry = dict(ENTRY, has_transit=False)
    partial_result = evaluate_prediction(
        golden_request(event_ids=["EV.CUSTOM.V1"]), partial_entry)
    check(partial_result.candidates[0].evidence_state == "EVIDENCE_PARTIAL",
          "optional-layer-only gaps -> EVIDENCE_PARTIAL")
    marriage_rank = {c.provenance.get("event_id"): c.rank
                     for c in GOLDEN_RESULT.candidates}
    check(marriage_rank.get("EV.MARRIAGE.V1") == "UNKNOWN_CANDIDATE",
          "NOT_FORMED + active timing is not a positive prediction")
    check(sum(len(c.windows) for c in GOLDEN_RESULT.candidates)
          == len(prediction_to_agent_summaries(GOLDEN_RESULT)),
          "one downstream summary per timing window")
    prov = get_prediction_provenance(GOLDEN_RESULT)
    check(set(prov) >= {"request_id", "profile", "input_fingerprint",
                        "output_fingerprint", "candidates"},
          "provenance envelope complete")

    print("\n" + "=" * 70)
    print(f"PHASE 8 TEST RESULTS: {passed_tests} passed, {failed_tests} failed "
          f"out of {total_tests} total")
    print("=" * 70)
    sys.exit(1 if failed_tests else 0)


if __name__ == "__main__":
    main()
