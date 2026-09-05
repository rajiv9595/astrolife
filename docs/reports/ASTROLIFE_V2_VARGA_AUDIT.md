# Astrolife V2 — Phase 2: Varga Audit

**Date**: 2026-09-02
**Scope**: D1–D60, file `backend/calculations.py`
**Canonical source**: `ChartFacts` (not yet consumed by Varga layer — finding)

---

## 1. Files & Functions Audited

| File | Functions |
|------|-----------|
| `backend/calculations.py:845-847` | `deg_in_sign(lon)` |
| `backend/calculations.py:850-863` | `navamsa_sign_num(d1_sign, deg)` |
| `backend/calculations.py:948-972` | `dashamsha_sign_num(d1_sign, deg)` |
| `backend/calculations.py:1044-1145` | `get_varga_sign(varga_num, d1_sign, deg)` — monolith dispatch |
| `backend/calculations.py:1148-1212` | `build_chart_varga(varga_num, asc_sidereal_deg, d1_planets)` |
| `backend/calculations.py:880-943` | `build_chart_d9(...)` (legacy wrapper, delegates to navamsa) |
| `backend/calculations.py:975-1037` | `build_chart_d10(...)` (legacy wrapper) |
| `backend/calculations.py:866-878` | `whole_sign_houses_from(lagna_sign)` |
| `backend/calculations.py:1604-1724` | `compute_chart(...)` — calls `build_chart_varga` loop for 16 vargas |

No file under `backend/core/calculation/` implements Vargas before this audit.

---

## 2. Current Formula Table

`d1_sign` is 1-indexed (1=Aries…12=Pisces). `deg` is degree within sign [0,30).

| Varga | Division | Segment size | Formula (as coded) | Starting-sign rule | Odd/even | Movable/fixed/dual | Output representation | Method label (coded) |
|-------|----------|-------------|--------------------|--------------------|----------|--------------------|-----------------------|----------------------|
| D1 | 1 | 30° | `return d1_sign` | same | — | — | `{d1_sign, longitude=D1 lon}` | implicit |
| D2 Hora | 2 | 15° | `deg<15 ? (odd?5:4) : (odd?4:5)` | Leo(5)/Cancer(4) | **yes** | — | sign only, lon=D1 lon | Parashari 2-Hora |
| D3 Drekkana | 3 | 10° | `part=deg//10; 0→same,1→+4,2→+8` | 1st,5th,9th trine | — | — | sign only | Parashara |
| D4 Chaturthamsa | 4 | 7°30' (7.5°) | `((d1_sign+part*3-1)%12)+1` with `part=deg//7.5` | Kendra chain (1,4,7,10) | — | — | sign only | Parashara |
| D7 Saptamsa | 7 | 4°17'08.571" (30/7) | `part=deg/(30/7); start= d1_sign if odd else d1_sign+6` sequential | same / 7th | **yes** | — | sign only | Parashara |
| D9 Navamsa | 9 | 3°20' (30/9) | `pada=deg*9//30; start= movable→same, fixed→9th, dual→5th` | computed per group | — | **yes** (1,4,7,10 / 2,5,8,11 / 3,6,9,12) | via `navamsa_sign_num` | Parashari classical |
| D10 Dasamsa | 10 | 3° | `dashamsha=deg/3; odd→same sequential, even→9th sequential` | same / 9th | **yes** | — | via `dashamsha_sign_num` | Parashari (9th for even) |
| D12 Dwadasamsa | 12 | 2°30' (2.5°) | `part=deg//2.5; ((d1-1+part)%12)+1` sequential from same | same | — | — | sign only | Parashara |
| D16 Shodasamsa | 16 | 1°52'30" (1.875°) | `part=deg/1.875; start= 1(Ari) if movable else 5(Leo) if fixed else 9(Sag)` sequential | — | **yes** | sign only | Parashara (Brahma/Vishnu/Shiva variant) |
| D20 Vimsamsa | 20 | 1°30' (1.5°) | `part=deg/1.5; start=1 if movable else 9 if fixed else 5` sequential | — | **yes** | sign only | Parashara |
| D24 Siddhamsa | 24 | 1°15' (1.25°) | `part=deg/1.25; start=5(Leo) if odd else 4(Cancer)` sequential | same-type odd/even proxy | **yes (odd/even)** | — | sign only | Parashara (education) |
| D27 Bhamsha/Nakshatramsa | 27 | 1°06'40" (30/27) | `part=deg/(30/27); element=(d1-1)%4; start=[1,4,7,10][element]` | Fire→Ari,Earth→Can,Air→Lib,Water→Cap | via element | — | sign only | Parashara (elemental) |
| D30 Trimsamsa | 30 (irregular) | 5,5,8,7,5 odd / 5,7,8,5,5 even | `if odd: <5→Ari, <10→Aqua, <18→Sag, <25→Gem else Taur; even: <5→Taur, <12→Vir, <20→Pis, <25→Cap else Scor` | planetary lords, not sequential | **yes** | — | sign only (house lord maps) | Parashari Trimsamsa (MUST NOT be 1° uniform) |
| D40 Khavedamsa | 40 | 0°45' (0.75°) | `part=deg/0.75; start=1 if odd else 7(Libra)` sequential | same / 7th | **yes** | — | sign only | Parashara |
| D45 Akshavedamsa | 45 | 0°40' (30/45) | `part=deg/(30/45); start=1 if movable else 5 if fixed else 9` sequential | — | **yes** | sign only | Parashara |
| D60 Shashtiamsa | 60 | 0°30' (0.5°) | `part=deg/0.5; ((d1-1+part)%12)+1` sequential from same | same | — | — | sign only | Generic sequential (disputed) |

