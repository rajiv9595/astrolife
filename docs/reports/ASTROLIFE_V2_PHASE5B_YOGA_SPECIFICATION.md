# ASTROLIFE V2 — PHASE 5B — YOGA SPECIFICATION

## 1. Architecture (unchanged from Phase 5A)

```
Canonical Calculation → Varga Facts → Strength Facts → RuleContext
  → Deterministic Yoga Formation → Strength Evaluation
  → Cancellation / Mitigation → Evidence → (future) AI Explanation
```

- Package: `backend/core/rules/parashari/` (`__init__`, `structural`,
  `catalog`, `raja_yoga`, `dhana_yoga`, `mahapurusha`, `major_yogas`,
  `parivartana`, `viparita`, `neecha_bhanga`, `special_yogas`,
  `exceptions`, `strength`, `fixtures`, `crosscheck`, `manifest.json`,
  `golden_snapshot.json`, `crosscheck.json`).
- Reuses Phase 5A `RuleDefinition`, `RuleContext`, `RuleResult`,
  `Condition`, `Evidence`, `Provenance`, `RuleRegistry`, `RuleEvaluator`.
  No rule-engine infrastructure was duplicated.
- Formation is evaluated through registered custom evaluators
  (`FORMATION_EVALUATORS`, one per yoga, pure functions of `RuleContext`).
  `EvaluationConfig`: formation ON, strength OFF (graded separately, see §3),
  activation OFF (`NOT_EVALUATED` by design — no prediction yet),
  cancellation/mitigation ON via `exceptions.py`.
- No LLM calls, no `eval`/`exec`, no astronomy, no Western aspects anywhere
  in the package (guarded by test).

## 2. Implemented catalogue (31 rules, all `category = YOGA`)

| # | rule_id | tradition | method | confidence |
|---|---|---|---|---|
| 1 | PARASHARI.YOGA.RAJA_KENDRA_TRIKONA | PARASHARI_CLASSICAL | kendra_trikona_sambandha | HIGH |
| 2 | PARASHARI.YOGA.DHARMA_KARMADHIPATI | PARASHARI_CLASSICAL | sambandha_9_10 | HIGH |
| 3 | PARASHARI.YOGA.YOGAKARAKA_RAJA | PARASHARI_CLASSICAL | yogakaraka_in_kendra_trikona | HIGH |
| 4 | PARASHARI.YOGA.DHANA_2_11 | PARASHARI_CLASSICAL | sambandha_2_11 | HIGH |
| 5 | PARASHARI.YOGA.DHANA_5_9 | PARASHARI_CLASSICAL | sambandha_5_9 | HIGH |
| 6 | PARASHARI.YOGA.DHANA_LAGNA_WEALTH | PARASHARI_CLASSICAL | sambandha_lagna_wealth | HIGH |
| 7 | PARASHARI.YOGA.RUCHAKA | PARASHARI_CLASSICAL | mahapurusha_kendra_own_exalted | HIGH |
| 8 | PARASHARI.YOGA.BHADRA | PARASHARI_CLASSICAL | mahapurusha_kendra_own_exalted | HIGH |
| 9 | PARASHARI.YOGA.HAMSA | PARASHARI_CLASSICAL | mahapurusha_kendra_own_exalted | HIGH |
| 10 | PARASHARI.YOGA.MALAVYA | PARASHARI_CLASSICAL | mahapurusha_kendra_own_exalted | HIGH |
| 11 | PARASHARI.YOGA.SASA | PARASHARI_CLASSICAL | mahapurusha_kendra_own_exalted | HIGH |
| 12 | PARASHARI.YOGA.GAJA_KESARI | PARASHARI_CLASSICAL | kendra_from_moon_house | HIGH |
| 13 | PARASHARI.YOGA.BUDHA_ADITYA | PARASHARI_CLASSICAL | same_house_conjunction | HIGH |
| 14 | PARASHARI.YOGA.CHANDRA_MANGALA | PARASHARI_CLASSICAL | same_house_conjunction | HIGH |
| 15 | PARASHARI.YOGA.ADHI | TRADITION_DEPENDENT | benefic_678_from_moon_any | TRADITION_DEPENDENT |
| 16 | PARASHARI.YOGA.LAKSHMI | TRADITION_DEPENDENT | ninth_lord_strong_plus_lagna | TRADITION_DEPENDENT |
| 17 | PARASHARI.YOGA.SARASWATI | PARASHARI_CLASSICAL | benefic_trio_kendra_trikona | MEDIUM |
| 18 | PARASHARI.YOGA.AMALA | PARASHARI_CLASSICAL | benefic_tenth_from_lagna | MEDIUM |
| 19 | PARASHARI.YOGA.VASUMATI | TRADITION_DEPENDENT | benefics_in_upachaya_count | TRADITION_DEPENDENT |
| 20 | PARASHARI.YOGA.SUNAPHA | PARASHARI_CLASSICAL | planet_2nd_from_moon | HIGH |
| 21 | PARASHARI.YOGA.ANAPHA | PARASHARI_CLASSICAL | planet_12th_from_moon | HIGH |
| 22 | PARASHARI.YOGA.DURUDHARA | PARASHARI_CLASSICAL | planets_2nd_and_12th_from_moon | HIGH |
| 23 | PARASHARI.YOGA.KEMADRUMA | PARASHARI_CLASSICAL | classical_isolation | HIGH |
| 24 | PARASHARI.YOGA.PARIVARTANA_MAHA | PARASHARI_CLASSICAL | parivartana_maha | HIGH |
| 25 | PARASHARI.YOGA.PARIVARTANA_KHALA | PARASHARI_CLASSICAL | parivartana_khala | HIGH |
| 26 | PARASHARI.YOGA.PARIVARTANA_DAINYA | PARASHARI_CLASSICAL | parivartana_dainya | HIGH |
| 27 | PARASHARI.YOGA.VIPARITA_HARSHA | PARASHARI_CLASSICAL | viparita_harsha_6L_in_dusthana | HIGH |
| 28 | PARASHARI.YOGA.VIPARITA_SARALA | PARASHARI_CLASSICAL | viparita_sarala_8L_in_dusthana | HIGH |
| 29 | PARASHARI.YOGA.VIPARITA_VIMALA | PARASHARI_CLASSICAL | viparita_vimala_12L_in_dusthana | HIGH |
| 30 | PARASHARI.YOGA.NEECHA_BHANGA | PARASHARI_CLASSICAL | neecha_bhanga_C1_C7 | HIGH |
| 31 | PARASHARI.YOGA.NEECHA_BHANGA_RAJA | PARASHARI_CLASSICAL | neecha_bhanga_raja_kendra_trikona | HIGH |

