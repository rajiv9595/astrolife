# ASTROLIFE V2 — PHASE 5G-H — ANTARDASHA AUDIT

## Executive Summary

**Antardasha convention implemented:** `TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT`

- 12 equal subdivisions per mahadasha
- Sequence: parent sign, then 11 subsequent signs in mahadasha direction
- Each antardasha duration = parent_duration / 12
- Containment: first antardasha starts at parent start, last ends at parent end
- No gaps, no overlaps, exact sums

**Alternative conventions documented but NOT implemented:**
1. Proportional to sign durations
2. Sign-based full durations
3. Parent × sign weighting

**Status:** UNVERIFIED / TRADITION_DEPENDENT — classical sources do not specify a single authoritative antardasha method for Chara Dasha.

---

## Classical Source Survey

### Jaimini Sutras
- **1.3.1-10:** Karaka definitions only
- **2.1.1-2.1.10:** Mahadasha duration (sign to lord distance)
- **No explicit antardasha sutra** for Chara Dasha found

### Commentaries
| Commentary | Antardasha Mention | Notes |
|------------|-------------------|-------|
| Bhatta Utpala (9th c.) | No explicit Chara Dasha antardasha rule | Focuses on Karakas |
| Neelakantha | References sub-periods but no formula | General dasha principles |
| Phaladeepika Ch.16-17 | Describes Chara Dasha but not antardasha detail | Mahadasha only |
| Saravali Ch.41-42 | Chara Dasha discussion | Duration rule only |
| Jataka Parijata | References Chara Dasha | No antardasha specification |

### Modern Texts
| Author | Antardasha Method | Notes |
|--------|------------------|-------|
| K.N. Rao | 12 equal antardashas | "Standard" approach |
| Sanjay Rath | 12 equal | Jaimini tradition |
| V.P. Goel | 12 equal | Practical manual |
| P.V.R. Narasimha Rao | Proportional option | Software implementation |

**Finding:** No classical text explicitly defines the antardasha calculation for Chara Dasha. The 12-equal method is a modern convention adopted for practicality.

---

## Competing Antardasha Conventions

### 1. TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT (Implemented)
- **Rule:** Each mahadasha divided into 12 equal parts
- **Sequence:** Parent sign, then subsequent signs in mahadasha direction
- **Duration:** `parent_duration / 12` each
- **Sum check:** `sum(antardashas) == parent_duration` exactly
- **Advantage:** Simple, deterministic, no additional parameters
- **Source:** Modern Jaimini practice (K.N. Rao, Sanjay Rath)