### Notes on code quality of existing layer

* **Integer division via `int(deg // size)` / `int(deg / size)`** — no epsilon, vulnerable to FP boundary misclassification (e.g. 7.5 represented as 7.4999999).
* **No `segment_index` returned** — caller cannot tell which amsa was used.
* **No Varga degree** — `longitude` field is copied from D1 (`p["longitude"]=lon`). Step 20 violation: D1 degree reused as Varga degree / longitude. `ascendant["degree"]` likewise copies `asc_sidereal_deg` rather than recomputing.
* **Not pure derivation from ChartFacts** — `build_chart_varga` takes `(asc_sidereal_deg, d1_planets_list)` built from legacy `res_planets`, not from `ChartFacts`. It also reads `_active_tz` global indirectly via caller.
* **No method identifier** in output.
* **Duplicated Navamsa** — `build_chart_d9` and `get_varga_sign==9` duplicate same logic via `navamsa_sign_num`.
* **D16/D20/D45 index constants**: movable/fixed/dual sets hard-coded but correct per BPHS Parashara edition (see below).
* **D27** only implements one of at least two published Bhamsa traditions (the elemental/fire-earth-air-water). The alternative counts continuously from Aries without elemental offset — not present.
* **D60** implements the simplest sequential model. Classical references list at least two D60 theories (Parashara sequential vs. “double-clock” where second half reverses). Current code picks one without labeling.

---

## 3. Per-Varga Deep Dive

### D1 (Rashi)
* **Verified**: derives sign via `lon //30`, degree via `%30`, house via Whole Sign. Ketu = (Rahu+180)%360.
* **Defect**: none in Phase 1 canonical. Legacy `calculate_houses` also builds Placidus cusps internally then discards them — wasteful but not wrong.
* **Action**: keep Phase 1 canonical as source; Varga engine must not recalc.

### D2 Hora
* **Segment**: 15°. Boundaries at 0,15,30.
* **Allocation coded**: `odd: [0,15)→Leo, [15,30)→Cancer`; `even: [0,15)→Cancer, [15,30)→Leo`. This is the **Parashari Sun/Moon Hora** with only Leo/Cancer as Hora signs. Variant exists where Hora is lorded by Sun/Moon but some schools use alternative Hora lords — not implemented. Mark `TRADITION_DEPENDENT` but default correctly set to Leo/Cancer.
* **Audit verdict**: VERIFIED for chosen tradition. Boundary at exactly 15° assigns second Hora (code uses `<15` so 15.0 belongs to second half — correct per half-open interval [0,15),[15,30)).
* **Missing**: boundary tests, varga degree (Hora degree = `(deg%15)*2` to map 15°→30°).

### D3 Drekkana
* **Segment**: 10°. Parts exactly 0–10,10–20,20–30.
* **Coded**: 1st same, 2nd 5th house, 3rd 9th. Classical Parashara D3.
* **Alternative**: some texts swap 2nd/3rd for second half — not used. Current is dominant.
* **Verdict**: VERIFIED.
* **Missing**: varga degree = `(deg%10)*3`, boundary epsilon.

### D4 Chaturthamsa
* **Segment**: 7.5°. Parts 0,1,2,3 → houses 1,4,7,10 (Kendra). Code uses `part*3`. Correct.
* **Defect**: uses floating `7.5` with `//` — FP risk at 7.5,15.0,22.5.
* **Verdict**: VERIFIED formula, NEEDS epsilon wrapper.

### D7 Saptamsa
* **Segment**: 30/7 ≈4.2857142857. Code uses `deg/(30/7)`.
* **Coded**: odd start same, even start 7th. Matches BPHS Saptamsa for children.
* **Alternative**: Nadi variant counts differently — document as `TRADITION_DEPENDENT`.
* **Verdict**: VERIFIED for Parashari.

