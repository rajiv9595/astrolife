"""
Phase 5G — Dasha validators. Returns violation lists (empty = valid).
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, List


def _dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def validate_dasha_result(result: Any, days_per_year: float = 365.25) -> List[str]:
    v: List[str] = []
    periods = list(result.periods or [])
    if result.status == "UNKNOWN":
        if periods:
            v.append("UNKNOWN result must carry no periods.")
        if "missing" not in str(result.validation).lower() and "unavailable" not in str(
                result.provenance.get("notes", "")).lower():
            v.append("UNKNOWN result must explain missing inputs.")
        return sorted(v)
    if len(periods) != 12:
        v.append(f"Expected 12 mahadashas, found {len(periods)}.")
        return sorted(v)
    signs = [p.sign for p in periods]
    if sorted(signs) != sorted(set(signs)) or len(set(signs)) != 12:
        v.append(f"Mahadashas must cover 12 distinct signs: {signs}.")
    if [p.sequence_index for p in periods] != list(range(1, 13)):
        v.append("Mahadasha sequence indices must be 1..12.")
    if any(p.duration_years <= 0 for p in periods):
        v.append("No negative or zero durations allowed.")
    if abs(sum(p.duration_years for p in periods) - result.total_years) > 1e-9:
        v.append("Total years must equal the sum of period durations.")
    for i, p in enumerate(periods):
        if not p.duration_evidence:
            v.append(f"{p.period_id}: missing duration evidence.")
        else:
            ev = p.duration_evidence
            if ev.exception == "OWN_SIGN_TWELVE" and ev.duration_years != 12.0:
                v.append(f"{p.period_id}: OWN_SIGN_TWELVE must yield 12 years.")
            if ev.exception == "NONE" and not (1.0 <= ev.duration_years <= 12.0):
                v.append(f"{p.period_id}: plain duration out of 1..12 range.")
        if abs(p.duration_days - p.duration_years * days_per_year) > 1e-6:
            v.append(f"{p.period_id}: days/years inconsistent with year model.")
        if i > 0 and p.start_utc_iso != periods[i - 1].end_utc_iso:
            v.append(f"{p.period_id}: gap/overlap at boundary with predecessor.")
        if not (_dt(p.start_utc_iso) < _dt(p.end_utc_iso)):
            v.append(f"{p.period_id}: end must exceed start.")
        if len(p.antardashas) != 12:
            v.append(f"{p.period_id}: expected 12 antardashas.")
            continue
        if abs(sum(c.duration_years for c in p.antardashas) - p.duration_years) > 1e-9:
            v.append(f"{p.period_id}: antardasha years must sum to parent.")
        if abs(sum(c.duration_days for c in p.antardashas) - p.duration_days) > 1e-6:
            v.append(f"{p.period_id}: antardasha days must sum to parent.")
        if p.antardashas[0].start_utc_iso != p.start_utc_iso:
            v.append(f"{p.period_id}: first antar must start at parent start.")
        if p.antardashas[-1].end_utc_iso != p.end_utc_iso:
            v.append(f"{p.period_id}: last antar must end at parent end.")
        for j, c in enumerate(p.antardashas):
            if j > 0 and c.start_utc_iso != p.antardashas[j - 1].end_utc_iso:
                v.append(f"{c.period_id}: antar gap/overlap.")
            if c.parent_id != p.period_id:
                v.append(f"{c.period_id}: parent linkage broken.")
    if result.provenance.get("source_reference") != "UNVERIFIED":
        v.append("Provenance source_reference must be UNVERIFIED.")
    if result.provenance.get("confidence") != "TRADITION_DEPENDENT":
        v.append("Provenance confidence must be TRADITION_DEPENDENT.")
    return sorted(v)
