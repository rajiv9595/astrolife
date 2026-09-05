# ASTROLIFE V2 — PHASE 10 — TEST REPORT

## Phase 10 suite: 993 / 993 PASS (`backend/test_regression_phase10.py`)
D1 anchors 58, invariants 48, synthetic ascendants 25, Vargas 144,
boundaries 80, D9 108, D10 120, D60 61, Panchanga 6, Vimshottari 16,
transit 2, Chara 17, strength 32, yoga 62, dosha 24, Jaimini 22, Jaimini
rules 13, dynamic rules 9, evidence 6, research 8, agents 11, prediction 5,
metamorphic 9, cross-layer 8, fingerprints 4, tolerance 6, mutation 8,
security 30, API 10, snapshots 14, e2e/determinism 5, concurrency 2, order
2, unknown/invalid 7, firewalls 12, immutability 4. Zero failures; every
check asserts an independent behavior against frozen goldens or invariants.

## Full regression accounting (§48)
| Scope | Executed | Unique |
|---|---|---|
| Prior baseline (Phases 1–9) | 104,528 | 104,490 |
| Phase 10 (NEW) | 993 | 993 |
| **Total** | **105,521** | **105,483** |

CARRIED-FORWARD 0, FAILURES 0, SKIPPED 0, XFAILED 0. All prior suites
re-executed in-session (39 / 19,692 / 82,521 / 87 / 185 / 355 / 157 / 143 /
62 / 57 / 38 / 62 / 57 / 48 / 51 / 115 / 86 / 105 / 176 / 211 / 281). Nothing
deleted, weakened, or suppressed; no goldens rewritten.

## Performance (§49, ms per stage)
Chart ~480 cold / ~1 warm; Vargas ~2; dynamic state ~2,440; strength
~1,440; yoga ~6; dosha ~1; Jaimini ~1; full Phase 10 suite ~4–6 min
(dominated by 50-run determinism + 13 chart builds + transit searches).
Correctness was never traded for speed.

## Static audit (§50)
Regression code calls canonical systems only; no duplicated formulas, no
ML/LLM, no eval/exec. Golden change control (§34): no `--update-golden`
exists; frozen values immutable by default.

## Discrepancies (§55–57)
None. All §60 protected goldens (JD, ayanamsha, ascendant, Moon, Ketu
opposition, karakas, Karakamsha, AL/UL, strength table, yoga/dosha sets,
Chara profiles, Phase 8/9 semantics) reproduced exactly.
