# ASTROLIFE V2 — PHASE 5D: JAIMINI FOUNDATION & DETERMINISTIC FACT SPECIFICATION

**Author:** DeepMind Advanced Agentic Coding  
**Status:** VALIDATED BASELINE & COMPLETE  
**Version:** 2.0.0  
**Phase:** 5D — Jaimini Foundation & Deterministic Fact Engine  

---

## 1. Executive Summary & Objective

Phase 5D establishes the **pure, deterministic mathematical and structural fact layer** for the Jaimini astrological system (`backend/core/jaimini/`). It strictly consumes validated canonical facts (`ChartFacts` from Phase 1 and `VargaFacts` from Phase 2) without recalculating astronomy or divisional positions, and without executing predictive, event-timing, or AI logic.

```
Canonical ChartFacts (D1 Sidereal Longitudes) + VargaFacts (D9 Navamsha)
                                ↓
                 Jaimini Deterministic Fact Engine
  [Chara Karakas, Rashi Drishti, Arudha Padas, Upapada, Karakamsha]
                                ↓
                       JaiminiFacts Layer
                                ↓
                   (Future Jaimini Rule Engine)
```

---

## 2. Architecture & Directory Structure

The Jaimini fact engine is isolated in `backend/core/jaimini/`:

```
backend/core/jaimini/
├── __init__.py           # Unified exports
├── profile.py            # JaiminiCalculationProfile & configuration enums
├── models.py             # Pydantic data models for all Jaimini facts
├── karakas.py            # Chara Karaka ranking, Rahu conventions & tie-breaking
├── rashi_drishti.py      # Pure sign-based aspect matrix & propagation
├── arudha.py             # Reusable Arudha projection & 10th-house exceptions
├── padas.py              # Calculation of all 12 Arudha Padas (A1-A12)
├── upapada.py            # Dedicated Upapada Lagna (UL / A12) derivation
├── karakamsha.py         # Karakamsha & Swamsa fact extractor from D9
├── context.py            # Read-only JaiminiContext accessor
├── pipeline.py           # Pure pipeline: generate_jaimini_facts()
└── validators.py         # Integrity and boundary validators
```

---

## 3. Mathematical & Algorithmic Specifications

### 3.1 Chara Karakas (Significators)

Chara Karakas are variable planetary significators ranked by intra-sign longitude (degree inside the occupied sign: $0.0^\circ \le \theta < 30.0^\circ$), **not** absolute continuous longitude ($0^\circ - 360^\circ$).

#### Planetary Candidates
* **7-Karaka Scheme (`SEVEN_KARAKA`)**:
  Candidates = `Sun`, `Moon`, `Mars`, `Mercury`, `Jupiter`, `Venus`, `Saturn` (7 visible grahas). Rahu and Ketu are excluded.
  Roles (Descending Order):
  1. **Atmakaraka (AK)** — Self / Soul (Highest intra-sign degree)
  2. **Amatyakaraka (AmK)** — Mind / Intellect / Career / Counsel
  3. **Bhratrukaraka (BK)** — Siblings / Courage / Gurus
  4. **Matrukaraka (MK)** — Mother / Nurturance / Education
  5. **Putrakaraka (PK)** — Children / Intelligence / Creativity
  6. **Gnatikaraka (GK)** — Relatives / Obstacles / Strife
  7. **Darakaraka (DK)** — Spouse / Partners (Lowest intra-sign degree)

* **8-Karaka Scheme (`EIGHT_KARAKA`)**:
  Candidates = `Sun`, `Moon`, `Mars`, `Mercury`, `Jupiter`, `Venus`, `Saturn`, `Rahu`.
  Roles (Descending Order):
  1. `AK` — Atmakaraka
  2. `AmK` — Amatyakaraka
  3. `BK` — Bhratrukaraka
  4. `MK` — Matrukaraka
  5. `PiK` — **Pitrukaraka** (Father / Ancestors)
  6. `PK` — Putrakaraka
  7. `GK` — Gnatikaraka
  8. `DK` — Darakaraka

