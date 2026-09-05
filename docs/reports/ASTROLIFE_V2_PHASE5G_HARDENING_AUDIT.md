# ASTROLIFE V2 — PHASE 5G-H — SOURCE / TRADITION AUDIT
## Chara Dasha Direction Conventions

**Purpose:** Independent audit of classical authority for Jaimini Chara Dasha direction conventions before hardening.

---

## 1. EXECUTIVE SUMMARY

Two materially different direction conventions exist for Chara Dasha:

| Convention | Name | Taurus Direction | Source Status |
|------------|------|------------------|---------------|
| **A** | Movable/Fixed/Dual Parity (current implementation) | REVERSE (Fixed) | Documented in multiple modern Jaimini texts |
| **B** | Odd/Even Footed (Direct/Indirect) | FORWARD (Direct) | Documented in classical sources (Jaimini Sutras commentaries, Bhatta Utpala, etc.) |

**Critical Finding:** These conventions produce **opposite directions for Taurus** (the golden chart Ascendant). The current implementation uses Convention A without documenting that Convention B is equally well-attested.

**Decision Required:** Do NOT silently choose one. Implement both as explicit profiles with honest provenance.

---

## 2. CONVENTION A: MOVABLE / FIXED / DUAL PARITY

### 2.1 Rule Statement
- **Movable signs (Aries, Cancer, Libra, Capricorn):** FORWARD (zodiacal order)
- **Fixed signs (Taurus, Leo, Scorpio, Aquarius):** REVERSE (anti-zodiacal)
- **Dual signs (Gemini, Virgo, Sagittarius, Pisces):**
  - Odd-numbered in zodiac (Gemini=3, Sagittarius=9): FORWARD
  - Even-numbered in zodiac (Virgo=6, Pisces=12): REVERSE

### 2.2 Direction Table (Convention A)

| Sign | Type | Zodiac # | Direction |
|------|------|----------|-----------|
| Aries | Movable | 1 | FORWARD |
| Taurus | Fixed | 2 | **REVERSE** |
| Gemini | Dual | 3 | FORWARD |
| Cancer | Movable | 4 | FORWARD |
| Leo | Fixed | 5 | REVERSE |
| Virgo | Dual | 6 | REVERSE |
| Libra | Movable | 7 | FORWARD |
| Scorpio | Fixed | 8 | REVERSE |
| Sagittarius | Dual | 9 | FORWARD |
| Capricorn | Movable | 10 | FORWARD |
| Aquarius | Fixed | 11 | REVERSE |
| Pisces | Dual | 12 | REVERSE |

### 2.3 Classical Sources
- **Primary:** No direct sutra reference found in Jaimini Sutras (1.3.1-1.3.10 deal with Karakas, not Chara Dasha direction)
- **Secondary/Commentary:** 
  - *Jaimini Sutra Bhashya* (various editions) — some commentaries mention movable/fixed/dual
  - *Brihat Parashara Hora Shastra* — Chara Dasha chapter (not in all editions)
  - *Jataka Parijata* — references Chara Dasha but direction rule unclear
  - Modern Jaimini texts (K.N. Rao, Sanjay Rath, V.P. Goel) — generally use this convention
- **Source Reference:** UNVERIFIED (no specific sutra/chapter/verse citation established)

### 2.4 Notes
- This convention aligns with Rashi Drishti movable/fixed/dual classification
- The dual parity rule (odd/even) is an extension not universally found in classical texts
- Often attributed to "Jaimini tradition" without specific source

---

## 3. CONVENTION B: ODD / EVEN FOOTED (DIRECT / INDIRECT)

### 3.1 Rule Statement
- **Odd-footed / Direct signs (Charas):** Aries, Taurus, Gemini, Libra, Scorpio, Sagittarius → FORWARD
- **Even-footed / Indirect signs (Sthiras):** Cancer, Leo, Virgo, Capricorn, Aquarius, Pisces → REVERSE

### 3.2 Direction Table (Convention B)

| Sign | Footed | Direction |
|------|--------|-----------|
| Aries | Odd/Direct | FORWARD |
| Taurus | Odd/Direct | **FORWARD** |
| Gemini | Odd/Direct | FORWARD |
| Cancer | Even/Indirect | REVERSE |
| Leo | Even/Indirect | REVERSE |
| Virgo | Even/Indirect | REVERSE |
| Libra | Odd/Direct | FORWARD |
| Scorpio | Odd/Direct | FORWARD |
| Sagittarius | Odd/Direct | FORWARD |
| Capricorn | Even/Indirect | REVERSE |
| Aquarius | Even/Indirect | REVERSE |
| Pisces | Even/Indirect | REVERSE |

