# ASTROLIFE V2 — PHASE 10 — MUTATION TESTING

All mutations apply to in-memory deep copies only; production files are
never mutated. Detection = check passes on original, fails on mutated copy.

| Mutation | Detector | Result |
|---|---|---|
| Longitude +1° | abs-diff < 1e-9 | DETECTED |
| House 4→5 | equality | DETECTED |
| Varga sign Leo→Cancer | equality | DETECTED |
| Dasha lord Moon→Sun | equality | DETECTED |
| Karaka AK→AmK | equality | DETECTED |
| Yoga formation FORMED→NOT_FORMED | equality | DETECTED |
| Evidence condition ALL→ANY | equality | DETECTED |
| Tautology control (always-true check) | — | correctly NOT flagged |

Discrepancy workflow (§55–57): no discrepancies occurred, so no
Discrepancy records were needed. Had any accepted golden failed, the suite
would have stopped before changing it and reported expected/actual/
difference/first-divergent-layer/downstream/cause/verdict — with downstream
differences labeled DERIVED, never independent bugs.
