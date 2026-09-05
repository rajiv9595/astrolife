# ASTROLIFE V2 — PHASE 6B: FACT NAMESPACE

**Module:** `core/rules/dynamic/namespace.py` (regex table + `match_namespace`).

| Root | Layer | Examples |
| :--- | :--- | :--- |
| `natal.ascendant.*` | ChartFacts | sign, degree |
| `natal.{planet}.*` | ChartFacts | sign, longitude, house, degree, nakshatra, pada, retrograde |
| `houses.{n}.*` | ChartFacts | sign, lord |
| `varga.{D1..D60}.{planet}` | VargaFacts | sign |
| `strength.{metric}.{planet}` | StrengthReport | shadbala (float rupas), dignity (mapped state), avastha, functional, vimsopaka, composite; bhava explicitly unavailable |
| `dasha.vimshottari.*` | DashaTimeline | mahadasha/antardasha lords (active at explicit datetime), active_sign |
| `dasha.jaimini.*` | JaiminiDashaResult | profile, mahadasha/active_sign (containment), period_id |
| `transit.{planet}.*` | TransitSnapshot | sign, longitude, house |
| `jaimini.karaka.*` | JaiminiFacts | AK..PiK planets |
| `jaimini.drishti` | JaiminiFacts | sign-aspect map |
| `jaimini.pada.{n}` | JaiminiFacts | final sign |
| `jaimini.karakamsha/swamsa` | JaiminiFacts | signs |
| `aspects.{planet}` | RuleContext (caller map) | Parashari aspect lists |
| `rule:{id}` | caller outcomes | FORMED/NOT_FORMED |

Types: Sign, HouseNumber (1–12 validated), Pada (1–4 validated), Planet,
Nakshatra, float, bool, string, list, map. Off-namespace ⇒ INVALID.
