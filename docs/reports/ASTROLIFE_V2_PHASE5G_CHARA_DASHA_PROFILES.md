# ASTROLIFE V2 — PHASE 5G-H — CHARA DASHA PROFILES

**Machine-readable manifest:** `backend/core/jaimini/dasha/profile.py` (PROFILE_REGISTRY)
**Golden snapshots:** `backend/golden_jaimini_dasha_snapshot.json` (Convention A)
**Cross-validation:** `backend/core/jaimini/dasha/reference.py` (independent reference)

---

## Implemented Profiles (3)

All profiles share the same core algorithm:
- **Start sign:** Lagna (Ascendant)
- **Duration:** Inclusive house-count to single-classical lord; OWN_SIGN_TWELVE = 12 years
- **Antardasha:** 12 equal subdivisions from parent sign in sequence direction
- **Birth balance:** NO_BIRTH_BALANCE (first mahadasha starts full at birth)
- **Year model:** MEAN_JULIAN_YEAR (365.25 days/year)
- **Boundary:** Half-open [start, end)
- **Levels:** MAHA_DASHA, ANTARDASHA
- **Source reference:** UNVERIFIED
- **Confidence:** TRADITION_DEPENDENT
- **Version:** 1.0.0

They differ ONLY in the **direction rule**:

---

### 1. CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL
**Convention A** — Movable/Fixed/Dual Parity (Modern Jaimini default)

| Sign Type | Signs | Direction |
|-----------|-------|-----------|
| Movable | Aries, Cancer, Libra, Capricorn | FORWARD |
| Fixed | Taurus, Leo, Scorpio, Aquarius | REVERSE |
| Dual (odd zodiac#) | Gemini (3), Sagittarius (9) | FORWARD |
| Dual (even zodiac#) | Virgo (6), Pisces (12) | REVERSE |

**Taurus → REVERSE** (Fixed)

**Sources:** Modern Jaimini texts (K.N. Rao, Sanjay Rath, V.P. Goel). Aligns with Rashi Drishti movable/fixed/dual classification. No direct sutra citation established.

---

### 2. CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED
**Convention B** — Odd/Even Footed (Direct/Indirect) — Classical

| Footed Type | Signs | Direction |
|-------------|-------|-----------|
| Odd-footed / Direct | Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius | FORWARD |
| Even-footed / Indirect | Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces | REVERSE |

**Taurus → FORWARD** (Odd-footed/Direct)

**Sources:** Classical commentaries (Bhatta Utpala 9th c., Neelakantha, Phaladeepika Ch.16-17, Saravali Ch.41-42, Jataka Parijata). 'Pada' (footed) classification distinct from movable/fixed/dual. Older and more widely attested in classical sources.

---

### 3. CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS
**Convention C** — Variant (Dual always FORWARD)

| Sign Type | Signs | Direction |
|-----------|-------|-----------|
| Movable | Aries, Cancer, Libra, Capricorn | FORWARD |
| Fixed | Taurus, Leo, Scorpio, Aquarius | REVERSE |
| Dual | Gemini, Virgo, Sagittarius, Pisces | FORWARD |

**Taurus → REVERSE** (Fixed)

**Sources:** Variant found in some modern practitioners. Less classically documented than A or B.

---

## Golden Chart Comparison (Taurus Ascendant)

| Convention | Profile ID | Direction | Cycle | First 4 Signs | First 3 Durations |
|------------|------------|-----------|-------|---------------|-------------------|
| A (Default) | `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL` | REVERSE | 92.0 yr | Taurus, Aries, Pisces, Aquarius | 9.0, 12.0, 7.0 |
| B (Classical) | `CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED` | FORWARD | 96.0 yr | Taurus, Gemini, Cancer, Leo | 5.0, 2.0, 6.0 |
| C (Variant) | `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL_ALWAYS` | REVERSE | 92.0 yr | Taurus, Aries, Pisces, Aquarius | 9.0, 12.0, 7.0 |

**Critical Discrepancy:** Taurus Ascendant produces **opposite directions** under Convention A (REVERSE) vs Convention B (FORWARD). Both are well-attested in different traditions. Neither can claim universal authority.

---

## Profile Selection

**DO NOT FORCE A SINGLE CANONICAL ANSWER.**

The user/application MUST explicitly select a profile:

```python
from core.jaimini.dasha.profile import JaiminiDashaProfile, CharaDashaProfileID

# Explicit choice required
profile = JaiminiDashaProfile.from_method(
    CharaDashaProfileID.CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED.value
)
# or
profile = JaiminiDashaProfile.from_method(
    CharaDashaProfileID.CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL.value
)
```

Each result carries the exact `profile_method` ID so downstream consumers know which convention generated the periods.

---

## Unsupported Traditions (Explicit Errors)

Requesting these raises `UnsupportedDashaMethodError` — never silently substituted:
- `CHARA_DASHA_PAKA_LAGNA_START`
- `CHARA_DASHA_ATMAKARAKA_START`
- `STHIRA_DASHA`
- `NARAYANA_DASHA`
- `BRAHMA_DASHA`
- `MANDOOKA_DASHA`
- `KARAKA_DASHA`
- `SUDASA_DASHA`

---

## Cross-Validation

All profiles verified against independent reference implementation (`backend/core/jaimini/dasha/reference.py`):
- ✅ All 12 ascendants × 3 profiles: direction matches reference
- ✅ All 144 periods × 3 profiles: durations + evidence match reference
- ✅ 144 lord positions tested for Convention A
- ✅ Own-sign exception (12 years) verified for all 7 lords
- ✅ Antardasha: containment, sequence, sums, linkage verified
- ✅ Golden chart: all 3 conventions computed and documented
- ✅ 50 consecutive evaluations byte-identical per profile
- ✅ Profile isolation: no cross-contamination

---

## Known Limitations

1. **Antardasha method:** 12 equal subdivisions implemented (TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT). Proportional and sign-based variants documented but not implemented — classical sources vary, no consensus established.

2. **Co-lord rule:** Single-classical lord only (Mars for Scorpio, Saturn for Aquarius). Co-lord-stronger method documented as unsupported; would require precise degree-comparison spec.

3. **Calendar year:** 365.25 days/year is an engineering convention. Classical texts specify "years" without calendar conversion.

4. **Birth balance:** NO_BIRTH_BALANCE assumed. Some modern practitioners use degree-based balance; no classical consensus.

5. **No VERIFIED confidence:** All profiles carry `source_reference = UNVERIFIED` and `confidence = TRADITION_DEPENDENT` per no-fabrication rule.

---

## Files

- `backend/core/jaimini/dasha/profile.py` — Profile definitions + registry
- `backend/core/jaimini/dasha/sequence.py` — Profile-aware direction/sequence
- `backend/core/jaimini/dasha/duration.py` — Duration with evidence
- `backend/core/jaimini/dasha/calculator.py` — Top-level calculation
- `backend/core/jaimini/dasha/reference.py` — Independent reference (no prod imports)
- `backend/core/jaimini/dasha/models.py` — Result models
- `backend/core/jaimini/dasha/validators.py` — Result validation
- `backend/test_jaimini_dasha_phase5g.py` — Phase 5G tests (38 passed)
- `backend/test_jaimini_dasha_phase5gh.py` — Phase 5G-H hardening tests (63 passed)
- `ASTROLIFE_V2_PHASE5G_HARDENING_AUDIT.md` — Source/tradition audit
- `ASTROLIFE_V2_PHASE5G_HARDENING_TEST_REPORT.md` — This test report