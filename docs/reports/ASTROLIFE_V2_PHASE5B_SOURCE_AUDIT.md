# ASTROLIFE V2 — PHASE 5B — SOURCE AUDIT

## Purpose

Independent audit of classical authority for every Parashari Yoga candidate
before implementation. Existing Astrolife code (`backend/yoga_evaluator.py`,
`backend/rulesets/yogas/*.json`) was treated as implementation reference
only — NOT as source of truth. Rule specifications below were validated
against classical structure, then cross-checked against the legacy
implementation. Discrepancies are recorded in §8.

## Method

- Prioritised primary classical texts: Brihat Parashara Hora Shastra (BPHS),
  Brihat Jataka, Phaladeepika, Saravali, Jataka Parijata.
- Secondary/modern references used only for cross-checking.
- No chapter/verse number is asserted unless directly verified against a
  text available to the project. Because exact editions vary (Giridhara /
  Sitaram Jha / R. Santhanam translations number chapters differently),
  every rule in this phase carries `source_reference = UNVERIFIED` with the
  traditional attribution recorded in `notes`. This is deliberate honesty,
  not an omission.
- Confidence follows Phase 5A model: VERIFIED only where formation is
  uniform across traditions AND directly checked; HIGH where the structure
  is uniform but the exact verse was not re-verified here; MEDIUM where
  details vary; TRADITION_DEPENDENT where schools disagree; EXPERIMENTAL
  never used for classical yogas (reserved for modern proposals, none
  implemented).

## Findings per Yoga

### A. Raja Yogas
| Yoga | Classical basis | Interpretation chosen | Alternatives / notes | Confidence |
|---|---|---|---|---|
| Kendra-Trikona lord sambandha | BPHS Raja Yoga adhyaya (trad. attrib.); Phaladeepika Ch.6-type Raja discussion; Saravali Raja chapters | Formation = lord of a Kendra (1,4,7,10) and lord of a Trikona (1,5,9), different planets, in sambandha = conjunction (same house / ≤8°) OR mutual Parashari aspect OR sign exchange. Same-planet (e.g. Taurus Saturn 9+10) counts only if that planet occupies Kendra/Trikona. | Some schools count any of 5 sambandhas (conjunction, aspect, exchange, mutual kendra, mutual trikona); we implement the 3 sambandhas most uniformly attested and document the narrower choice. | HIGH |
| Yogakaraka Raja | BPHS functional lordship doctrine (Kendra+Trikona lord = Yogakaraka) | Formation = Yogakaraka planet (per Phase 4 functional engine) placed in Kendra or Trikona. | Universally accepted structurally; result strength debated. | HIGH |
| Dharma-Karmadhipati (9L-10L) | BPHS Raja Yoga adhyaya (trad.: Ch.41-type in some editions) | Formation = 9th and 10th lords in conjunction / mutual aspect / exchange. Same-planet case → requires Kendradhi/Trikona placement. Evidence records `relationship_type`. Strength differs by type (conjunction generally strongest) but formation is equal. | Mutual kendra/trikona occupancy without aspect is claimed by some authors — NOT implemented; documented as omitted variant. | HIGH |

### B. Dhana Yogas
| Yoga | Classical basis | Interpretation | Notes | Confidence |
|---|---|---|---|---|
| Dhana 2-11 | BPHS / Phaladeepika Dhana chapters (trad. attrib.) | 2nd & 11th lords in sambandha (conjunct/mutual aspect/exchange). | Simplistic "2+11 always Dhana" rejected; sambandha required. | HIGH |
| Dhana 5-9 | Same family | 5th & 9th lords in sambandha. | Trikona-pair wealth. | HIGH |
| Dhana Lagna-wealth | Same family | Lagna lord in sambandha with any of 2/5/9/11 lords. | Lagna involvement required; documented. | HIGH |

### C. Pancha Mahapurusha (Ruchaka/Bhadra/Hamsa/Malavya/Sasa)
- Classical basis: BPHS Mahapurusha adhyaya; Brihat Jataka Ch.7-type; Phaladeepika; Saravali. Uniformly: Mars/Mercury/Jupiter/Venus/Saturn respectively, in own sign or exaltation, in Kendra from Lagna (some editions: from Lagna AND Moon — we implement Lagna, the dominant Parashari reading, and document the Moon-variant as omitted).
- Formation = planet in Kendra (1,4,7,10 from Lagna) AND (own sign OR exalted). Moolatrikona alone does NOT qualify. Combustion/affliction modifies strength/cancellation, never formation.
- Confidence: HIGH (structure uniform; exact verse UNVERIFIED per rule above).

