"""
Phase 5H — Timing Engine Tests.

Exhaustive unit tests for the Jaimini Timing + Event-Candidate Engine.
Tests: models, dasha activation, transit activation, convergence,
candidate building, deduplication, conflicts, pipeline, profile isolation,
golden snapshots, determinism, edge cases.
"""
from __future__ import annotations

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, patch

import pytest

# ============================================================================
# Fixtures & Helpers
# ============================================================================


def _utc(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    return datetime(year, month, day, hour, minute, tzinfo=timezone.utc)


def _make_temporal_window(start: datetime, end: datetime):
    from core.jaimini.timing.models import TemporalWindow
    return TemporalWindow(start=start, end=end)


def _make_dasha_period(
    period_id: str,
    sign: str,
    start: datetime,
    end: datetime,
    level: str = "MAHA_DASHA",
    antardashas: Optional[List] = None,
):
    from core.jaimini.dasha.models import JaiminiDashaPeriod
    return JaiminiDashaPeriod(
        period_id=period_id,
        level=level,
        sign=sign,
        start_utc_iso=start.isoformat(),
        end_utc_iso=end.isoformat(),
        duration_years=(end - start).total_seconds() / (365.25 * 86400),
        antardashas=antardashas or [],
    )


def _make_dasha_result(
    profile_method: str,
    periods: List,
):
    from core.jaimini.dasha.models import JaiminiDashaResult
    return JaiminiDashaResult(
        profile_method=profile_method,
        periods=periods,
        status="COMPUTED",
    )


def _make_mapping_entry(
    rule_id: str = "JAI.KARAKA.AK_AMK_CONJUNCTION",
    event_category: str = "RELATIONSHIP",
    activation_conditions: Optional[List] = None,
    transit_requirements: str = "transit-to-natal-AK-sign",
):
    from core.jaimini.mappings import MappingEntry
    from core.jaimini.candidates import JaiminiEventCategory
    if activation_conditions is None:
        from core.jaimini.mappings import ActivationCondition
        activation_conditions = [
            ActivationCondition.ACTIVE_DASHA_SIGN,
            ActivationCondition.TRANSIT_RELATIONSHIP,
        ]
    return MappingEntry(
        rule_id=rule_id,
        event_category=JaiminiEventCategory(event_category),
        activation_conditions=activation_conditions,
        timing_requirements="MAHA_DASHA",
        required_dasha_level="MAHA_DASHA",
        transit_requirements=transit_requirements,
        evidence_requirements=["DIRECT_FACT", "DERIVED_FACT"],
        tradition="JAIMINI",
        method="CLASSICAL_STANDARD",
        confidence="TRADITION_DEPENDENT",
        provenance="UNVERIFIED",
    )


def _make_candidate_context(
    rule_id: str = "JAI.KARAKA.AK_AMK_CONJUNCTION",
    event_category: str = "RELATIONSHIP",
    profile_id: str = "TEST_PROFILE",
    rule_formed: bool = True,
    dasha_activations: Optional[List] = None,
    transit_conditions: Optional[List] = None,
):
    from core.jaimini.timing.models import CandidateContext, DashaActivationRecord
    if dasha_activations is None:
        dasha_activations = [
            DashaActivationRecord(
                period_id="PERIOD_1",
                level="MAHA_DASHA",
                sign="Aries",
                start=_utc(2025, 1, 1),
                end=_utc(2030, 1, 1),
                profile_id=profile_id,
            )
        ]
    if transit_conditions is None:
        transit_conditions = []
    return CandidateContext(
        rule_id=rule_id,
        event_category=event_category,
        rule_formed=rule_formed,
        formation_status="FORMED",
        dasha_activations=dasha_activations,
        transit_conditions=transit_conditions,
        profile_id=profile_id,
    )


def _make_candidate(
    candidate_id: str = "test:RELATIONSHIP:2025-01-01:2030-01-01",
    profile: str = "TEST_PROFILE",
    event_category: str = "RELATIONSHIP",
    rule_ids: Optional[List[str]] = None,
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    convergence: str = "SINGLE_CONDITION",
):
    from core.jaimini.candidates import JaiminiEventCandidate, JaiminiEventCategory
    if rule_ids is None:
        rule_ids = ["JAI.KARAKA.AK_AMK_CONJUNCTION"]
    if start is None:
        start = _utc(2025, 1, 1)
    if end is None:
        end = _utc(2030, 1, 1)
    return JaiminiEventCandidate(
        candidate_id=candidate_id,
        event_category=JaiminiEventCategory(event_category),
        rule_ids=rule_ids,
        dasha_period_ids=["PERIOD_1"],
        transit_condition_ids=[],
        start=start,
        end=end,
        duration_years=(end - start).total_seconds() / (365.25 * 86400),
        duration_precision="WINDOW",
        status="ACTIVE",
        profile=profile,
        evidence=[],
        dependencies=[],
        conflicts=[],
        convergence=convergence,
    )


# ============================================================================
# TEST: TemporalWindow
# ============================================================================


class TestTemporalWindow:
    def test_overlapping_windows(self):
        w1 = _make_temporal_window(_utc(2025, 1, 1), _utc(2026, 1, 1))
        w2 = _make_temporal_window(_utc(2025, 6, 1), _utc(2026, 6, 1))
        assert w1.overlaps(w2)
        assert w2.overlaps(w1)

    def test_non_overlapping_windows(self):
        w1 = _make_temporal_window(_utc(2025, 1, 1), _utc(2025, 6, 1))
        w2 = _make_temporal_window(_utc(2025, 7, 1), _utc(2025, 12, 1))
        assert not w1.overlaps(w2)

    def test_adjacent_windows_no_overlap(self):
        w1 = _make_temporal_window(_utc(2025, 1, 1), _utc(2025, 6, 1))
        w2 = _make_temporal_window(_utc(2025, 6, 1), _utc(2025, 12, 1))
        assert not w1.overlaps(w2)

    def test_intersection(self):
        w1 = _make_temporal_window(_utc(2025, 1, 1), _utc(2026, 1, 1))
        w2 = _make_temporal_window(_utc(2025, 6, 1), _utc(2026, 6, 1))
        inter = w1.intersection(w2)
        assert inter is not None
        assert inter.start == _utc(2025, 6, 1)
        assert inter.end == _utc(2026, 1, 1)

    def test_no_intersection(self):
        w1 = _make_temporal_window(_utc(2025, 1, 1), _utc(2025, 6, 1))
        w2 = _make_temporal_window(_utc(2025, 7, 1), _utc(2025, 12, 1))
        assert w1.intersection(w2) is None

    def test_duration_days(self):
        w = _make_temporal_window(_utc(2025, 1, 1), _utc(2025, 1, 31))
        assert abs(w.duration_days() - 30.0) < 0.01

    def test_frozen(self):
        w = _make_temporal_window(_utc(2025, 1, 1), _utc(2026, 1, 1))
        with pytest.raises(Exception):
            w.start = _utc(2020, 1, 1)


# ============================================================================
# TEST: Dasha Activation
# ============================================================================


class TestDashaActivation:
    def test_single_period_intersecting(self):
        from core.jaimini.timing.dasha_activation import activate_dasha_periods

        period = _make_dasha_period(
            "P1", "Aries", _utc(2025, 1, 1), _utc(2030, 1, 1)
        )
        result = _make_dasha_result("PROFILE_A", [period])
        window = _make_temporal_window(_utc(2025, 6, 1), _utc(2028, 1, 1))

        activations = activate_dasha_periods(result, window)
        assert len(activations) == 1
        assert activations[0].period_id == "P1"
        assert activations[0].start == _utc(2025, 6, 1)
        assert activations[0].end == _utc(2028, 1, 1)

    def test_no_intersecting_period(self):
        from core.jaimini.timing.dasha_activation import activate_dasha_periods

        period = _make_dasha_period(
            "P1", "Aries", _utc(2020, 1, 1), _utc(2022, 1, 1)
        )
        result = _make_dasha_result("PROFILE_A", [period])
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))

        activations = activate_dasha_periods(result, window)
        assert len(activations) == 0

    def test_multiple_periods(self):
        from core.jaimini.timing.dasha_activation import activate_dasha_periods

        p1 = _make_dasha_period("P1", "Aries", _utc(2025, 1, 1), _utc(2027, 1, 1))
        p2 = _make_dasha_period("P2", "Taurus", _utc(2027, 1, 1), _utc(2029, 1, 1))
        result = _make_dasha_result("PROFILE_A", [p1, p2])
        window = _make_temporal_window(_utc(2025, 6, 1), _utc(2028, 6, 1))

        activations = activate_dasha_periods(result, window)
        assert len(activations) == 2
        assert activations[0].period_id == "P1"
        assert activations[1].period_id == "P2"

    def test_antardasha_levels(self):
        from core.jaimini.timing.dasha_activation import activate_dasha_periods

        ad1 = _make_dasha_period(
            "AD1", "Taurus", _utc(2025, 1, 1), _utc(2025, 7, 1),
            level="ANTARDASHA"
        )
        p1 = _make_dasha_period(
            "P1", "Aries", _utc(2025, 1, 1), _utc(2030, 1, 1),
            antardashas=[ad1]
        )
        result = _make_dasha_result("PROFILE_A", [p1])
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))

        activations_maha = activate_dasha_periods(result, window, ["MAHA_DASHA"])
        assert len(activations_maha) == 1

        activations_both = activate_dasha_periods(
            result, window, ["MAHA_DASHA", "ANTARDASHA"]
        )
        assert len(activations_both) == 2