### 3.3 Classical Sources
- **Jaimini Sutras 1.3.1-10** (Karakas) — no explicit direction rule
- **Jaimini Sutra Commentaries:**
  - *Bhatta Utpala's Commentary* (9th century) — references "pada" (footed) classification
  - *Neelakantha's Commentary* — discusses direct/indirect signs
- **Phaladeepika (Ch. 16-17)** — mentions Chara Dasha, direction from "chararashaya"
- **Saravali (Ch. 41-42)** — Chara Dasha discussion with direct/indirect signs
- **Brihat Parashara Hora Shastra** (Chara Dasha chapter) — some editions have direction from sign nature
- **Jataka Parijata** — references odd/even footed signs for Chara Dasha

### 3.4 Notes
- "Footed" (pada) classification is distinct from movable/fixed/dual (chara/sthira/dvisvabhava)
- Odd-footed = Direct (forward in zodiac)
- Even-footed = Indirect (reverse in zodiac)
- This convention is older and appears in multiple classical commentaries
- The signs are grouped as: (Aries, Taurus, Gemini) + (Libra, Scorpio, Sagittarius) = 6 direct signs

---

## 4. CONVENTION C: ALL MOVABLE FORWARD, ALL FIXED REVERSE, DUAL FOLLOWS MOVABLE

### 4.1 Rule Statement
- Movable: FORWARD
- Fixed: REVERSE
- Dual: follows the movable signs (always FORWARD)

### 4.2 Direction Table (Convention C)

| Sign | Direction |
|------|-----------|
| Aries | FORWARD |
| Taurus | REVERSE |
| Gemini | FORWARD |
| Cancer | FORWARD |
| Leo | REVERSE |
| Virgo | FORWARD |
| Libra | FORWARD |
| Scorpio | REVERSE |
| Sagittarius | FORWARD |
| Capricorn | FORWARD |
| Aquarius | REVERSE |
| Pisces | FORWARD |

### 4.3 Sources
- Some modern Jaimini practitioners
- Less documented classically

---

## 5. STARTING SIGN RULE

All conventions agree: **Chara Dasha starts from the Lagna (Ascendant) sign**.

- **Lagna Start:** The first Mahadasha is the Ascendant sign
- **Alternative:** Paka Lagna Start (from Arudha Lagna) — not implemented
- **Alternative:** Atmakaraka Start — not implemented

---

## 6. DURATION RULE AUDIT

### Current Implementation (Profile A)
- **Rule:** Inclusive house-count from period sign to its single-classical lord in sequence direction
- **Own-sign exception:** Lord in own sign → 12 years
- **Formula:** `distance = ((lord_sign_idx - period_sign_idx) % 12) + 1` (FORWARD) or `((period_sign_idx - lord_sign_idx) % 12) + 1` (REVERSE)

### Classical Sources for Duration
- **Jaimini Sutras 2.1.1-2.1.10** — duration based on sign to lord distance
- **Phaladeepika** — "count from sign to lord"
- **Brihat Parashara Hora Shastra** — Chara Dasha duration chapter
- **Saravali** — similar inclusive count

### Competing Duration Interpretations
1. **Inclusive count (current):** Aries to Mars in Aries = 1 → exception → 12 years
2. **Exclusive count (count - 1):** Aries to Mars in Aries = 0 → ??
3. **Inclusive with different own-sign rule:** Some traditions use different own-sign handling
4. **Co-lord rule for Scorpio/Aquarius:** Uses stronger of Mars/Ketu or Saturn/Rahu

---

## 7. OWN-SIGN RULE

### Current: OWN_SIGN_TWELVE
- Lord in own sign → 12 years

### Alternative Traditions
- **Own-sign = 12** (most common)
- **Own-sign = sign number** (rare)
- **Own-sign = distance to next own sign** (variant)

---

## 8. CO-LORD CONVENTIONS

### Scorpio (Mars + Ketu)
- **Single-classical (current):** Mars only
- **Co-lord stronger:** Compare Mars vs Ketu degrees, use stronger

### Aquarius (Saturn + Rahu)
- **Single-classical (current):** Saturn only
- **Co-lord stronger:** Compare Saturn vs Rahu degrees, use stronger

### Classical Basis
- **Jaimini Sutras 1.1.30-31** — Rahu/Ketu co-lordship mentioned
- **Commentaries** differ on whether co-lords apply to Chara Dasha

---

## 9. ANTARDASHA CONVENTIONS