### D. Major yogas
| Yoga | Chosen definition (`method`) | Alternatives documented | Confidence |
|---|---|---|---|
| Gaja Kesari (`kendra_from_moon_house`) | Jupiter in Kendra (1,4,7,10 houses) from Moon, counted by whole-sign houses from Moon's house. No added strength gate in formation. | Variant requiring waxing/strong Moon; variant counting exact degrees; South-Indian stricter dignity gates — all recorded, not merged. | HIGH |
| Budha-Aditya (`same_house_conjunction`) | Sun+Mercury in same house (whole sign). Orb recorded as evidence; formation is house-based per classical usage. | Combustion-based cancellation handled in exceptions, not formation. | HIGH |
| Chandra-Mangala (`same_house_conjunction`) | Moon+Mars same house. | Some texts accept mutual aspect — implemented as formation too? NO: aspect recorded as evidence but formation requires same-house conjunction; aspect variant documented as omitted. Corrected during audit (legacy `dhana_yoga_check`-style looseness rejected). | HIGH |
| Adhi (`benefic_678_from_moon_any`) | Any of Jupiter/Venus/Mercury in 6th/7th/8th house from Moon. | Strict reading demands benefics in ALL THREE houses; another demands freedom from malefic association. Implemented the widely-used "any" reading, labelled TRADITION_DEPENDENT. | TRADITION_DEPENDENT |
| Lakshmi (`ninth_lord_strong_plus_lagna`) | 9th lord in Kendra/Trikona in own/exalted dignity AND Lagna lord strong (own/exalt/kendra-trikona/shadbala). | Several competing Lakshmi definitions exist (Venus+9L variants) — documented; only this high-consensus form implemented. | TRADITION_DEPENDENT |
| Saraswati (`benefic_trio_kendra_trikona`) | Jupiter+Venus+Mercury all in Kendra/Trikona from Lagna. | Jataka Parijata variants add dignity gates — documented, not imposed on formation. | MEDIUM |
| Amala (`benefic_tenth_from_lagna`) | Natural benefic in 10th from Lagna. | Moon-variant (10th from Moon) documented as omitted alternative. | MEDIUM |
| Vasumati (`benefics_in_upachaya_count`) | ≥3 of Jupiter/Venus/Mercury/waxing-Moon in Upachaya (3,6,10,11). | "All benefics in Upachaya" strict reading documented. | TRADITION_DEPENDENT |
| Sunapha / Anapha / Durudhara | Planets (excl. Sun, Rahu, Ketu) in 2nd / 12th / both from Moon. | Mars/Saturn-only variants rejected. | HIGH |
| Kemadruma (`classical_isolation`) | No planet (excl. Sun/Rahu/Ketu) in 2/12 from Moon AND none in Kendra from Moon AND Moon not in Kendra from Lagna companion conditions per strict reading? Chosen: 2nd & 12th from Moon empty AND no planet in Kendra from Moon (excl. Sun/Rahu/Ketu). | Many cancellations (handled in exceptions). Kemadruma treated as a Yoga-category dosha-like combination per classical catalogues; kept under YOGA with cancellation. | HIGH |

### E. Parivartana
- Detector: A occupies B's sign AND B occupies A's sign (sign-lord table).
- Classification `method=house_role`: DAINYA if either planet rules 6/8/12; else KHALA if 3rd lord involved; else MAHA (both rule Kendra/Trikona/2/11/1 houses). Documented simplification of longer classical lists; no modern invention.
- Confidence HIGH.

### F. Viparita (Harsha/Sarala/Vimala)
- Formation: 6th / 8th / 12th lord respectively placed in a Dusthana house (6,8,12). Conjunction/exchange variants NOT counted as formation (documented omission). "Any dusthana lord anywhere in dusthana = Viparita" rejected — lord-house pairing is explicit.
- Confidence HIGH.

### G. Neecha Bhanga / Neecha Bhanga Raja Yoga
- Separated: DEBILITATED (dignity fact) ≠ NEECHA_BHANGA (≥1 classical cancellation) ≠ NEECHA_BHANGA_RAJA_YOGA (bhanga + planet in Kendra/Trikona from Lagna).
- Cancellation conditions implemented (each evidence-backed): C1 debilitation-lord in Kendra from Lagna; C2 debilitation-lord in Kendra from Moon; C3 exaltation-lord in Kendra from Lagna; C4 exaltation-lord in Kendra from Moon; C5 exalted planet (the planet that exalts in that sign) in Kendra from Lagna/Moon; C6 aspect of debilitation/exaltation lord on the debilitated planet; C7 sign exchange with debilitation lord. D9 strength alone is NEVER a bhanga (explicitly excluded).
- Confidence HIGH for the separation and C1–C4; MEDIUM for C5–C7 (commentarial variance, documented).

## Omitted candidates (deliberately NOT implemented as VERIFIED)
Vesi/Vasi/Ubhayachari, Sakata, Kahala, Chamara, Matsya/Kurma/Parvata families,
Brahma/Vishnu/Shiva/Hari/Hara/Gandharva/Indra complexes, Pushkala, Kalpadruma,
Akhanda Samrajya, Mridanga, Kusuma, Ravi, Kalanidhi/Nipuna, Parijata/Suparijata,
Kedara/Shula/Pasha/Musala/Yuga/Gola, Dama/Astra/Kama/Asura/Bhagya/Dhenu/Go/Jaladhi/
Khyati/Shaalya etc. Reason: definitions vary widely between the legacy JSON
rulesets and modern lists; no single high-consensus Parashari form could be
established without verse-level verification. Counted as UNVERIFIED/omitted,
not as failures.

## Counts
- Implemented yogas: 31.
- HIGH: 23. MEDIUM: 3. TRADITION_DEPENDENT: 5. VERIFIED: 0 (by the
  no-fabrication rule — all carry `source_reference = UNVERIFIED`).
  This is intentional: correctness and traceability over inflated confidence.
- Omitted/unverified candidates: ~60 legacy JSON names not promoted.

## Legacy cross-check summary
- Legacy `yoga_evaluator.py` predicate engine and `rulesets/yogas/*.json`
  conflate formation with strength (weighted scores), use whole-sign
  approximations inconsistently, and merge variant definitions silently
  (e.g. `dhana_yoga_check` = any wealth-lord contact; `parivartana_*`
  filters differ from classical house roles; `neechabhanga_check` omits
  Moon-kendra and aspect/exchange conditions). All such cases were
  re-specified from the classical structure above; §8 of the Specification
  records each discrepancy and the correction applied.