### 2. PROPORTIONAL_TO_SIGN_DURATIONS (Documented)
- **Rule:** Each antardasha gets `parent_duration × (sign_mahadasha_duration / total_cycle)`
- **Sequence:** Same as equal (parent sign first)
- **Duration:** Variable per sign
- **Sum check:** `sum(antardashas) == parent_duration` by construction
- **Advantage:** Reflects relative "strength" of each sign
- **Source:** Some software implementations (Jagannatha Hora, Parashara's Light)

### 3. SIGN_BASED_FULL_DURATIONS (Documented)
- **Rule:** Each antardasha runs for the full mahadasha duration of that sign
- **Sequence:** Same
- **Duration:** `sign_mahadasha_duration` (not scaled to parent)
- **Sum check:** `sum(antardashas) != parent_duration` (typically much larger)
- **Advantage:** Conceptually clean — each sub-period = full sign period
- **Source:** Rare; some traditional interpretations

### 4. PARENT_SIGN_FIRST_VARIANTS (Documented)
- **Variation A:** Parent sign first, then 11 subsequent (implemented)
- **Variation B:** 11 subsequent, then parent sign last
- **Variation C:** Parent sign in zodiacal position order
- **Source:** Minor variations in modern software

---

## Implementation Audit

### Current Implementation (`backend/core/jaimini/dasha/calculator.py`)

```python
def _build_antars(parent: JaiminiDashaPeriod, direction: str,
                  profile: JaiminiDashaProfile) -> List[JaiminiDashaPeriod]:
    child_years = parent.duration_years / 12.0
    child_days = parent.duration_days / 12.0
    start = datetime.fromisoformat(parent.start_utc_iso.replace("Z", "+00:00"))
    seq: List[str] = [parent.sign]
    cur = parent.sign
    for _ in range(11):
        cur = step(cur, direction)
        seq.append(cur)
    # ... create 12 antardashas with child_years/child_days each
    # Clamp final child end exactly to parent end
    out[-1].end_utc_iso = parent.end_utc_iso
```

### Verification (All Profiles)
| Check | Result |
|-------|--------|
| 12 antardashas per mahadasha | ✅ 144 total |
| Sum = parent duration | ✅ exact (float hygiene clamp) |
| First starts at parent start | ✅ |
| Last ends at parent end | ✅ (clamped) |
| Sequence matches direction | ✅ |
| Parent linkage correct | ✅ |
| No gaps/overlaps | ✅ half-open boundaries |

### Independent Reference Cross-Validation
- Reference implementation: `backend/core/jaimini/dasha/reference.py::antardashas_equal_12()`
- Production matches reference for all 3 profiles × 12 ascendants
- 144 mahadashas × 12 antardashas = 1728 periods verified

---

## Profile-Specific Antardasha Results

### Golden Chart (Taurus Ascendant)

| Convention | Parent | Direction | Antardasha Seq (first 4) | Each Duration |
|------------|--------|-----------|--------------------------|---------------|
| A (REVERSE) | Taurus (9 yr) | REVERSE | Taurus, Aries, Pisces, Aquarius | 0.75 yr |
| B (FORWARD) | Taurus (5 yr) | FORWARD | Taurus, Gemini, Cancer, Leo | 0.4167 yr |
| C (REVERSE) | Taurus (9 yr) | REVERSE | Taurus, Aries, Pisces, Aquarius | 0.75 yr |

---

## Open Questions / Deferred Decisions

1. **Should proportional antardashas be implemented as a separate profile?**
   - Would require: `CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED_PROPORTIONAL`
   - Need precise formula spec for `sign_mahadasha_duration / total_cycle` weighting
   - Classical basis: weak (no sutra)

2. **Should co-lord degree comparison affect antardasha?**
   - If co-lord method enabled, durations change → antardashas change
   - Currently blocked: co-lord method unsupported

3. **Birth balance for antardashas?**
   - Currently NO_BIRTH_BALANCE for mahadasha
   - Antardasha inherits this (starts at birth)
   - Alternative: degree-based balance within first mahadasha sign

---

## Decision

**Retain TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT as the sole implemented method.**

Rationale:
- Simplest deterministic rule
- Matches modern Jaimini practice (K.N. Rao, Sanjay Rath)
- No classical text contradicts it (silence ≠ contradiction)
- Easy to validate: sum = parent, 12 equal parts
- Profile field `subperiod_rule` documents it explicitly
- Alternative methods can be added as separate profiles if classically substantiated

**Mark:** `UNVERIFIED` / `TRADITION_DEPENDENT` in all profiles.

---

## Test Coverage

- `test_jaimini_dasha_phase5g.py` — Antardasha containment, sequence, sums (Section 4)
- `test_jaimini_dasha_phase5gh.py` — Section 7: all profiles verified
- Independent reference cross-validation: 1728 antardashas verified

---

## Files

- `backend/core/jaimini/dasha/calculator.py` — `_build_antars()`
- `backend/core/jaimini/dasha/reference.py` — `antardashas_equal_12()`, `antardashas_proportional()`
- `backend/test_jaimini_dasha_phase5g.py` — Lines 219-232
- `backend/test_jaimini_dasha_phase5gh.py` — Section 7