### D9 Navamsa
* **Segment**: 3.333...°. `pada = floor(deg *9/30)`.
* **Allocation**: movable→same, fixed→9th, dual→5th then +pada. This is the **BPHS Parashari classical** and universally used. Code matches exactly.
* **Boundary**: requires 9 tests per sign (108 total minimum).
* **Verdict**: VERIFIED. Duplicated function should be unified.

### D10 Dasamsa
* **Segment**: 3°.
* **Coded**: odd same sequential, even 9th sequential. This matches **Parashara Dasamsa** as used in Jagannatha Hora / Sanjay Rath. Alternative Dasamsa (even start from 9th vs even start from 8th) exists but not adopted here. Variant should be documented.
* **Verdict**: VERIFIED for declared method. Mark `TRADITION_DEPENDENT` (one common alternative starts even from 8th not 9th).

### D12 Dwadasamsa
* **Segment**: 2.5°. Sequential from same. Matches classical.
* **Verdict**: VERIFIED.

### D16 Shodasamsa
* **Segment**: 1.875°.
* **Coded**: movable→Aries(1), fixed→Leo(5), dual→Sagittarius(9). Checking BPHS Ch.6: Shodasamsa (conveyances) — “Aries for movable, Leo for fixed, Sag for dual” — **matches credited Parashara**.
* **Cross-check**: Some secondary sources list movable→Aries, fixed→Leo, dual→Sag (same). Others rotate. Code aligns with dominant.
* **Verdict**: VERIFIED as `PARASHARI_CLASSICAL`; flag `TRADITION_DEPENDENT` with note.

### D20 Vimsamsa
* **Segment**: 1.5°.
* **Coded**: movable→Aries, fixed→Sagittarius, dual→Leo (note different vs D16). BPHS Vimsamsa (spiritual): movable→Aries, fixed→Sag, mutable→Leo — matches coded. Good.
* **Verdict**: VERIFIED.

### D24 Chaturvimsamsa (Siddhamsa)
* **Segment**: 1.25°.
* **Coded**: odd→Leo, even→Cancer. Matches Siddhamsa tradition (knowledge). Correct.
* **Verdict**: VERIFIED.

### D27 Saptavimsamsa / Bhamsa / Nakshatramsa
* **Segment**: 30/27≈1.111111°.
* **Coded**: elemental: (sign-1)%4 → [Aries,Cancer,Libra,Capricorn]. This is the **Nakshatramsa** method where fire signs start Aries etc. Alternative published method starts every sign from Aries or sequentially from same — not used.
* **Verdict**: TRADITION_DEPENDENT. Default elemental method is defensible; alternative must be documented.

### D30 Trimsamsa
* **Segment**: **Irregular** — not 1°. Code correctly implements 5 unequal parts per BPHS with different cut points for odd/even and planetary sign mapping. NOT a 30-part division. Crucial that generic `deg//1` was not used.
* **Odd cuts**: 0-5 Mars/Aries, 5-10 Saturn/Aqua, 10-18 Jupiter/Sag, 18-25 Mercury/Gem, 25-30 Venus/Taurus.
* **Even cuts**: 0-5 Venus/Taurus, 5-12 Mercury/Virgo, 12-20 Jupiter/Pisces, 20-25 Saturn/Cap, 25-30 Mars/Scorpio.
* **Cut points offset differs by 2° between traditions?** Some texts use even 0-5,5-10,10-18 vs 0-5,5-12 etc. Coded version with 12 not 10 is one accepted sloka reading. Must be documented as `PARASHARI_CLASSICAL` with alternative noted.
* **Verdict**: VERIFIED (matches BPHS as interpreted by Sanjay Rath / PVR). Do NOT replace with 1° uniform.

### D40 Khavedamsa
* **Segment**: 0.75°.
* **Coded**: odd→Aries, even→Libra (7th). Matches BPHS Khavedamsa (auspicious/inauspicious). Correct.
* **Verdict**: VERIFIED.

### D45 Akshavedamsa
* **Segment**: 0.666...° (30/45).
* **Coded**: movable→Aries, fixed→Leo, dual→Sag (same as D16). BPHS Akshavedamsa traditionally movable→Aries, fixed→Leo, mutable→Sag — matches. Some manuscripts swap fixed/dual; document.
* **Verdict**: VERIFIED with `TRADITION_DEPENDENT` note.