All carry `source_reference = UNVERIFIED` (no fabricated verses; traditional
attribution in provenance notes — see SOURCE_AUDIT). Hence VERIFIED = 0 by
design; HIGH = 23, MEDIUM = 3 (Saraswati, Amala + C5–C7 note), TRADITION_DEPENDENT = 5.

## 3. Formation conditions (per yoga)

- **Raja Kendra-Trikona**: any Kendra lord (1,4,7,10) + Trikona lord (1,5,9),
  different planets, with `sambandha_kind` ∈ conjunction (same whole-sign
  house or ≤8° orb) / mutual Parashari aspect / sign exchange. Same-house
  pair (1,1) skipped. Shared-lord case needs Kendra/Trikona occupancy.
- **Dharma-Karmadhipati**: 9L–10L sambandha as above; evidence records
  `relationship_type` (conjunction/mutual_aspect/exchange/same_lord_*).
- **Yogakaraka Raja**: functional Yogakaraka (Phase 4) that rules a
  non-Lagna Kendra (4/7/10) AND non-Lagna Trikona (5/9), placed in
  Kendra/Trikona. Lagna-lord-only cases (e.g. Taurus Venus 1+6) excluded.
- **Dhana ×3**: (2L–11L), (5L–9L), (LagnaL with 2/5/9/11L) sambandha.
- **Mahapurusha ×5**: planet in Kendra from Lagna AND own sign OR exalted.
  Moolatrikona alone never qualifies (tested: Venus/Libra 15° boundary).
- **Gaja Kesari**: Jupiter in Kendra houses from Moon (whole-sign offset
  0/3/6/9). No strength gate in formation (debilitated-Jupiter test proves
  FORMED + non-STRONG separation).
- **Budha-Aditya / Chandra-Mangala**: same whole-sign house; orb recorded.
  Mutual-aspect variant omitted (documented).
- **Adhi**: any of Jupiter/Venus/Mercury in 6/7/8 from Moon (lenient,
  TRADITION_DEPENDENT; strict all-three variant documented).
- **Lakshmi**: 9L in Kendra/Trikona in own/exalted dignity AND Lagna lord
  strong (own/exalt/MTK/KT/Shadbala ≥ 1).