#### Rahu Handling Conventions
* `RahuKarakaMethod.EXCLUDED`: Rahu is omitted from ranking.
* `RahuKarakaMethod.DIRECT_LONGITUDE`: $\theta_{Rahu} = \lambda_{Rahu} \pmod{30.0}$.
* `RahuKarakaMethod.INVERSE_LONGITUDE`: $\theta_{Rahu} = (30.0 - (\lambda_{Rahu} \pmod{30.0})) \pmod{30.0}$ (measured from end of sign due to retrograde motion).

#### Deterministic Tie-Breaking
When $|\theta_1 - \theta_2| \le 10^{-7}$ (defined by `profile.float_tolerance`):
1. Precision tolerance handles floating point binary representation.
2. Canonical Graha Precedence fallback ensures strict determinism without relying on Python dictionary order:
   $$\text{Sun} \succ \text{Moon} \succ \text{Mars} \succ \text{Mercury} \succ \text{Jupiter} \succ \text{Venus} \succ \text{Saturn} \succ \text{Rahu}$$
3. Structured evidence records the exact tie condition and resolution.

---

### 3.2 Jaimini Rashi Drishti (Sign Aspects)

Unlike Parashari Graha Drishti (which is degree-based), Jaimini Rashi Drishti is **purely sign-based**. Signs aspect other signs based on their quadruplicity (Movable, Fixed, Dual):

1. **Movable (Chara) Signs** ($\{1, 4, 7, 10\}$: Aries, Cancer, Libra, Capricorn):
   Aspect all Fixed signs **except the adjacent fixed sign** (the next sign, 2nd house):
   * Aries ($1$) $\to$ Leo ($5$), Scorpio ($8$), Aquarius ($11$) [Excludes Taurus ($2$)]
   * Cancer ($4$) $\to$ Scorpio ($8$), Aquarius ($11$), Taurus ($2$) [Excludes Leo ($5$)]
   * Libra ($7$) $\to$ Aquarius ($11$), Taurus ($2$), Leo ($5$) [Excludes Scorpio ($8$)]
   * Capricorn ($10$) $\to$ Taurus ($2$), Leo ($5$), Scorpio ($8$) [Excludes Aquarius ($11$)]

2. **Fixed (Sthira) Signs** ($\{2, 5, 8, 11\}$: Taurus, Leo, Scorpio, Aquarius):
   Aspect all Movable signs **except the adjacent movable sign** (the previous sign, 12th house):
   * Taurus ($2$) $\to$ Cancer ($4$), Libra ($7$), Capricorn ($10$) [Excludes Aries ($1$)]
   * Leo ($5$) $\to$ Libra ($7$), Capricorn ($10$), Aries ($1$) [Excludes Cancer ($4$)]
   * Scorpio ($8$) $\to$ Capricorn ($10$), Aries ($1$), Cancer ($4$) [Excludes Libra ($7$)]
   * Aquarius ($11$) $\to$ Aries ($1$), Cancer ($4$), Libra ($7$) [Excludes Capricorn ($10$)]

3. **Dual (Dvisvabhava) Signs** ($\{3, 6, 9, 12\}$: Gemini, Virgo, Sagittarius, Pisces):
   Aspect all other Dual signs **except themselves**:
   * Gemini ($3$) $\to$ Virgo ($6$), Sagittarius ($9$), Pisces ($12$)
   * Virgo ($6$) $\to$ Gemini ($3$), Sagittarius ($9$), Pisces ($12$)
   * Sagittarius ($9$) $\to$ Gemini ($3$), Virgo ($6$), Pisces ($12$)
   * Pisces ($12$) $\to$ Gemini ($3$), Virgo ($6$), Sagittarius ($9$)