# ============================================================================
# TEST: Convergence
# ============================================================================


class TestConvergence:
    def test_single_condition(self):
        from core.jaimini.timing.convergence import classify_convergence
        from core.jaimini.timing.models import DashaActivationRecord

        da = DashaActivationRecord(
            period_id="P1", level="MAHA_DASHA", sign="Aries",
            start=_utc(2025, 1, 1), end=_utc(2030, 1, 1), profile_id="P"
        )
        result = classify_convergence([da], [])
        assert result == "SINGLE_CONDITION"

    def test_double_condition(self):
        from core.jaimini.timing.convergence import classify_convergence
        from core.jaimini.timing.models import DashaActivationRecord, TransitConditionRecord, TemporalWindow

        da = DashaActivationRecord(
            period_id="P1", level="MAHA_DASHA", sign="Aries",
            start=_utc(2025, 1, 1), end=_utc(2030, 1, 1), profile_id="P"
        )
        tc = TransitConditionRecord(
            condition_id="conj:Sun:AK", condition_type="conjunction",
            transit_planet="Sun", target="AK",
            window=TemporalWindow(start=_utc(2025, 6, 1), end=_utc(2025, 6, 2)),
        )
        result = classify_convergence([da], [tc])
        assert result == "DOUBLE_CONDITION"

    def test_multi_condition(self):
        from core.jaimini.timing.convergence import classify_convergence
        from core.jaimini.timing.models import DashaActivationRecord, TransitConditionRecord, TemporalWindow

        da = DashaActivationRecord(
            period_id="P1", level="MAHA_DASHA", sign="Aries",
            start=_utc(2025, 1, 1), end=_utc(2030, 1, 1), profile_id="P"
        )
        tc1 = TransitConditionRecord(
            condition_id="conj:Sun:AK", condition_type="conjunction",
            transit_planet="Sun", target="AK",
            window=TemporalWindow(start=_utc(2025, 6, 1), end=_utc(2025, 6, 2)),
        )
        tc2 = TransitConditionRecord(
            condition_id="conj:Jupiter:AmK", condition_type="conjunction",
            transit_planet="Jupiter", target="AmK",
            window=TemporalWindow(start=_utc(2025, 6, 1), end=_utc(2025, 6, 2)),
        )
        result = classify_convergence([da], [tc1, tc2])
        assert result == "MULTI_CONDITION"

    def test_convergence_from_counts(self):
        from core.jaimini.timing.convergence import convergence_from_counts
        assert convergence_from_counts(1, 0) == "SINGLE_CONDITION"
        assert convergence_from_counts(1, 1) == "DOUBLE_CONDITION"
        assert convergence_from_counts(2, 1) == "MULTI_CONDITION"
        assert convergence_from_counts(1, 2) == "MULTI_CONDITION"