- **Saraswati**: Jupiter + Venus + Mercury all in Kendra/Trikona.
- **Amala**: natural benefic in 10th from Lagna (Moon variant omitted).
- **Vasumati**: ≥3 of Jupiter/Venus/Mercury/Moon in Upachaya (3,6,10,11).
- **Sunapha/Anapha/Durudhara**: planets excl. Sun/Rahu/Ketu in 2nd / 12th /
  both from Moon. **Kemadruma**: 2nd & 12th empty AND none in Kendra from
  Moon (same exclusions).
- **Parivartana**: mutual sign occupation; classified DAINYA (6/8/12
  lordship) > KHALA (3rd lord) > MAHA (`method=house_role`).
- **Viparita**: 6L/8L/12L respectively in Dusthana (6,8,12). No
  conjunction/exchange variants.
- **Neecha Bhanga**: debilitated planet + ≥1 of C1–C7 (C1 dep-lord Kendra
  Lagna; C2 dep-lord Kendra Moon; C3 ex-lord Kendra Lagna; C4 ex-lord Kendra
  Moon; C5 exalting planet Kendra Lagna/Moon; C6 aspect of dep/ex lord;
  C7 exchange with dep lord). **NBRY**: bhanga + planet in Kendra/Trikona.
  D9 never consulted in formation (D9 recorded only as strength modifier).

## 4. Strength (separate from formation)

`strength.py::evaluate_yoga_strength` counts explicit D1 factors per relevant
planet (DIGNITY_STRONG = exalted/own/MTK; SHADBALA_STRONG = ratio ≥ 1.0;
HOUSE_STRONG = Kendra/Trikona). STRONG: ≥2 strong planets or one planet with
all three; MODERATE: any factor; WEAK: none. D9 dignity is evidence-only and
can never promote WEAK → STRONG. No weighted YogaScore exists.

## 5. Cancellation / mitigation (separate, evidence-backed)

`exceptions.py`: cancellation triggers = uncancelled debilitation,
Dusthana placement, unrelieved malefic co-habitation (→ PARTIAL via
`is_partial`); mitigation = benefic conjunction/aspect, strong dignity,
Kendra/Trikona placement. Formation evidence is never overwritten.

## 6. Varga usage

Vargas consulted ONLY as strength modifiers (D9 dignity in strength
evidence). No formation reads any Varga. No Varga weighting.

## 7. Aspects and lordship

Parashari aspects exclusively via `RuleContext` (all-planets 7th + Mars
4/7/8, Jupiter 5/7/9, Saturn 3/7/10). House lordship and Yogakaraka status
from the validated Phase 4 functional engine; never re-implemented per yoga
(all 12 ascendants swept in tests).

## 8. Legacy discrepancies found and corrected

1. Legacy `raja_yoga_9_10` self-matches when one planet rules both houses
   (golden Saturn 9+10) — corrected with shared-lord KT rule.
2. Legacy `dhana_yoga_check` (any wealth-lord contact) replaced by three
   explicit sambandha rules.
3. Legacy `neechabhanga_check` omits Moon-kendra/aspect/exchange paths —
   replaced by C1–C7.
4. Legacy `parivartana_*` filters replaced by detector + house_role
   classification.
5. Legacy weighted scores (formation⇄strength conflation) removed; formation,
   strength, cancellation, mitigation are independent statuses.
6. Cross-check on golden chart: 15 MATCH, 3 CONVENTION_DIFFERENCE
   (Dharma-Karmadhipati self-match artifact; Adhi strict-vs-lenient;
   Kemadruma isolation), 0 ASTROLIFE_BUG, 0 UNRESOLVED
   (`crosscheck.json`).

## 9. Evidence, confidence, versioning

Every FORMED result carries ≥2 evidence items (lordship relationship +
dignity/strength/house), `relationship_type`/`class`/`condition` details,
provenance (`source_reference = UNVERIFIED` + method), confidence per table,
rule version `1.0.0`, engine version `5.1.0`. Activation is always
`NOT_EVALUATED` (no timing/prediction in this phase).

## 10. Known limitations

- Zero VERIFIED confidences (honest UNVERIFIED references; verse-level
  verification deferred to a text-scholar pass).
- Omitted ~60 legacy-JSON names (Vesi/Vasi/Ubhayachari, Sakata, Kahala,
  Chamara, Matsya/Kurma/Parvata, Brahma/Vishnu/Shiva complexes, Pushkala,
  Kalpadruma, Akhanda Samrajya, …) — audited, not promoted.
- Strength grading is an explicit Astrolife assessment rule, not a
  classical formula; kept separate from formation by design.
