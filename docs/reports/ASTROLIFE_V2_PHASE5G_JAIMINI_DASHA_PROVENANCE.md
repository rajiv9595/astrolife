# ASTROLIFE V2 — PHASE 5G: DASHA PROVENANCE

**Status:** All UNVERIFIED / TRADITION_DEPENDENT. No exceptions.

## 1. Implemented Profile

`tradition = JAIMINI`, `dasha_system = JAIMINI_CHARA`,
`method = CHARA_DASHA_LAGNA_START_V1`, `source_reference = UNVERIFIED`,
`confidence = TRADITION_DEPENDENT`. No Adhyaya/Pada/sutra/verse numbers, no
quotations, no Sanskrit citations anywhere in the dasha package
(scan-tested). The profile documents its conventions explicitly (Lagna start,
nature/parity direction, inclusive lord-distance durations, own-sign-12,
equal antardashas, 365.25-day year, no birth balance) precisely so consumers
know what is profile convention versus verified text.

## 2. Known Variant Traditions (isolated, unsupported)

Paka-Lagna and Atmakaraka starts; Sthira, Narayana, Brahma, Mandooka, Karaka,
Sudasa dashas; exaltation/debilitation duration adjustments; Savana 360-day
year; alternative dual-direction rules; pratyantardasha levels. Requesting any
raises `UnsupportedDashaMethodError` naming the supported method. Nothing is
merged or silently substituted.

## 3. Separation Statements

Vimshottari (120-year nakshatra system, 365.2425-day default) untouched and
never referenced by 5G code; `dasha_system` labels keep timelines distinct.
Dasha periods are DATA; the package contains no outcome vocabulary
(scan-tested) and emits no timing claims.