### D60 Shashtiamsa
* **Segment**: 0.5°.
* **Coded**: sequential from same sign ((d1-1+part)%12)+1. This is **one** of the published D60 mappings — the simplest “Parashara Shashtiamsa” sequential. Alternative D60 (sometimes called “Shashtiamsa 2” or Nadiamsa doubling) reverses the order in the second half or uses deity mapping with 60 names (Ghora, etc.). No deity association is computed today (not in `get_varga_sign`).
* **Missing**: varga degree (`(deg%0.5)*60` → 0-30 continuous), deity metadata, and method labeling. Extremely sensitive near 0.5° boundaries.
* **Verdict**: `TRADITION_DEPENDENT` / `NEEDS_VALIDATION` — pick sequential as default but expose `method` and document alternative.

---

## 4. Cross-Cutting Findings

| Area | Finding |
|------|---------|
| **Derivation vs recalculation** | VIOLATION: `build_chart_varga` consumes legacy `res_planets` which themselves call Swisseph directly; canonical `ChartFacts` is available in `pipeline.py` but not plumbed to Vargas. Phrase-2 requires Vargas to consume `ChartFacts.planets[].longitude.sidereal` only. |
| **Varga degree** | MISSING for all 16: only `longitude` (D1 long) returned. Step 20 requires `varga_degree = (deg_in_sign % segment_size) * (30/segment_size)` i.e. position inside derived sign (0≤d<30). |
| **Boundary handling** | No epsilon; floating boundary at exact segment size may flip part via rounding. Needs `EPSILON=1e-9` and `min(part, N-1)` clamping, plus half-open interval semantics. |
| **Method identifier** | Absent. Every Varga must carry `method` and ideally `segment_index`. |
| **D1 validation** | Phase 1 canonical already verified (39/39). D1 derivation in legacy `build_chart_varga` uses `int(lon//30)` without `floor` edge clamp — minor but should use `get_sign_from_longitude`. |
| **Testing** | No exhaustive varga tests exist. Only golden baseline lists D9/D10 per planet for 9 planets (9 samples). Exhaustive 12*N cases absent. |
| **Duplication** | `navamsa_sign_num` / `dashamsha_sign_num` duplicate subset of `get_varga_sign`; should be folded into unified pure engine. |
| **House handling** | Varga houses correctly use Whole Sign from Varga lagna; cusp degree intentionally None — correct. |
| **Backward compat** | Current keys `dN_sign`, `dN_sign_num`, `dN_longitude` must be preserved. New structured keys (`varga_degree`, `method`, `segment_index`) should be additive. |

---

## 5. Confidence Labels (per Step 30)

| Varga | Label | Reason |
|-------|-------|--------|
| D1 | VERIFIED | Phase 1 whole-sign |
| D2 | VERIFIED | Leo/Cancer Hora is dominant; alternative Hora-lords exist but rare |
| D3 | VERIFIED | 1st/5th/9th trinal |
| D4 | VERIFIED | Kendra chain—well attested |
| D7 | VERIFIED | odd/even Saptamsa |
| D9 | VERIFIED | movable/fixed/dual Navamsa |
| D10 | TRADITION_DEPENDENT | even=9th is dominant; even=8th variant documented elsewhere |
| D12 | VERIFIED | sequential Dwadasamsa |
| D16 | TRADITION_DEPENDENT | Aries/Leo/Sag start attested but some texts differ |
| D20 | TRADITION_DEPENDENT | same reason |
| D24 | VERIFIED | Leo/Cancer Siddhamsa |
| D27 | TRADITION_DEPENDENT | elemental Fire→Aries etc; continuous-from-Aries alternative exists |
| D30 | VERIFIED | Parashari Trimsamsa correctly irregular |
| D40 | VERIFIED | odd→Aries even→Libra |
| D45 | TRADITION_DEPENDENT | Aries/Leo/Sag mapping variant |
| D60 | TRADITION_DEPENDENT | sequential is one classical method; deity mapping & reversed-half variant exists |

---

## 6. Required Corrections (Blocking Phase 2)

1. Create `backend/core/calculation/varga.py` as pure derivation layer consuming only sidereal longitude + method; no Swisseph calls, no JD.
2. Implement shared `varga_segment_index(deg, division)` with epsilon and clamping.
3. Implement `varga_degree = (deg % segment_size) * divisions_mapped_to_30` — i.e. `fraction_in_segment * 30`.
4. Unify all 16 formulas under method `PARASHARI_CLASSICAL` with explicit start-sign tables; D30 branch uses cut-point table, not `deg/size`.
5. Extend `CalculationProfile` with `varga_method` and optional per-varga overrides.
6. Add `calculate_varga_position` and `calculate_all_vargas(chart_facts, profile)` APIs.
7. Integrate into `compute_chart` while preserving legacy keys; feed `ChartFacts` as source.
8. Create exhaustive programmatic tests (12*N per Varga, boundary epsilon tests, property tests).
9. Add documentation `ASTROLIFE_V2_VARGA_SPECIFICATION.md` and test report.

No Phase 1 astronomical formulas will be modified.