#### Aspect Matrix Properties
* **Exact Cardinality**: Every sign aspects exactly $3$ signs and has $8$ non-aspected signs.
* **Mutual Symmetry**: If Sign $A$ aspects Sign $B$, then Sign $B$ unconditionally aspects Sign $A$ ($100\%$ symmetric across all $144$ sign pairs).
* **Planetary Propagation**: A planet situated in sign $S$ casts Rashi Drishti on all signs aspected by $S$ and on all planets situated in those aspected signs.

---

### 3.3 Arudha Padas & Classical 10th-House Exceptions

The Arudha Pada ($A_n$) of house $n$ represents the projected image of that house:

1. Let $S_H \in \{0..11\}$ be the source sign of house $n$.
2. Let $L$ be the lord of $S_H$, situated in lord sign $S_L \in \{0..11\}$.
3. Distance in signs: $D = (S_L - S_H) \pmod{12}$.
4. Raw projected sign: $S_{raw} = (S_L + D) \pmod{12} = (S_H + 2D) \pmod{12}$.
5. **Classical 10th-House Exception Rules (method label `CLASSICAL_ARUDHA_STANDARD`; exact verse references UNVERIFIED)**:
   * **1st House Fall**: If $S_{raw} = S_H$ (occurs when lord is in $1\text{st}$ or $7\text{th}$ from house):
     $$S_{final} = (S_H + 9) \pmod{12} \quad (\text{10th house from source})$$
   * **7th House Fall**: If $S_{raw} = (S_H + 6) \pmod{12}$ (occurs when lord is in $4\text{th}$ or $10\text{th}$ from house):
     $$S_{final} = (S_H + 3) \pmod{12} \quad (\text{10th house from 7th} = \text{4th house from source})$$
   * **Standard Case**: Otherwise, $S_{final} = S_{raw}$.

> **Phase 5D-H hardening note (single source of truth).** `calculate_single_arudha`
> (`backend/core/jaimini/arudha.py`) computes `distance_signs`, `raw_proj_idx`,
> and the exception from one code path and builds the evidence strings from those
> same variables — calculation, evidence, and documentation share one formula.
> Inclusive house-count ($D + 1$) is reported alongside 0-indexed sign distance
> ($D$) and both feed the same projection; there are no separate formulas.

#### Golden chart A1 derivation (engine-generated, exception = NONE)

* Source: 1st house / Taurus ($S_H = 1$).
* Lord: Venus; lord placement: Virgo ($S_L = 5$).
* Sign distance: $D = (5 - 1) \pmod{12} = 4$ signs (5 houses inclusive).
* Raw projection: $S_{raw} = (5 + 4) \pmod{12} = 9$ = Capricorn.
* Exception: NONE (raw Capricorn is neither Taurus nor 7th-from-Taurus Scorpio).
* Final A1 (AL) = Capricorn.

#### Golden chart UL derivation (engine-generated, 1st-house exception)

* Source: 12th house / Aries; lord Mars placed in Aries ($D = 0$).
* Raw projection Aries falls in the source house → 10th-from-source exception →
  final UL (A12) = Capricorn. UL is identically the A12 pada (`upapada ==
  arudha_padas[12]` invariant, validator-enforced).

#### Arudha Padas (A1 to A12)
* **A1 (AL)**: Arudha Lagna (Bhava Pada)
* **A2**: Dhana Pada (Kosa Pada)
* **A3**: Bhratru Pada (Vikrama Pada)
* **A4**: Matru Pada (Sukh Pada)
* **A5**: Putra Pada (Mantra Pada)
* **A6**: Satru Pada (Roga Pada)
* **A7**: Dara Pada (Kalatra Pada)
* **A8**: Mrityu Pada (Randhra Pada)
* **A9**: Dharma Pada (Bhagya Pada)
* **A10**: Karma Pada (Rajya Pada)
* **A11**: Labha Pada
* **A12 (UL)**: Upapada Lagna (Gauna Pada)

---

### 3.4 Upapada Lagna (UL / A12)

Upapada is derived from the $12\text{th}$ house using the canonical Arudha algorithm. It is distinctly modeled in `UpapadaDetails` with complete provenance and step-by-step mathematical evidence.