# ============================================================================
# TEST: Candidate Builder
# ============================================================================


class TestCandidateBuilder:
    def test_build_candidate_formed(self):
        from core.jaimini.timing.candidates import build_candidate

        ctx = _make_candidate_context(rule_formed=True)
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))

        candidate = build_candidate(ctx, window)
        assert candidate is not None
        assert candidate.rule_ids == ["JAI.KARAKA.AK_AMK_CONJUNCTION"]
        assert candidate.event_category.value == "RELATIONSHIP"
        assert candidate.profile == "TEST_PROFILE"

    def test_build_candidate_not_formed(self):
        from core.jaimini.timing.candidates import build_candidate

        ctx = _make_candidate_context(rule_formed=False)
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))

        candidate = build_candidate(ctx, window)
        assert candidate is None

    def test_build_candidate_no_dasha(self):
        from core.jaimini.timing.candidates import build_candidate

        ctx = _make_candidate_context(rule_formed=True, dasha_activations=[])
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))

        candidate = build_candidate(ctx, window)
        assert candidate is None

    def test_candidate_id_deterministic(self):
        from core.jaimini.timing.candidates import build_candidate

        ctx = _make_candidate_context()
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))

        c1 = build_candidate(ctx, window)
        c2 = build_candidate(ctx, window)
        assert c1.candidate_id == c2.candidate_id

    def test_candidate_frozen(self):
        from core.jaimini.timing.candidates import build_candidate

        ctx = _make_candidate_context()
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))
        c = build_candidate(ctx, window)
        with pytest.raises(Exception):
            c.rule_ids = []


