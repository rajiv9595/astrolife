# ASTROLIFE V2 — PHASE 5E: JAIMINI RULE CATALOGUE

**Version:** 1.0.0
**Rules implemented:** 12 (deliberately small; only precisely specifiable rules)
**Global provenance:** tradition `JAIMINI`, source_reference `UNVERIFIED`,
confidence `TRADITION_DEPENDENT`. No verse/adhyaya citations claimed.

Golden-chart formation (engine-generated): 3 / 12 formed —
`JAI.ARUDHA.AL_LORD_KENDRA_TRINE`, `JAI.DRISHTI.AK_AMK_MUTUAL`,
`JAI.KARAKAMSHA.BENEFIC_OCCUPANCY`.

| Rule ID | Name | Origin | Method | Formation condition | Required inputs | Cancellation | Mitigation | Golden |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| JAI.KARAKA.AK_AMK_CONJUNCTION | AK–AmK Conjunction Combination | CLASSICAL_JAIMINI | ak_amk_conjunction | AK & AmK same D1 sign | chara_karakas | PARTIAL on AK/AmK degree tie, else NONE | PARTIAL on benefic support of AK sign, else NONE | NOT FORMED (Virgo vs Sagittarius) |
| JAI.KARAKA.AK_KENDRA_FROM_AL | AK in Kendra from AL | TRADITION_DEPENDENT | ak_kendra_from_al | AK sign in kendra (1/4/7/10) from AL | chara_karakas, A1 | tie→PARTIAL, else NONE | benefic support → PARTIAL | NOT FORMED (house 9) |
| JAI.KARAKA.DK_UL_SAMBANDHA | DK–UL Sambandha | TRADITION_DEPENDENT | dk_ul_sambandha | DK in UL (occupation) OR DK==UL lord (lordship) OR mutual drishti DK↔UL-lord; mode recorded | chara_karakas, UL, rashi_drishti, D1 occupancy | tie→PARTIAL, else NONE | benefic support of UL → PARTIAL | NOT FORMED |
| JAI.DRISHTI.AK_AMK_MUTUAL | AK–AmK Mutual Rashi Drishti | CLASSICAL_JAIMINI | ak_amk_mutual_drishti | mutual drishti, same-sign excluded (disjoint from conjunction) | chara_karakas, rashi_drishti | tie→PARTIAL, else NONE | benefic support → PARTIAL | FORMED (Virgo↔Sagittarius duals) |
| JAI.DRISHTI.AMK_ON_AL | AmK Rashi Drishti on AL | TRADITION_DEPENDENT | amk_on_al | AmK aspects AL via occupied sign | chara_karakas, A1, rashi_drishti | tie→PARTIAL, else NONE | benefic support of AL → PARTIAL | NOT FORMED |
| JAI.DRISHTI.AK_ON_AL | AK Rashi Drishti on AL | TRADITION_DEPENDENT | ak_on_al | AK aspects AL via occupied sign | chara_karakas, A1, rashi_drishti | tie→PARTIAL, else NONE | benefic support of AL → PARTIAL | NOT FORMED |
| JAI.ARUDHA.AL_BENEFIC_OCCUPANCY | Benefic in AL | CLASSICAL_JAIMINI | al_benefic_occupancy | Jupiter/Venus/Mercury/Moon in AL (D1) | A1, D1 occupancy | NONE (factual) | benefic support → PARTIAL | NOT FORMED (Capricorn empty) |
| JAI.ARUDHA.AL_LORD_KENDRA_TRINE | AL Lord in Kendra/Trikona from AL | CLASSICAL_JAIMINI | al_lord_kendra_trine | AL lord in house {1,4,5,7,9,10} from AL | A1, D1 occupancy | NONE (factual) | benefic support of AL → PARTIAL | FORMED (Saturn in Cancer, 7th from Capricorn AL) |
| JAI.ARUDHA.DHANA_A2_A11 | A2–A11 Dhana Combination | CLASSICAL_JAIMINI | dhana_a2_a11 | same sign OR mutual drishti OR shared lord; mode recorded | A2, A11 | NONE (factual) | benefic support of A2/A11 → PARTIAL | NOT FORMED (Leo vs Sagittarius, distinct lords) |
| JAI.ARUDHA.A7_UL_ALIGNMENT | A7–UL Alignment | TRADITION_DEPENDENT | a7_ul_alignment | A7 == UL | A7, UL | NONE (factual) | benefic support of UL → PARTIAL | NOT FORMED (Virgo vs Capricorn) |
| JAI.KARAKAMSHA.BENEFIC_OCCUPANCY | Benefic in Karakamsha (D9) | TRADITION_DEPENDENT | karakamsha_benefic_occupancy | benefic in AK's D9 sign | karakamsha, D9 occupancy | NONE (factual) | NONE (D9 scope; D1 drishti N/A) | FORMED (Jupiter in Cancer D9) |
| JAI.SWAMSA.BENEFIC_OCCUPANCY | Benefic in Swamsa (D9) | TRADITION_DEPENDENT | swamsa_benefic_occupancy | benefic in D9 Lagna sign | karakamsha (Swamsa), D9 occupancy | NONE (factual) | NONE (D9 scope) | NOT FORMED |

## Intentionally Excluded (with reason)

* Jaimini dashas (Chara/Sthira/Mandooka etc.) — later phase by scope order.
* Event timing / marriage-age / career / wealth-amount claims — prediction,
  out of scope for a rule engine.
* Dignity-based karaka rules (e.g. AK exaltation) — would add a strength-engine
  dependency; excluded to keep 5E purely on 5D facts + occupancy.
* Co-lord variants (Ketu/Mars, Rahu/Saturn) — profile default is single-lord
  classical; variants deferred, documented in 5D spec.
* Any "yoga" whose formation cannot be reduced to the accepted fact layers
  (e.g. Argala, which needs its own specification pass) — excluded rather than
  approximated.
* Numerical yoga scores — forbidden by design (formed ≠ strong).
* Natural-language interpretations / AI summaries — later phases.

## Tradition Variants & Disputes (known)

* AK–AmK Raja attribution is consensus-level but its exact boundaries
  (conjunction only vs conjunction-or-mutual-aspect) vary by commentator; 5E
  implements conjunction and mutual-drishti as SEPARATE rules so consumers
  choose explicitly.
* Benefic-in-AL / AL-lord placement effects vary across commentaries; 5E
  records formation only, quality UNASSESSED.
* Karakamsha occupant effects (which planets, which outcomes) are among the
  most variant-sensitive claims; 5E implements occupancy-only formation with
  UNVERIFIED provenance and no outcome text.
* D9-scope rules deliberately ignore D1-drishti mitigation (scope honesty).
