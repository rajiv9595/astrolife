"""
Generate real golden end-to-end timing snapshots for all 3 Chara Dasha profiles.

Uses the actual golden chart and real upstream implementations.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.calculation.varga import calculate_all_vargas
from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.jaimini.integration import evaluate_jaimini
from core.jaimini.dasha import (
    JaiminiDashaProfile, calculate_jaimini_dasha
)
from core.jaimini.timing.pipeline import evaluate_jaimini_timing
from core.jaimini.timing.models import CandidateEvaluation
from core.jaimini.timing.golden import capture_golden_snapshot, verify_determinism


def main():
    print("=" * 70)
    print("GENERATING REAL GOLDEN END-TO-END TIMING SNAPSHOTS")
    print("=" * 70)

    # Golden chart
    print("\n1. Generating ChartFacts...")
    gchart = generate_chart_facts(
        year=2005, month=8, day=17, hour=0, minute=2, second=0,
        lat=16.93407, lon=81.95522, tz_name="Asia/Kolkata",
        location_name="Anaparthy", country_name="India",
        profile=DEFAULT_PROFILE
    )
    print(f"   Ascendant: {gchart.ascendant.sign.name}")

    # Varga facts
    print("2. Generating VargaFacts...")
    gvf = calculate_all_vargas(gchart, DEFAULT_PROFILE)
    print(f"   Vargas: {len(gvf.get('planets', {}))} planets")

    # Jaimini facts
    print("3. Generating JaiminiFacts...")
    gjf = generate_jaimini_facts(gchart, gvf, JaiminiCalculationProfile())
    print(f"   Karakas: {gjf.chara_karakas.karakas['AK'].planet}")
    print(f"   Karakamsha: {gjf.karakamsha.karakamsha_sign}")

    # Jaimini rules evaluation
    print("4. Evaluating Jaimini rules...")
    jeval = evaluate_jaimini(gchart, gjf, gvf)
    print(f"   Total rules: {jeval.total_rules}")
    print(f"   Formed: {jeval.formed_rules}")
    print(f"   Unknown: {jeval.unknown_rules}")

    # Evaluation window (1 year from birth for testing)
    birth_utc = datetime.fromisoformat(gchart.time.utc_datetime.replace("Z", "+00:00"))
    evaluation_start = birth_utc
    evaluation_end = birth_utc.replace(year=birth_utc.year + 1)

    # Three Chara Dasha profiles
    profiles = [
        "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL",
        "CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED",
        "CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS",
    ]

    all_snapshots = {}

    for profile_id in profiles:
        print(f"\n{'='*70}")
        print(f"PROFILE: {profile_id}")
        print(f"{'='*70}")

        # Create profile
        profile = JaiminiDashaProfile.from_method(profile_id)
        print(f"Direction rule: {profile.direction_rule}")

        # Calculate Chara Dasha
        print("5. Calculating Chara Dasha...")
        dasha_result = calculate_jaimini_dasha(gchart, gjf, profile)
        print(f"   Status: {dasha_result.status}")
        print(f"   Starting sign: {dasha_result.starting_sign}")
        print(f"   Direction: {dasha_result.direction}")
        print(f"   Total years: {dasha_result.total_years}")
        print(f"   Periods: {len(dasha_result.periods)}")
        for p in dasha_result.periods[:4]:
            print(f"     {p.sign}: {p.duration_years:.1f} yr ({p.start_utc_iso[:10]} to {p.end_utc_iso[:10]})")

        # Full timing evaluation
        print("6. Running full timing evaluation...")
        timing_result = evaluate_jaimini_timing(
            chart_facts=gchart,
            jaimini_facts=gjf,
            jaimini_evaluation=jeval,
            dasha_result=dasha_result,
            evaluation_start=evaluation_start,
            evaluation_end=evaluation_end,
            calc_profile=DEFAULT_PROFILE,
        )
        print(f"   Candidates: {timing_result.total_candidates}")
        print(f"   Conflicts: {len(timing_result.conflicts)}")
        for c in timing_result.candidates:
            print(f"     {c.candidate_id} - {c.event_category.value} [{c.convergence}] {c.start.isoformat()[:10]} to {c.end.isoformat()[:10]}")

        # Capture golden snapshot
        print("7. Capturing golden snapshot...")
        snapshot_dir = Path(os.path.dirname(__file__)) / "golden_timing_snapshots"
        snapshot_dir.mkdir(exist_ok=True)
        snapshot_path = snapshot_dir / f"golden_timing_{profile_id}.json"

        meta = capture_golden_snapshot(timing_result, snapshot_path)
        print(f"   Snapshot written: {snapshot_path}")
        print(f"   Total candidates: {meta['total_candidates']}")

        # Verify determinism
        print("8. Verifying determinism (50 runs)...")

        def eval_fn():
            return evaluate_jaimini_timing(
                chart_facts=gchart,
                jaimini_facts=gjf,
                jaimini_evaluation=jeval,
                dasha_result=dasha_result,
                evaluation_start=evaluation_start,
                evaluation_end=evaluation_end,
                calc_profile=DEFAULT_PROFILE,
            )

        det_result = verify_determinism(eval_fn, profile_id, n_runs=50)
        print(f"   Deterministic: {det_result['deterministic']}")
        print(f"   Unique hashes: {det_result['unique_hashes']}")

        # Store for summary
        all_snapshots[profile_id] = {
            "profile": profile_id,
            "direction_rule": profile.direction_rule,
            "direction": dasha_result.direction,
            "starting_sign": dasha_result.starting_sign,
            "total_years": dasha_result.total_years,
            "dasha_periods": [
                {
                    "sign": p.sign,
                    "duration_years": p.duration_years,
                    "start_utc": p.start_utc_iso,
                    "end_utc": p.end_utc_iso,
                }
                for p in dasha_result.periods
            ],
            "timing": {
                "total_candidates": timing_result.total_candidates,
                "candidates": [
                    {
                        "candidate_id": c.candidate_id,
                        "event_category": c.event_category.value,
                        "convergence": c.convergence,
                        "start": c.start.isoformat(),
                        "end": c.end.isoformat(),
                        "duration_years": c.duration_years,
                        "dasha_period_ids": c.dasha_period_ids,
                        "transit_condition_ids": c.transit_condition_ids,
                        "rule_ids": c.rule_ids,
                    }
                    for c in timing_result.candidates
                ],
                "conflicts": timing_result.conflicts,
            },
            "determinism": det_result,
        }

    # Write combined summary
    summary_path = snapshot_dir / "golden_timing_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump({
            "chart": "MEDAPATI BHASKARA VENKATA RAJEEV REDDY 17/08/2005 00:02 IST Anaparthy",
            "engine": "jaimini-timing/1.0.0",
            "evaluation_window": {
                "start": evaluation_start.isoformat(),
                "end": evaluation_end.isoformat(),
            },
            "profiles": all_snapshots,
        }, f, indent=2)

    print(f"\n{'='*70}")
    print(f"ALL SNAPSHOTS COMPLETE")
    print(f"Summary: {summary_path}")
    print(f"{'='*70}")

    # Print summary table
    print("\nSUMMARY TABLE:")
    print(f"{'Profile':<50} {'Direction':<10} {'Candidates':<10} {'Cycles':<8}")
    print("-" * 78)
    for pid, snap in all_snapshots.items():
        print(f"{pid:<50} {snap['direction']:<10} {snap['timing']['total_candidates']:<10} {snap['total_years']:.1f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())