# ============================================================================
# TEST: Deduplication
# ============================================================================


class TestDeduplication:
    def test_no_duplicates(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates

        c1 = _make_candidate(
            candidate_id="A:REL:2025:2030",
            rule_ids=["RULE_A"],
            start=_utc(2025, 1, 1),
            end=_utc(2030, 1, 1),
        )
        c2 = _make_candidate(
            candidate_id="B:REL:2035:2040",
            rule_ids=["RULE_B"],
            start=_utc(2035, 1, 1),
            end=_utc(2040, 1, 1),
        )
        result = deduplicate_candidates([c1, c2])
        assert len(result) == 2

    def test_overlapping_same_key_merge(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates

        c1 = _make_candidate(
            candidate_id="A:REL:2025:2030",
            rule_ids=["RULE_A"],
            start=_utc(2025, 1, 1),
            end=_utc(2030, 1, 1),
        )
        c2 = _make_candidate(
            candidate_id="A:REL:2027:2032",
            rule_ids=["RULE_A"],
            start=_utc(2027, 1, 1),
            end=_utc(2032, 1, 1),
        )
        result = deduplicate_candidates([c1, c2])
        assert len(result) == 1
        assert result[0].start == _utc(2025, 1, 1)
        assert result[0].end == _utc(2032, 1, 1)

    def test_different_keys_no_merge(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates

        c1 = _make_candidate(
            candidate_id="A:REL:2025:2030",
            rule_ids=["RULE_A"],
            start=_utc(2025, 1, 1),
            end=_utc(2030, 1, 1),
        )
        c2 = _make_candidate(
            candidate_id="A:WEALTH:2025:2030",
            event_category="WEALTH",
            rule_ids=["RULE_B"],
            start=_utc(2025, 1, 1),
            end=_utc(2030, 1, 1),
        )
        result = deduplicate_candidates([c1, c2])
        assert len(result) == 2

    def test_empty_list(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates
        assert deduplicate_candidates([]) == []

    def test_merge_preserves_extra_evidence(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates

        c1 = _make_candidate(
            candidate_id="A:REL:2025:2030",
            rule_ids=["RULE_A"],
            start=_utc(2025, 1, 1),
            end=_utc(2030, 1, 1),
        )
        c2 = _make_candidate(
            candidate_id="A:REL:2027:2032",
            rule_ids=["RULE_A"],
            start=_utc(2027, 1, 1),
            end=_utc(2032, 1, 1),
        )
        result = deduplicate_candidates([c1, c2])
        assert len(result) == 1
        assert result[0].rule_ids == ["RULE_A"]


# ============================================================================
# TEST: Candidate Conflicts
# ============================================================================


class TestCandidateConflicts:
    def test_no_conflicts_different_profiles(self):
        from core.jaimini.timing.conflicts import report_candidate_conflicts

        c1 = _make_candidate(candidate_id="P1:REL:2025:2030", profile="P1")
        c2 = _make_candidate(candidate_id="P2:REL:2025:2030", profile="P2")
        result = report_candidate_conflicts([c1, c2])
        assert len(result) == 0

    def test_no_conflicts_different_categories(self):
        from core.jaimini.timing.conflicts import report_candidate_conflicts

        c1 = _make_candidate(candidate_id="P:REL:2025:2030", profile="P")
        c2 = _make_candidate(
            candidate_id="P:WEALTH:2025:2030",
            profile="P",
            event_category="WEALTH",
            rule_ids=["JAI.ARUDHA.DHANA_A2_A11"],
        )
        result = report_candidate_conflicts([c1, c2])
        assert len(result) == 0

    def test_no_conflicts_non_overlapping(self):
        from core.jaimini.timing.conflicts import report_candidate_conflicts

        c1 = _make_candidate(
            candidate_id="P:REL:2025:2027",
            start=_utc(2025, 1, 1),
            end=_utc(2027, 1, 1),
        )
        c2 = _make_candidate(
            candidate_id="P:REL:2028:2030",
            start=_utc(2028, 1, 1),
            end=_utc(2030, 1, 1),
        )
        result = report_candidate_conflicts([c1, c2])
        assert len(result) == 0

    def test_single_candidate_no_conflicts(self):
        from core.jaimini.timing.conflicts import report_candidate_conflicts
        c1 = _make_candidate()
        result = report_candidate_conflicts([c1])
        assert len(result) == 0


# ============================================================================
# TEST: Profile Isolation
# ============================================================================


class TestProfileIsolation:
    def test_clean_isolation(self):
        from core.jaimini.timing.profile_isolation import ProfileIsolationGuard

        guard = ProfileIsolationGuard()
        c1 = _make_candidate(candidate_id="C1", profile="P1")
        c2 = _make_candidate(candidate_id="C2", profile="P2")
        guard.register("P1", [c1])
        guard.register("P2", [c2])
        violations = guard.check_isolation()
        assert violations == []

    def test_violation_on_shared_candidate(self):
        from core.jaimini.timing.profile_isolation import ProfileIsolationGuard

        guard = ProfileIsolationGuard()
        c1 = _make_candidate(candidate_id="SHARED_ID", profile="P1")
        c2 = _make_candidate(candidate_id="SHARED_ID", profile="P2")
        guard.register("P1", [c1])
        guard.register("P2", [c2])
        violations = guard.check_isolation()
        assert len(violations) == 1
        assert "SHARED_ID" in violations[0]

    def test_get_candidates(self):
        from core.jaimini.timing.profile_isolation import ProfileIsolationGuard

        guard = ProfileIsolationGuard()
        c1 = _make_candidate(profile="P1")
        guard.register("P1", [c1])
        assert len(guard.get_candidates("P1")) == 1
        assert len(guard.get_candidates("P2")) == 0

    def test_all_profiles(self):
        from core.jaimini.timing.profile_isolation import ProfileIsolationGuard

        guard = ProfileIsolationGuard()
        guard.register("P2", [_make_candidate(profile="P2")])
        guard.register("P1", [_make_candidate(profile="P1")])
        assert guard.all_profiles() == ["P1", "P2"]

    def test_merge_profiles(self):
        from core.jaimini.timing.profile_isolation import ProfileIsolationGuard

        guard = ProfileIsolationGuard()
        c1 = _make_candidate(candidate_id="C1", profile="P1")
        c2 = _make_candidate(candidate_id="C2", profile="P2")
        guard.register("P1", [c1])
        guard.register("P2", [c2])
        merged = guard.merge_profiles()
        assert "P1" in merged
        assert "P2" in merged
        assert len(merged["P1"]) == 1
        assert len(merged["P2"]) == 1


# ============================================================================
# TEST: Golden Snapshots
# ============================================================================


class TestGoldenSnapshots:
    def test_capture_and_verify(self):
        from core.jaimini.timing.golden import capture_golden_snapshot, verify_golden_snapshot
        from core.jaimini.timing.models import CandidateEvaluation

        eval_result = CandidateEvaluation(
            profile_id="TEST",
            total_candidates=0,
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "golden.json"
            meta = capture_golden_snapshot(eval_result, path)
            assert path.exists()
            assert meta["total_candidates"] == 0

            verification = verify_golden_snapshot(eval_result, path)
            assert verification["match"] is True

    def test_verify_mismatch(self):
        from core.jaimini.timing.golden import verify_golden_snapshot
        from core.jaimini.timing.models import CandidateEvaluation

        eval_result = CandidateEvaluation(profile_id="TEST", total_candidates=0)

        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "golden.json"
            path.write_text('{"changed": true}')

            verification = verify_golden_snapshot(eval_result, path)
            assert verification["match"] is False

    def test_verify_missing_file(self):
        from core.jaimini.timing.golden import verify_golden_snapshot
        from core.jaimini.timing.models import CandidateEvaluation

        eval_result = CandidateEvaluation(profile_id="TEST", total_candidates=0)
        path = Path("/nonexistent/golden.json")
        verification = verify_golden_snapshot(eval_result, path)
        assert verification["match"] is False

    def test_determinism_check(self):
        from core.jaimini.timing.golden import verify_determinism
        from core.jaimini.timing.models import CandidateEvaluation

        def eval_fn():
            return CandidateEvaluation(profile_id="TEST", total_candidates=0)

        result = verify_determinism(eval_fn, "TEST", n_runs=50)
        assert result["deterministic"] is True
        assert result["unique_hashes"] == 1


# ============================================================================
# TEST: Candidate Model
# ============================================================================


class TestCandidateModel:
    def test_event_category_enum(self):
        from core.jaimini.candidates import JaiminiEventCategory
        assert JaiminiEventCategory.FAMILY.value == "FAMILY"
        assert JaiminiEventCategory.RELATIONSHIP.value == "RELATIONSHIP"
        assert JaiminiEventCategory.MARRIAGE.value == "MARRIAGE"
        assert JaiminiEventCategory.CAREER.value == "CAREER"
        assert JaiminiEventCategory.WEALTH.value == "WEALTH"
        assert JaiminiEventCategory.SPIRITUAL.value == "SPIRITUAL"

    def test_temporal_precision_enum(self):
        from core.jaimini.candidates import TemporalPrecision
        assert TemporalPrecision.EXACT.value == "EXACT"
        assert TemporalPrecision.DAY.value == "DAY"
        assert TemporalPrecision.WINDOW.value == "WINDOW"
        assert TemporalPrecision.APPROXIMATE.value == "APPROXIMATE"
        assert TemporalPrecision.UNKNOWN.value == "UNKNOWN"

    def test_convergence_level_enum(self):
        from core.jaimini.candidates import ConvergenceLevel
        assert ConvergenceLevel.SINGLE_CONDITION.value == "SINGLE_CONDITION"
        assert ConvergenceLevel.DOUBLE_CONDITION.value == "DOUBLE_CONDITION"
        assert ConvergenceLevel.MULTI_CONDITION.value == "MULTI_CONDITION"

    def test_candidate_repr(self):
        c = _make_candidate()
        r = repr(c)
        assert "JaiminiEventCandidate" in r
        assert "RELATIONSHIP" in r


# ============================================================================
# TEST: Mapping Entry
# ============================================================================


class TestMappingEntry:
    def test_mapping_entry_creation(self):
        m = _make_mapping_entry()
        assert m.rule_id == "JAI.KARAKA.AK_AMK_CONJUNCTION"
        assert m.event_category.value == "RELATIONSHIP"
        assert m.tradition == "JAIMINI"

    def test_mapping_entry_mutable(self):
        m = _make_mapping_entry()
        m.activated = True
        assert m.activated is True


# ============================================================================
# TEST: DashaActivationRecord
# ============================================================================


class TestDashaActivationRecord:
    def test_creation(self):
        from core.jaimini.timing.models import DashaActivationRecord
        da = DashaActivationRecord(
            period_id="P1", level="MAHA_DASHA", sign="Aries",
            start=_utc(2025, 1, 1), end=_utc(2030, 1, 1), profile_id="P"
        )
        assert da.period_id == "P1"
        assert da.level == "MAHA_DASHA"

    def test_frozen(self):
        from core.jaimini.timing.models import DashaActivationRecord
        da = DashaActivationRecord(
            period_id="P1", level="MAHA_DASHA", sign="Aries",
            start=_utc(2025, 1, 1), end=_utc(2030, 1, 1), profile_id="P"
        )
        with pytest.raises(Exception):
            da.period_id = "CHANGED"


# ============================================================================
# TEST: TransitConditionRecord
# ============================================================================


class TestTransitConditionRecord:
    def test_creation(self):
        from core.jaimini.timing.models import TransitConditionRecord, TemporalWindow
        tc = TransitConditionRecord(
            condition_id="conj:Sun:AK", condition_type="conjunction",
            transit_planet="Sun", target="AK",
            window=TemporalWindow(start=_utc(2025, 6, 1), end=_utc(2025, 6, 2)),
        )
        assert tc.condition_id == "conj:Sun:AK"
        assert tc.transit_planet == "Sun"

    def test_frozen(self):
        from core.jaimini.timing.models import TransitConditionRecord, TemporalWindow
        tc = TransitConditionRecord(
            condition_id="conj:Sun:AK", condition_type="conjunction",
            transit_planet="Sun", target="AK",
            window=TemporalWindow(start=_utc(2025, 6, 1), end=_utc(2025, 6, 2)),
        )
        with pytest.raises(Exception):
            tc.condition_id = "CHANGED"


# ============================================================================
# TEST: CandidateContext
# ============================================================================


class TestCandidateContext:
    def test_creation(self):
        ctx = _make_candidate_context()
        assert ctx.rule_id == "JAI.KARAKA.AK_AMK_CONJUNCTION"
        assert ctx.rule_formed is True
        assert ctx.profile_id == "TEST_PROFILE"

    def test_frozen(self):
        ctx = _make_candidate_context()
        with pytest.raises(Exception):
            ctx.rule_id = "CHANGED"


# ============================================================================
# TEST: CandidateEvaluation
# ============================================================================


class TestCandidateEvaluation:
    def test_creation(self):
        from core.jaimini.timing.models import CandidateEvaluation
        ce = CandidateEvaluation(profile_id="P1", total_candidates=5)
        assert ce.profile_id == "P1"
        assert ce.total_candidates == 5

    def test_frozen(self):
        from core.jaimini.timing.models import CandidateEvaluation
        ce = CandidateEvaluation(profile_id="P1")
        with pytest.raises(Exception):
            ce.profile_id = "CHANGED"

    def test_default_values(self):
        from core.jaimini.timing.models import CandidateEvaluation
        ce = CandidateEvaluation()
        assert ce.candidates == []
        assert ce.conflicts == []
        assert ce.total_candidates == 0


# ============================================================================
# TEST: Edge Cases
# ============================================================================


class TestEdgeCases:
    def test_empty_dasha_result(self):
        from core.jaimini.timing.dasha_activation import activate_dasha_periods
        result = _make_dasha_result("P", [])
        window = _make_temporal_window(_utc(2025, 1, 1), _utc(2030, 1, 1))
        assert activate_dasha_periods(result, window) == []

    def test_zero_duration_window(self):
        w = _make_temporal_window(_utc(2025, 1, 1), _utc(2025, 1, 1))
        assert w.duration_days() == 0.0
        assert not w.overlaps(w)

    def test_candidate_sort_stability(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates
        c1 = _make_candidate(candidate_id="B:REL:2025:2030", start=_utc(2025, 1, 1), end=_utc(2030, 1, 1))
        c2 = _make_candidate(candidate_id="A:REL:2025:2030", start=_utc(2025, 1, 1), end=_utc(2030, 1, 1))
        result = deduplicate_candidates([c1, c2])
        ids = [c.candidate_id for c in result]
        assert ids == sorted(ids)

    def test_many_candidates_deterministic_order(self):
        from core.jaimini.timing.deduplication import deduplicate_candidates
        candidates = []
        for i in range(20):
            candidates.append(
                _make_candidate(
                    candidate_id=f"P{i}:REL:2025:2030",
                    rule_ids=[f"RULE_{i}"],
                    start=_utc(2025, 1, 1),
                    end=_utc(2030, 1, 1),
                )
            )
        result = deduplicate_candidates(candidates)
        ids = [c.candidate_id for c in result]
        assert ids == sorted(ids)