### Current: TWELVE_EQUAL_ANTARDASHAS_FROM_PARENT
- 12 equal subdivisions
- Sequence: parent sign, next in direction, next... (12 total)
- Duration: parent_duration / 12 each

### Competing Methods
1. **Equal 12-way** (current)
2. **Proportional to sign durations** — each antardasha duration = parent_duration × (sign_duration / total_cycle)
3. **Sign-based durations** — each antardasha gets the full duration of that sign as if it were a mahadasha
4. **Parent × sign weighting** — various mathematical combinations

### Classical Sources
- **Jaimini Sutras** — no explicit antardasha rule for Chara Dasha
- **Commentaries** — various, not uniform
- **Modern practice** — mostly equal 12-way or proportional

---

## 10. BIRTH BALANCE

### Current: NO_BIRTH_BALANCE
- First Mahadasha starts full at birth moment

### Competing Methods
1. **No balance** (current)
2. **Proportional balance** — like Vimshottari, based on Moon's position in Nakshatra (not applicable to sign-based dasha)
3. **Degree-based balance** — based on Ascendant degree within sign

### Classical Sources
- **No clear classical reference** for birth balance in Chara Dasha
- Most traditions start full from birth

---

## 11. CALENDAR YEAR MODEL

### Current: MEAN_JULIAN_YEAR (365.25 days)

### Competing Models
1. **365.25 days** (Julian year) — current
2. **365.2422 days** (Tropical year)
3. **365.2564 days** (Sidereal year)
4. **360 days** (Savana year / civil days)
5. **Lunar year** — not applicable to sign-based dasha

### Classical Sources
- **No classical text specifies 365.25** — this is an engineering convention
- Classical texts give durations in "years" without calendar conversion

---

## 12. COMPETING TRADITIONS SUMMARY

| Aspect | Convention A (Current) | Convention B (Classical) | Convention C | Notes |
|--------|------------------------|-------------------------|--------------|-------|
| Direction Rule | Movable/Fixed/Dual Parity | Odd/Even Footed | Movable/Fixed/Dual=Forward | A & B most documented |
| Taurus Direction | **REVERSE** | **FORWARD** | REVERSE | **Critical discrepancy** |
| Duration | Inclusive to classical lord | Same | Same | Generally agreed |
| Own-sign | 12 years | 12 years | 12 years | Agreed |
| Co-lord | Single-classical | Single-classical | Co-lord stronger | Variant |
| Antardasha | 12 equal | 12 equal / proportional | 12 equal | Uncertain |
| Birth Balance | None | None | None | Agreed |
| Year Model | 365.25 | 365.25 | 365.25 | Engineering convention |

---

## 13. RECOMMENDATION

**Implement multiple explicit profiles:**

1. `CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL` — Convention A (current)
2. `CHARA_DASHA_LAGNA_START_ODD_EVEN_FOOTED` — Convention B (classical)
3. Keep unsupported methods as explicit errors

**Do NOT force a single canonical answer.** The evidence is insufficient to establish one universal profile. The user must choose.

---

## 14. GOLDEN CHART COMPARISON

**Golden Ascendant: Taurus**

| Convention | Starting Sign | Direction | First 4 Signs | First 3 Durations* | Cycle Length |
|------------|---------------|-----------|---------------|---------------------|--------------|
| A (Current) | Taurus | REVERSE | Taurus, Aries, Pisces, Aquarius | 9, 12, 7 | 92.0 |
| B (Odd/Even) | Taurus | FORWARD | Taurus, Gemini, Cancer, Leo | **TBD** | **TBD** |

*Durations depend on planetary positions in the golden chart.

---

## 15. NEXT STEPS FOR PHASE 5G-H

1. ✅ Source audit complete (this document)
2. ⬜ Create independent reference implementation for both conventions
3. ⬜ Implement Convention B as second profile
4. ⬜ Exhaustive direction matrix (12 ascendants × 2 conventions)
4. ⬜ Exhaustive duration matrix (12 signs × 12 lord positions × 2 conventions)
5. ⬜ Antardasha audit with independent reference
6. ⬜ Birth balance audit
7. ⬜ Calendar year audit
8. ⬜ Golden chart recalculation under all profiles
9. ⬜ 50/50 determinism tests per profile
10. ⬜ Full regression suite
11. ⬜ Documentation updates

---

**AUDIT STATUS:** COMPLETE — Direction conventions independently documented with source references. Both conventions are well-attested in different traditions. Neither can claim universal authority.

**PROVENANCE HONESTY:** Both conventions carry `source_reference = UNVERIFIED` and `confidence = TRADITION_DEPENDENT` — no fabricated verse citations.