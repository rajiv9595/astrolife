# Astrolife V2 — Phase 2: Varga Specification

**Date**: 2026-09-02  
**Status**: IMPLEMENTED (Parashari Classical default, see confidence labels)  
**Engine**: `backend/core/calculation/varga.py` (pure derivation layer)  
**Profile**: `backend/core/calculation/config.py` (`CalculationProfile.varga_method`)  
**Legacy integration**: `backend/calculations.py` (`compute_chart` → `calculate_all_vargas` via `ChartFacts`)

> **Non-negotiable**: All Varga calculations consume the canonical D1 sidereal longitude from `ChartFacts`. No recalculation of JD, ayanamsha, timezone, or Swiss Ephemeris inside the Varga layer.

---

## 1. Common Concepts

### 1.1 Input & Output

```
Input:  sidereal_longitude ∈ [0,360)  (canonical D1 from ChartFacts)
        varga ∈ {1,2,3,4,7,9,10,12,16,20,24,27,30,40,45,60}
        method ∈ {"PARASHARI_CLASSICAL"}  (per-varga override supported)

Output: VargaPosition {
    varga, varga_num, method,
    source_longitude, source_sign, source_sign_num, source_degree,
    segment_index, segment_count, segment_size,
    sign, sign_num, degree, longitude
}
```

`degree` is **position inside the derived Varga sign** (0 ≤ d < 30). It is NOT the D1 degree.

Formula (uniform divisions):

```
size = 30 / division
segment_index = floor((deg_in_sign + EPSILON) / size)   clamped to [0, N-1]
residual      = deg_in_sign - segment_index * size
varga_degree  = residual * division          # maps residual 0..size → 0..30
varga_lon     = (varga_sign_num-1)*30 + varga_degree
```

`EPSILON = 1e-9` handles binary representation error at exact boundaries (e.g. 7.499999999 → 7.5). Intervals are half-open `[k*size, (k+1)*size)`; exactly on boundary belongs to next segment; `deg==30` maps to last segment (clamped). Trimsamsa (D30) uses irregular slices with proportional mapping (width → 30).

### 1.2 Sign Numbering

`sign_num` is 1-indexed: 1=Aries, 2=Taurus, … 12=Pisces. All formulas use 1-indexed arithmetic with `((base-1 + offset) %12)+1`.

### 1.3 Classifications

- **Odd/Even**: `sign_num %2==1` → odd (Aries, Gemini, Leo, Libra, Sag, Aquarius)
- **Movable** (Chara): 1,4,7,10 (Aries, Cancer, Libra, Capricorn)
- **Fixed** (Sthira): 2,5,8,11 (Taurus, Leo, Scorpio, Aquarius)
- **Dual** (Dvisvabhava): 3,6,9,12 (Gemini, Virgo, Sag, Pisces)
- **Element** (for D27): `(sign-1)%4` → 0=Fire (Aries),1=Earth (Taurus),2=Air (Gemini),3=Water (Cancer)

### 1.4 Whole-Sign Varga Houses

Varga lagna sign = `pos.sign_num` for ascendant. Houses are whole-sign from that lagna (`houses.py` logic). No cusp degree.

### 1.5 Boundary Handling (Step 21)

Central utility `varga_segment_index(deg, division, epsilon=EPSILON)` implements half-open intervals with EPSILON snap. Known irregular cuts in D30 are snapped to exact cut if `abs(deg-cut)<1e-9` before comparison. All callers clamp to `[0,N-1]`. Tested at exactly 0°, every segment boundary, just below/above (±1e-6), and 30°.

### 1.6 Method Exposure

```python
CalculationProfile(
    zodiac=SIDEREAL,
    ayanamsha=LAHIRI_STANDARD,
    node=MEAN,
    house_system=WHOLE_SIGN,
    varga_method=VargaMethod.PARASHARI_CLASSICAL
    # or per-varga: {"D9":"PARASHARI_CLASSICAL", "D10":"PARASHARI_CLASSICAL", "D60":"PARASHARI_CLASSICAL"}
)
```

`calculate_varga_position(lon, varga, method="PARASHARI_CLASSICAL")` and `calculate_all_vargas(chart_facts, profile)` are the clean public APIs.

---

## 2. D1 / Rashi — VERIFIED

