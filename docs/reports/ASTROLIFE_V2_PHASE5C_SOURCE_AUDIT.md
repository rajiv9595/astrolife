# ASTROLIFE V2 — PHASE 5C: DOSHA SOURCE AUDIT

## Audit Date: Phase 5C Implementation
## Auditor: Deterministic Rule Engine Audit

---

## 1. MANGLIK / KUJA DOSHA

### Name
Manglik Dosha / Kuja Dosha / Mars Dosha

### Source Tradition
Hindu Vedic — multiple traditions disagree on scope and cancellation

### Primary Source (if verified)
Brihat Parashara Hora Shastra (BPHS) — attributed to Parashara
- The BPHS references Mars in specific houses causing affliction to marriage
- UNVERIFIED exact verse numbers (cannot fabricate verse references)

### Secondary References
- Phaladeepika (Mantreshwara) — mentions Mars affliction
- Jataka Parijata (Vaidyanatha Dikshita) — Manglik analysis
- Saravali (Kalyana Varma) — Mars in dusthana/kendra analysis
- Various regional traditions (South Indian, North Indian, Bengal)

### Exact Definition
Mars placed in specific houses from Lagna, Moon, or Venus causes "Manglik Dosha"
afflicting marriage and partnership prospects.

### Alternative Definitions (CRITICAL — many disagree)

**Method A: Lagna Reference (most common)**
- Affected houses from Lagna: 1, 2, 4, 7, 8, 12
- Mars in these houses from Lagna = Manglik

**Method B: Moon Reference**
- Same house set but counted from Moon sign
- Some traditions use Moon-only

**Method C: Venus Reference**
- Same house set counted from Venus sign
- Primarily for marriage compatibility assessment

**House Set Disagreements:**
- Most common: {1, 2, 4, 7, 8, 12}
- Some exclude house 2
- Some include house 12 only for specific cancellation contexts
- South Indian traditions may differ

### Cancellation Rules (commonly listed)
1. Mars in own sign (Aries, Scorpio) — disputed cancellation
2. Mars exalted (Capricorn) — disputed
3. Mars conjunct Jupiter — widely cited
4. Mars conjunct Moon — widely cited
5. Mars aspected by Jupiter — widely cited
6. Jupiter in ascendant — some traditions
7. Mars in 2nd/12th in specific signs — very tradition-dependent

**NOT ALL cancellation rules are universally accepted.**
Many cancellation lists on the internet are compilations without source.

### Severity Assessment
NOT universally agreed:
- Some count number of affected reference points (Lagna/Moon/Venus)
- Some weight by house position
- Some weight by Mars dignity
- NO validated classical numerical severity scale exists

### Whether Formation is Universally Accepted
YES — Mars in affected houses from reference point is widely accepted.
NO — the reference point(s) and exact house set are NOT universally agreed.

### Whether Severity is Tradition-Dependent
YES — completely tradition-dependent

### Whether the Dosha is Controversial
YES — the scope and cancellation rules are actively debated.

### Implementation Decision
**IMPLEMENT** with explicit method separation:
- `DOSHA.MANGLIK.LAGNA_CLASSICAL` — Mars in {1,2,4,7,8,12} from Lagna
- `DOSHA.MANGLIK.MOON_REFERENCE` — Mars in {1,2,4,7,8,12} from Moon
- `DOSHA.MANGLIK.VENUS_REFERENCE` — Mars in {1,2,4,7,8,12} from Venus
Each method records its own formation, cancellation, mitigation, severity.

---

## 2. KEMADRUMA DOSHA

### Name
Kemadruma Dosha / Kemadruma Yoga

### Source Tradition
Parashari Classical — part of Parashari yoga/dosha system

### Primary Source (if verified)
Brihat Parashara Hora Shastra (BPHS)
- Attributed to Parashara: planets flanking Moon (2nd/12th) and kendra from Moon
- UNVERIFIED exact verse numbers