---

### 3.5 Karakamsha & Swamsa

* **Karakamsha Sign**: The Navamsha (D9) sign occupied by the identified Atmakaraka (AK).
* **Swamsa Terminology**:
  * `karakamsha_sign`: D9 sign of Atmakaraka (classical Parasara & Sanjay Rath).
  * `swamsa_navamsha_lagna_sign`: D9 Ascendant sign (Navamsha Lagna).
* **Zero Recalculation**: Consumes validated D9 positions from `varga_facts["planets"][ak]["D9"]` and `varga_facts["ascendant"]["D9"]`.

---

## 4. Calculation Profiles (`JaiminiCalculationProfile`)

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `karaka_method` | `KarakaMethod` | `SEVEN_KARAKA` | 7 or 8 Chara Karaka scheme |
| `rahu_karaka_method` | `RahuKarakaMethod` | `EXCLUDED` | Excluded, Direct longitude, or Inverse longitude |
| `rashi_drishti_method`| `RashiDrishtiMethod` | `JAIMINI_CLASSICAL` | Classical movable/fixed/dual aspect rules |
| `arudha_method` | `ArudhaMethod` | `PARASHARI_JAIMINI_STANDARD` | Distance projection with 10th-house exceptions |
| `upapada_method` | `UpapadaMethod` | `UPAPADA_12TH_HOUSE` | Derived from 12th house |
| `co_lord_method` | `CoLordMethod` | `SINGLE_LORD_CLASSICAL` | Single classical lordships (Mars for Sco, Sat for Aqu) |
| `float_tolerance` | `float` | `1e-7` | Epsilon for intra-sign degree equality check |
| `source_tradition` | `str` | `"Jaimini Sutras / BPHS"` | Textual authority |
| `version` | `str` | `"2.0.0"` | Implementation version |

---

## 5. Provenance & Verification Gate

All calculations produce structured evidence and classical provenance:

* **Tradition / method / reference:** `tradition = JAIMINI`,
  `method = CLASSICAL_ARUDHA_STANDARD`, `source_reference = UNVERIFIED`.
  Exact verse numbers are not cited because exact textual references have not
  been verified. The profile enum value `ArudhaMethod.PARASHARI_JAIMINI_STANDARD`
  is retained for API stability and maps to this method label in
  `JaiminiFacts.metadata`.
* **Determinism**: 100 consecutive runs tested with bit-for-bit identical hashes.
* **No AI / No Prediction**: Zero machine learning or predictive logic in the fact engine.

---

## 6. Phase 5D-H Hardening Record (2026-09-04)

* Arudha arithmetic audited against an independent reference implementation over
  all 144 house-1 source/lord permutations: 24 first-house exceptions, 24
  seventh-house exceptions, 96 no-exception cases — 144/144 match on
  `distance_signs`, `raw_projected_sign`, `exception_applied`, and `final_sign`,
  with evidence strings verified to contain the computed signs.
* Golden A1 evidence revalidated: Taurus → Venus in Virgo → 5-house inclusive
  count (4 signs) → raw Capricorn → exception NONE → final Capricorn.
* No "raw Pisces" defect exists in the engine: calculation, evidence, and final
  result agree. No arithmetic change was required.
* Chara Karaka ordering revalidated as intra-sign (`sidereal % 30`) ranking;
  7-Karaka excludes Rahu; 8-Karaka DIRECT/INVERSE conventions verified
  (golden Rahu 22.3264° direct / 7.6736° inverse).
* Rashi Drishti revalidated: 12/12 signs aspect exactly 3, 100% mutual symmetry
  over 144 pairs, planetary propagation derived only from occupied signs; the
  module imports no Parashari aspect code (sole "Graha" mention is a docstring
  contrast note).
* Golden snapshot `backend/golden_jaimini_snapshot.json` regenerated by the
  corrected engine: AL = Capricorn, UL = Capricorn (engine-derived; equals A12),
  Karakamsha = Cancer.