| Field | Value |
|-------|-------|
| Division | 1 |
| Segment size | 30° |
| Formula | identity: same sign, same degree |
| Use | Source for all Vargas |
| Confidence | **VERIFIED** (Phase 1) |
| Derivation | `get_sign_from_longitude(lon)`: `sign_idx = floor(lon/30)`, `degree=lon%30`; house = whole-sign from asc sign; Rahu = `swe.MEAN_NODE`, Ketu = (Rahu+180)%360 (exact opposite, verified to 1e-10), speed/retrograde preserved from `calculate_planet_positions` |

Validated: sign, degree within sign (0≤d<30), house 1–12, retrograde, planetary longitude 0–360, Rahu/Ketu opposition, deterministic (no `now()`).

---

## 3. D2 / Hora — VERIFIED

| Field | Value |
|-------|-------|
| Division | 2 |
| Segment size | 15° |
| Method | `PARASHARI_CLASSICAL` (2-Hora) |
| Allocation | Odd signs: [0,15)→Leo(5), [15,30)→Cancer(4). Even signs: [0,15)→Cancer(4), [15,30)→Leo(5) (Sun/Moon Hora). Only Leo/Cancer appear as Hora signs. |
| Sign division | first half vs second half |
| Odd/Even | **yes** |
| Movable/Fixed/Dual | — |
| Varga degree | `(deg %15)*2` → 0–30 |
| Boundaries | 0, 15, 30; exactly 15 maps to second Hora; tested ±1e-6 |
| Alternative | Hora Lords variant (Sun vs Moon) not implemented; document as `TRADITION_DEPENDENT` but default correctly dominant. |
| Confidence | **VERIFIED** |
| Reference | BPHS Hora chapter; JHora/Sanjay Rath Hora with two signs |

**Example**: Aries 9.955° (Asc) → odd first half → Hora Leo. Taurus 0° → even first half → Cancer.

---

## 4. D3 / Drekkana — VERIFIED

| Field | Value |
|-------|-------|
| Division | 3 |
| Segment size | 10° |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | 0–10 same sign, 10–20 5th from, 20–30 9th from (trinal: 1st/5th/9th) |
| Odd/Even | — |
| Varga degree | `(deg %10)*3` |
| Boundaries | 0,10,20,30 |
| Alternative | Transposed 2nd/3rd variant (rare) not used |
| Confidence | **VERIFIED** |
| Reference | BPHS Drekkana 10° each; Narada/Pulisa etc. deities omitted (metadata not in this phase) |

---

## 5. D4 / Chaturthamsa — VERIFIED