### Secondary References
- Phaladeepika — discusses Moon isolation
- Saravali — Moon-related afflictions
- Jataka Parijata — Kemadruma analysis

### Exact Definition (Classical)
Kemadruma forms when:
1. No planet occupies the 2nd house from Moon
2. No planet occupies the 12th house from Moon
3. No planet occupies any kendra (1,4,7,10) from Moon (excluding Moon itself)

### Alternative Definitions
- SIMPLISTIC (internet): "no planets beside Moon" — TOO SIMPLE, ignores kendra
- STRICT CLASSICAL: all three conditions must be met
- SOME exclude Sun from the check (Sun's conjunction with Moon = Amavasya, special case)

### Cancellation Rules
1. Jupiter aspect on Moon — widely cited
2. Saturn aspect on Moon — some traditions
3. Sun conjunction with Moon — debated (Amavasya special case)
4. Venus conjunction with Moon — some traditions
5. Yogakaraka planet in kendra from Moon — some traditions

### Severity Assessment
- Classical: Kemadruma is considered a significant affliction
- No validated numerical scale
- Categorical: NONE / MODERATE / SIGNIFICANT

### Whether Formation is Universally Accepted
YES — the concept is widely accepted in Parashari tradition.
The exact conditions vary slightly by commentator.

### Whether Severity is Tradition-Dependent
YES — cancellation rules vary

### Whether the Dosha is Controversial
MODERATE — the core concept is stable, cancellations vary

### Implementation Decision
**IMPLEMENT** as a separate Dosha from the Phase 5B Kemadruma yoga.
Use strict classical definition (2nd, 12th, kendra-from-Moon).
Mark as PARASHARI_CLASSICAL with UNVERIFIED exact verse.
Note: Phase 5B already has a Kemadruma YOGA — the Dosha version adds
severity/cancellation/mitigation analysis beyond yoga formation.

---

## 3. KALA SARPA DOSHA

### Name
Kala Sarpa Dosha / Kala Sarpa Yoga

### Source Tradition
TRADITION_DEPENDENT — NOT universally accepted as Parashari Classical

### Primary Source (if verified)
- NOT found in BPHS (Brihat Parashara Hora Shastra)
- NOT found in Phaladeepika
- NOT found in Saravali
- Origin uncertain — possibly medieval or regional tradition
- Some attribute to "Kataka Khoda" or unnamed classical source — UNVERIFIED

### Secondary References
- Modern Vedic astrology textbooks (various authors)
- Regional traditions (Rajasthan, Gujarat, South India)
- Popularized in 20th century astrology

### Exact Definition
All seven classical planets (Sun, Moon, Mars, Mercury, Jupiter, Venus, Saturn)
are hemmed between Rahu and Ketu (one side of the nodal axis).

### Alternative Definitions
**Method A: Sign-based containment**
- All 7 planets in signs between Rahu sign and Ketu sign (clockwise or counterclockwise)

**Method B: Degree-based containment**  
- All 7 planets within the arc from Rahu longitude to Ketu longitude

**Method C: Strict sign (nodes exclusive)**
- Planets on the exact Rahu or Ketu sign boundary do NOT count as contained

**Method D: Strict sign (nodes inclusive)**
- Planets on Rahu or Ketu sign boundary DO count

### Boundary Handling Disagreements
- Whether a planet at 0° Aries (start of zodiac) counts as inside/outside
- Whether the wrap-around at 0°/360° is handled
- Whether outer planets (Uranus, Neptune, Pluto) are included — NO for Vedic
- Whether retrograde nodes change the axis

### Cancellation Rules
1. Jupiter in Ascendant — widely cited
2. Jupiter aspecting Rahu — widely cited
3. Multiple benefic aspects — tradition-dependent
4. No universally agreed cancellation set

### Severity Assessment
NO validated classical severity scale.
Modern astrology sites use arbitrary scoring.
Categorical: FORMED / NOT_FORMED / PARTIAL / UNCERTAIN

### Whether Formation is Universally Accepted
NO — this is one of the most debated doshas in Vedic astrology.

### Whether Severity is Tradition-Depent
YES — highly tradition-dependent

### Whether the Dosha is Controversial
YES — many scholars do not recognize it as a classical dosha.

### Implementation Decision
**IMPLEMENT** with explicit TRADITION_DEPENDENT classification.
Use sign-based containment as primary method (Method A).
Document as tradition-dependent with medium confidence.
Do NOT label as PARASHARI_CLASSICAL.

---

## 4. PITRU DOSHA

### Name
Pitru Dosha / Pitra Dosha / Pitri Dosha

### Source Tradition
Hindu tradition — partially textual, partially oral tradition

### Primary Source (if verified)
- NOT a clearly defined classical Parashari dosha in BPHS
- Concept of "Pitri" (ancestors) is classical
- The specific dosha formation rules are largely modern/secondary

### Secondary References
- Modern Vedic astrology textbooks
- Pitrupaksha / Shradh traditions (ritual, not astrological)
- Some references in Jataka Parijata — UNVERIFIED exact attribution

### Exact Definition (Modern Common)
Sun or Moon conjunct Rahu or Ketu, OR Rahu/Ketu placed in 9th house.

### Alternative Definitions
1. Sun conjunct Rahu (most common single indicator)
2. Sun conjunct Rahu OR Ketu
3. Moon conjunct Rahu OR Ketu
4. Rahu/Ketu in 9th house from Lagna
5. Rahu/Ketu in 9th house from Moon
6. Any combination of above

### Cancellation Rules
- Very few universally agreed cancellation rules
- Some cite Jupiter aspect as cancellation
- Very tradition-dependent

### Severity Assessment
NO validated classical scale.
Modern websites assign arbitrary severity.

### Whether Formation is Universally Accepted
NO — the specific astrological formation rules are modern synthesis.
The concept of ancestral affliction is traditional; the specific chart indicators are secondary.

### Whether Severity is Tradition-Dependent
YES — highly

### Whether the Dosha is Controversial
YES — many classical scholars do not recognize this as a standalone dosha.

### Implementation Decision
**IMPLEMENT** with conservative classification.
Mark as TRADITION_DEPENDENT or UNVERIFIED.
Implement only the most commonly cited conditions.
Document clearly that the astrological formation rules are secondary/modern.
Do NOT generate deterministic predictions from it.

---

## 5. GRAHANA / ECLIPSE AFFLICTION

### Name
Grahan Dosha / Eclipse Affliction

### Source Tradition
Multiple — both astronomical and astrological

### Primary Source (if verified)
- Eclipse as astronomical event — scientific
- Eclipse-related dosha in astrology — various modern sources
- Classical texts mention eclipses but not as permanent natal doshas

### Exact Definition
Birth during or near an eclipse (solar or lunar) creates an affliction.

### Key Distinction
- ASTRONOMICAL ECLIPSE = momentary event at birth
- PERMANENT NATAL DOSHA = not universally accepted from a single eclipse at birth
- Classical texts treat eclipses as transit events, not natal formations

### Implementation Decision
**DO NOT IMPLEMENT as a named dosha.**
The concept of a permanent natal dosha from birth eclipse is modern.
If needed, represent as a generic affliction modifier, not a named dosha.

---

## 6. GENERIC PLANETARY AFFLICTION LOGIC

### Name
Generic Afflictions / Planetary Afflictions

### Source Tradition
Parashari Classical — for individual affliction concepts

### Components
1. **Conjunction with malefic** — classical (Sun, Mars, Saturn, Rahu, Ketu are natural malefics)
2. **Malefic aspect** — classical (Parashari aspects from malefics)
3. **Combustion** — classical (planet too close to Sun)
4. **Debilitation** — classical (neecha position)
5. **Severe dignity weakness** — derived from classical dignity system
6. **House affliction** — planet in dusthana (6, 8, 12)
7. **Node affliction** — Rahu/Ketu conjunction — PARTIALLY classical

### Whether Formation is Universally Accepted
YES for individual concepts (debilitation, combustion, etc.)
NO for mapping individual afflictions to named doshas

### Implementation Decision
**IMPLEMENT** as reusable affliction evaluation functions.
Do NOT automatically create named doshas from generic afflictions.
Keep "node_affliction" separate from "named_dosha".

---

## 7. SHAKATA DOSHA

### Name
Shakata Dosha

### Source Tradition
Attributed to Parashara — UNVERIFIED

### Definition
Moon in certain houses from Jupiter (2nd, 4th, 5th, 7th, 8th, 9th, 11th, 12th)
or Jupiter in certain houses from Moon.

### Implementation Decision
**DEFER** — not implementing in Phase 5C. Too many alternative definitions
without clear classical provenance. May be added in future phase.

---

## 8. CHANDRA DOSHA (Separate from Kemadruma)

### Name
Various Chandra-related afflictions

### Implementation Decision
**ABSORBED** into Kemadruma implementation where applicable.
Not implementing as separate named doshas in Phase 5C.

---

## 9. VASHI Dosha

### Name
Vashi Dosha / Vashikarana Dosha

### Source Tradition
Modern practice — not classical

### Implementation Decision
**DO NOT IMPLEMENT** — modern practice, no clear classical source.

---

## 10. HUBBIE DOSHA (Naming Pattern)

Various obscure doshas commonly listed on websites without clear source.

### Implementation Decision
**DO NOT IMPLEMENT** doshas without clear classical or well-attested traditional source.

---

## SUMMARY TABLE

| Dosha | Tradition | Source | Confidence | Implementation |
|-------|-----------|--------|------------|----------------|
| Manglik/Kuja | Multiple | BPHS (attributed) | HIGH | YES — 3 methods |
| Kemadruma | Parashari | BPHS (attributed) | HIGH | YES — strict classical |
| Kala Sarpa | Tradition-Dependent | Uncertain | MEDIUM | YES — explicitly tradition-dependent |
| Pitru Dosha | Tradition-Dependent | Modern synthesis | LOW | YES — conservative, UNVERIFIED label |
| Grahan/Eclipse | Modern | No classical | LOW | NO |
| Shakata | Attributed | UNVERIFIED | LOW | NO (deferred) |
| Generic Afflictions | Parashari | Classical concepts | HIGH | YES — reusable functions |
| Vashi | Modern | No classical | LOW | NO |

---

## LEGACY CODE AUDIT

### backend/doshas_advanced.py
- `check_kala_sarpa_dosha()` — sign-based, simple
  - No method metadata
  - No boundary handling documentation
  - No partial case handling
  - **REPLACE** with Phase 5C implementation
  
- `check_pitru_dosha()` — simplified definition
  - No method metadata
  - No tradition classification
  - **REPLACE** with Phase 5C implementation

### backend/calculations.py (calculate_mangal_dosha)
- Checks Lagna, Moon, Venus references — GOOD
- House set {1,2,4,7,8,12} — most common
- Cancellation rules — mixture of traditions, some internet-derived
  - Own sign cancellation — disputable
  - Exaltation cancellation — disputable
  - "Friendly sign" cancellation (Leo, Cancer) — internet
  - House-specific sign exceptions — internet
  - Jupiter/Moon conjunction — widely cited
  - Jupiter/Moon aspect — widely cited
- **REPLACE** with Phase 5C implementation that separates methods and sources

### frontend consumption
- `MangalDoshaCard.jsx` — consumes `mangal_dosha` from compute_chart
- `AdvancedDoshasCard.jsx` — consumes `advanced_doshas` from compute_chart
- Phase 5C will produce new engine output; legacy endpoints maintained for compatibility
