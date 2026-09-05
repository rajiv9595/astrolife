# ASTROLIFE V2 — PHASE 8 TIMING

## 1. Windows (§22)

`TimingWindow{start, end, precision, source_signals, exact_events,
uncertainty, profile, provenance}`. ISO strings, half-open `[start, end)`
matching timing-architecture conventions. Precision ladder:
EXACT > DAY > WEEK > MONTH > DATE_RANGE > DASHA_RANGE > UNKNOWN.
Dasha rows arrive as DASHA_RANGE; exact canonical roots arrive EXACT.

## 2. Algebra (§23)

intersection (None when empty; touching bounds do not overlap; exact point
in range stays EXACT), union (unbounded dominates), contains (start
inclusive, end exclusive; None when undecidable), overlap, distance (gap
days, 0.0 when overlapping, None when unbounded-indeterminate), clip to
request bounds. Overlapping independent windows merge narrower; disjoint
windows are preserved side by side — never force-intersected.

## 3. Sources (§§9–12, 24)

Vimshottari MD/AD rows (PD absent → no approximation, UNKNOWN by
construction), Chara rows per explicit profile, transit facts + verbatim
root timestamps, rule-activation booleans. Only canonical transit-natal
relationships represented in supplied facts are used; no aspect formula
added; rounded values never feed calculations.