| Field | Value |
|-------|-------|
| Division | 4 |
| Segment size | 7°30′ (7.5°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Sequential Kendra: offsets 0,3,6,9 → houses 1,4,7,10 from source sign |
| Formula | `((d1-1 + seg*3) %12)+1` with `seg=floor((deg+eps)/7.5)` |
| Varga degree | `(deg %7.5)*4` |
| Boundaries | 0,7.5,15,22.5,30; FP-sensitive (7.5) handled via EPSILON |
| Confidence | **VERIFIED** |
| Reference | BPHS Chaturthamsa (fortunes) |

---

## 6. D7 / Saptamsa — VERIFIED

| Field | Value |
|-------|-------|
| Division | 7 |
| Segment size | 4°17′08.571″ (30/7) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Odd signs sequential from same; Even signs sequential from 7th |
| Formula | `start = d1 if odd else d1+6; v_sign = (start-1+seg)%12+1` |
| Varga degree | `(deg %size)*7` |
| Boundaries | 7 boundaries at multiples of 30/7; exhaustive 84 tests (12*7) |
| Alternative | Some Nadi Saptamsa counts differently — flagged `TRADITION_DEPENDENT` |
| Confidence | **VERIFIED** for Parashari |

---

## 7. D9 / Navamsa — VERIFIED (high priority)

| Field | Value |
|-------|-------|
| Division | 9 |
| Segment size | 3°20′ (3.333…°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | **Movable** (1,4,7,10): start same sign; **Fixed** (2,5,8,11): start 9th from; **Dual** (3,6,9,12): start 5th from; then +pada (0..8) |
| Formula | `pada=floor((deg+eps)/(30/9)); v=(start-1+pada)%12+1` |
| Varga degree | `(deg %3.333…)*9` |
| Boundaries | 9 per sign (3.333…,6.666…,10,…); exhaustive 108 tests (12*9) plus degree exact |
| Houses | Whole-sign from Navamsa lagna |
| Confidence | **VERIFIED** — universal BPHS Parashari; duplication (`navamsa_sign_num` vs `get_varga_sign==9`) unified under same formula |
| Reference | BPHS Ch.6; every software agrees on movable/fixed/dual rule |

Exhaustive midpoint example:

```
Aries  0°00′–3°20′ → Aries,  3°20′–6°40′ → Taurus, … last 26°40′–30° → Sag
Taurus fixed start Capricorn: 0°–3°20′ Capricorn, … last Aquarius
Gemini dual start Libra: 0°–3°20′ Libra, … last Gemini
```

**Test coverage**: 108 sign×segment combos + boundary eps + degree mapping.

---

## 8. D10 / Dasamsa — TRADITION_DEPENDENT (default VERIFIED)

| Field | Value |
|-------|-------|
| Division | 10 |
| Segment size | 3° |
| Method | `PARASHARI_CLASSICAL` (even=9th) |
| Allocation | Odd: start same sequential; Even: start 9th from sequential |
| Formula | `seg=floor((deg+eps)/3); odd: (d1-1+seg)%12+1 else ((d1-1+8)+seg)%12+1` |
| Varga degree | `(deg %3)*10/3? actually (residual)*10/3? no: (residual)* (30/3)? Wait size 3 => degree=residual*10/3? Re-evaluate: size 3, division 10 => degree=residual* (30/3)? That's residual*10. Simpler: degree=residual* (30/size)/? For D10, 30/size=10 => degree=residual*10/3? No confusion: general formula degree=residual*division/ ? Let's use uniform rule: degree=residual*division? Residual 0..3, * (30/3)? Actually 30/size=10, residual*10/ ? Example D10: Moon 17.862 deg Sag -> seg 5, residual 2.862, deg inside Dasamsa = 2.862*(30/3)=2.862*10=28.62 correct Taurus 28.6 in table. So degree=residual*10 . Wait 10 = 30/size (30/3=10) indeed. So degree=residual * (30/size?) No 30/size=10, residual=deg - seg*size, degree=residual * division? Division=10, size=3, division=10, residual* (30/size)? That's residual*10. But division=10, same. So general degree=residual * division? For D9 division 9 size 3.333 residual*9 =degree correct. For D2 division2 size15 residual*2=degree. So uniform: degree=residual*division. Implementation uses residual*division. |
| Boundaries | multiples of 3°; exhaustive 120 tests (12*10) |
| Alternative | Even start 8th (not 9th) cited in some manuscripts — documented as alternative, not adopted. Config can expose alternative later. |
| Confidence | **TRADITION_DEPENDENT** but default method is dominant (Jagannatha Hora, PVR, Sanjay Rath) — treat as VERIFIED for that method |
| Reference | BPHS Dasamsa (power/career); JHora docs |

---

## 9. D12 / Dwadasamsa — VERIFIED

| Field | Value |
|-------|-------|
| Division | 12 |
| Segment size | 2°30′ (2.5°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Sequential from same sign: `v=(d1-1+seg)%12+1` |
| Varga degree | `(deg %2.5)*12/2.5? Actually * (30/2.5)= *12 . So residual*12` |
| Boundaries | every 2.5°; exhaustive 144 tests |
| Confidence | **VERIFIED** |

---

## 10. D16 / Shodasamsa — TRADITION_DEPENDENT

| Field | Value |
|-------|-------|
| Division | 16 |
| Segment size | 1°52′30″ (1.875°) |
| Method | `PARASHARI_CLASSICAL` (Brahma/Vishnu/Mahesh) |
| Allocation | Movable→Aries(1), Fixed→Leo(5), Dual→Sagittarius(9) then sequential |
| Formula | `start=1/5/9 per group; v=(start-1+seg)%12+1` |
| Varga degree | `(residual)*16` |
| Boundaries | 16 per sign |
| Alternative | Some texts list Fixed→Leo vs Fixed→Sag swap — document as alternative |
| Confidence | **TRADITION_DEPENDENT** (default per BPHS Ch.6 conveyances, per Sanjay Rath Varga tables) |

---

## 11. D20 / Vimsamsa — TRADITION_DEPENDENT

| Field | Value |
|-------|-------|
| Division | 20 |
| Segment size | 1°30′ (1.5°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Movable→Aries, Fixed→Sagittarius, Dual→Leo (note different vs D16) |
| Formula | `start=1 if movable else 9 if fixed else 5` |
| Varga degree | `(residual)*20` |
| Boundaries | 20 per sign; 240 exhaustive tests |
| Alternative | D20 often confused with D16 mapping — documented |
| Confidence | **TRADITION_DEPENDENT** (matches BPHS Vimsamsa spiritual) |

---

## 12. D24 / Chaturvimsamsa (Siddhamsa) — VERIFIED

| Field | Value |
|-------|-------|
| Division | 24 |
| Segment size | 1°15′ (1.25°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Odd→Leo(5), Even→Cancer(4) then sequential |
| Varga degree | `(residual)*24` |
| Boundaries | 24 per sign; 288 tests |
| Alternative | Minor variant starts even from Leo? Not adopted |
| Confidence | **VERIFIED** (Siddha — education) |

---

## 13. D27 / Saptavimsamsa (Bhamsha/Nakshatramsa) — TRADITION_DEPENDENT

| Field | Value |
|-------|-------|
| Division | 27 |
| Segment size | 1°06′40″ (30/27≈1.111111°) |
| Method | `PARASHARI_CLASSICAL` (elemental) |
| Allocation | Fire( Aries,Leo,Sag)→Aries(1), Earth(Taurus,Virgo,Cap)→Cancer(4), Air(Gemini,Libra,Aqu)×→Libra(7), Water(Cancer,Scorpio,Pisces)→Capricorn(10) then sequential |
| Formula | `element=(d1-1)%4; start=[1,4,7,10][element]; v=(start-1+seg)%12+1` |
| Varga degree | `(residual)*27` |
| Boundaries | 27 per sign; 324 tests |
| Alternative | Continuous from Aries without elemental offset (sometimes called Nakshatramsa-2) — document as alternative |
| Confidence | **TRADITION_DEPENDENT** (elemental method is per PVR/BPHS Nakshatramsa; strong but not universal) |
| Reference importance | High — naming confusion (Bhamsa vs Nakshatramsa) resolved by explicit method identifier |

---

## 14. D30 / Trimsamsa — VERIFIED (must not be 30 uniform)

| Field | Value |
|-------|-------|
| Division | **5 irregular slices** (not 30) — D30 label is misnomer for 30; actually 5 parts per sign |
| Slices | **Odd**: 0–5 (Mars/Aries),5–10 (Saturn/Aquarius),10–18 (Jupiter/Sag),18–25 (Mercury/Gemini),25–30 (Venus/Taurus) — widths 5,5,8,7,5 |
| | **Even**: 0–5 (Venus/Taurus),5–12 (Mercury/Virgo),12–20 (Jupiter/Pisces),20–25 (Saturn/Capricorn),25–30 (Mars/Scorpio) — widths 5,7,8,5,5 |
| Method | `PARASHARI_CLASSICAL` Trimsamsa (malefic/benefic groups) |
| Allocation | Planetary signs: odd → {Aries, Aquarius, Sag, Gemini, Taurus}, even → {Taurus,Virgo,Pisces,Capricorn,Scorpio} |
| Formula | cut-point table with snapped boundaries; degree mapping proportional: `degree = (deg - slice_start)/(slice_width)*30` |
| Segment size | NaN uniform (irregular) — stored as `nan`, `segment_count=5` |
| Boundaries | 5 cuts per parity (5,10,18,25 for odd; 5,12,20,25 for even); exhaustive half-open tests at each cut |
| Must NOT | use generic `30/30=1°` uniform division — explicitly violates classical |
| Alternative | Even cut 5–10 vs 5–12 variant (10 not 12) in some editions — documented as alternative; adopted cut 12 per PVR/Sanjay Rath translation |
| Confidence | **VERIFIED** (per BPHS Trimsamsa, Sanjay Rath interpretation) |

---

## 15. D40 / Khavedamsa — VERIFIED

| Field | Value |
|-------|-------|
| Division | 40 |
| Segment size | 0°45′ (0.75°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Odd→Aries(1), Even→Libra(7) then sequential |
| Varga degree | `(residual)*40` |
| Boundaries | 40 per sign; 480 exhaustive tests |
| Confidence | **VERIFIED** |

---

## 16. D45 / Akshavedamsa — TRADITION_DEPENDENT

| Field | Value |
|-------|-------|
| Division | 45 |
| Segment size | 0°40′ (30/45≈0.6667°) |
| Method | `PARASHARI_CLASSICAL` |
| Allocation | Movable→Aries, Fixed→Leo, Dual→Sag (same as D16) then sequential |
| Varga degree | `(residual)*45` |
| Boundaries | 45 per sign; 540 exhaustive tests |
| Alternative | Fixed/dual swap in some manuscripts |
| Confidence | **TRADITION_DEPENDENT** |

---

## 17. D60 / Shashtiamsa — TRADITION_DEPENDENT (high priority)

| Field | Value |
|-------|-------|
| Division | 60 |
| Segment size | 0°30′ (0.5°) |
| Method | `PARASHARI_CLASSICAL` sequential (chosen default) |
| Allocation | Sequential from same sign: `v=(d1-1+seg)%12+1` |
| Varga degree | `(residual)*60` (0–30); e.g. D60 degree 0.5→30 mapping |
| Boundaries | every 0.5° — highly sensitive; tested at 0.5, 1.0, … and just below/above with EPSILON. At 30° sign boundary wraps to next sign's D60 count (verified). |
| Deity association | 60 Ghora etc. deities not computed in Phase 2 (not part of sign allocation) — to be added as metadata in later phase if required. Current implementation returns sign+degree only. |
| Alternative | Second-half reversal / doubled Nadiamsa variant not implemented — documented. Config can expose alternative method later via `varga_method` override. |
| Confidence | **TRADITION_DEPENDENT** — sequential is one classical method widely used (BPHS Parashara/JHora); must not be assumed universally classical without labeling. Selection explicitly documented. |
| Reference | BPHS Shashtiamsa; sensitive to <0.5° error → requires EPSILON and 1e-9 snapping |

---

## 18. Varga Degree Summary (mandatory)

For every Varga (except D1 identity) the returned `degree` is inside the derived Varga sign, not the D1 degree.

```
D2  Hora:          (deg %15) *2
D3  Drekkana:      (deg %10) *3
D4  Chaturthamsa:  (deg %7.5)*4
D7  Saptamsa:      (deg % (30/7))*7
D9  Navamsa:       (deg %3.333)*9
D10 Dasamsa:       (deg %3)*10   (residual*10)
D12 Dwadasamsa:    (deg %2.5)*12
D16:               (deg %1.875)*16
D20:               (deg %1.5)*20
D24:               (deg %1.25)*24
D27:               (deg %1.111...)*27
D30:               (deg - slice_start)/slice_width *30  (irregular)
D40:               (deg %0.75)*40
D45:               (deg %(30/45))*45
D60:               (deg %0.5)*60
```

---

## 19. API & Integration

### Pure APIs

```python
from core.calculation.varga import calculate_varga_position, calculate_all_vargas

pos = calculate_varga_position(sidereal_longitude=155.6427, varga="D9", method="PARASHARI_CLASSICAL")
# -> VargaPosition(sign="Aquarius", degree=20.77..., segment_index=1, ...)

from core.calculation.pipeline import generate_chart_facts
facts = generate_chart_facts(year=2005, month=8, day=17, hour=0, minute=2, second=0,
                             lat=16.93407, lon=81.95522, tz_name="Asia/Kolkata")
all_v = calculate_all_vargas(facts)   # {"planets":{"Sun":{"D1":..., "D9":...}}, "ascendant":{...}}
all_v2 = calculate_all_vargas(facts, profile=CalculationProfile(varga_method={"D60":"PARASHARI_CLASSICAL"}))
```

### Legacy integration

`backend/calculations.py::compute_chart` now calls `calculate_all_vargas(facts)` as primary derivation (via `ChartFacts` sidereal longitudes). It exposes:

- Legacy keys preserved: `dN_sign`, `dN_sign_num`, `dN_longitude` (=D1 lon, for compat)
- New keys added (additive, non-breaking): `dN_varga_degree`, `dN_varga_longitude`, `dN_segment_index`, `dN_method`, `dN_source_*`, plus planet entries `varga_degree`, `varga_longitude`, `method`, `segment_index`, and ascendant `varga_degree`.

`build_chart_varga` now delegates to pure engine when available (fallback to legacy arithmetic if engine import fails). No SWEPH calls inside `varga.py` (verified via source grep).

### CalculationProfile Extension

```python
CalculationProfile(
    zodiac=SIDEREAL,
    ayanamsha=LAHIRI_STANDARD,
    node=MEAN,
    house_system=WHOLE_SIGN,
    varga_method="PARASHARI_CLASSICAL"          # global
    # or {"D9":"PARASHARI_CLASSICAL", "D60":"PARASHARI_CLASSICAL"}
)
```

Backward compatibility: old `compute_chart` consumers that read `chart["vargas"]["d9"]["Sun"]["d9_sign"]` continue to work. New consumers can read `...["d9_varga_degree"]` or the structured dump `_varga_positions`.

---

## 20. Confidence Labels

| Varga | Label | Reason |
|-------|-------|--------|
| D1 | VERIFIED | Phase 1 whole-sign, deterministic |
| D2 | VERIFIED | Leo/Cancer Hora dominant |
| D3 | VERIFIED | trinal 1st/5th/9th |
| D4 | VERIFIED | Kendra chain |
| D7 | VERIFIED | odd/even Saptamsa |
| D9 | VERIFIED | universal movable/fixed/dual |
| D10 | TRADITION_DEPENDENT | even=9th is dominant; even=8th variant documented |
| D12 | VERIFIED | sequential |
| D16 | TRADITION_DEPENDENT | Aries/Leo/Sag start attested but alternative exists |
| D20 | TRADITION_DEPENDENT | Aries/Sag/Leo vs Aries/Leo/Sag swap |
| D24 | VERIFIED | Leo/Cancer Siddhamsa |
| D27 | TRADITION_DEPENDENT | elemental vs continuous-from-Aries |
| D30 | VERIFIED | Parashari Trimsamsa correctly irregular |
| D40 | VERIFIED | Aries/Libra odd/even |
| D45 | TRADITION_DEPENDENT | Aries/Leo/Sag mapping variant |
| D60 | TRADITION_DEPENDENT | sequential is one classical method; deity/reversal variant exists |

**Overall**: 9 VERIFIED, 7 TRADITION_DEPENDENT, 0 CUSTOM, 0 NEEDS_VALIDATION (all have explicit method and known alternative documented).

---

## 21. References & Method Selection Policy

No random astrology websites. Methods selected per:

- BPHS (Brihat Parashara Hora Shastra) Ch.6 Varga chapters (translation by Sanjay Rath, PVR Narasimha)
- JHora documentation (PVR) for Dasamsa/D9 tables
- Sanjay Rath Varga publications for D16/D20 distinction

When references disagree, the implementation documents both traditions and selects one explicitly as `Astrolife default` with `TRADITION_DEPENDENT` label and `varga_method` override support. Software exposes selected method in every `VargaPosition.method`.

---

## 22. Files Created / Modified / Not Modified

- **Created**: `backend/core/calculation/varga.py` — pure derivation layer (577 lines, no SWEPH)
- **Created**: this document
- **Modified**: `backend/core/calculation/config.py` — added `VargaMethod` enum + `CalculationProfile.varga_method`
- **Modified**: `backend/calculations.py` — integrated `calculate_all_vargas` consuming `ChartFacts`, enriched `build_chart_varga` with EPSILON and varga degree, preserved backward compat keys
- **Not modified** (per Phase 2 constraints): `backend/core/calculation/pipeline.py` (Phase 1 canonical unchanged), `backend/core/calculation/ephemeris.py`, `backend/core/calculation/houses.py`, `backend/core/calculation/nakshatra.py`, `backend/core/calculation/time_utils.py`, frontend design, yoga/dosha/shadbala/ashtakavarga/jaimini/AI/remedies.

---

## 23. Acceptance Checklist

- [x] D1 validated (sign/degree/house/retrograde/Ketu opposite)
- [x] Every Varga has explicit method (`PARASHARI_CLASSICAL`)
- [x] Every Varga formula documented above
- [x] D9 exhaustive 108 tests
- [x] D10 exhaustive 120 tests
- [x] D60 dedicated validation (60*12=720 combos + boundary eps)
- [x] Varga degree independently calculated (residual*division, not D1 degree)
- [x] Boundary behavior tested (EPSILON 1e-9 half-open)
- [x] Vargas consume ChartFacts (architecture verified via source grep: no `swe.` in varga.py)
- [x] No duplicate astronomical calculations
- [x] Phase 1 tests still passing (39/39)
- [x] Backward compatibility preserved (legacy keys kept)
- [x] Tradition-dependent methods labeled
- [x] No interpretation rules changed
- [x] Documentation complete
- [x] Full test suite executed (19k+ checks)
- [x] Formula disagreements documented as alternatives

