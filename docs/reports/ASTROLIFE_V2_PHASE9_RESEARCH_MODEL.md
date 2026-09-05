# ASTROLIFE V2 — PHASE 9 — RESEARCH MODEL

## ResearchRulePackage
`package_id`, `package_version`, author identity (`author`, `author_email`),
`description`, `rules`, `sources`, `claims`, `evidence`, `dependencies`,
`fixtures`, `profiles`, `experiments`, `review`, `lifecycle`, `fingerprint`.
JSON-serializable, versioned, schema-validated, security-scanned. No
executable Python as rule definition — rules stay declarative.

## Rule authoring (Phase 6A DSL reused, no second language)
Identity (`rule_id`, `rule_version`, `rule_name`, `description`), `tradition`,
`category`, `formation`/`cancellation`/`mitigation`/`activation` condition
trees (`{op, params, children}` with `op ∈ known_ops()`),
`applicability`, `dependencies`, `evidence_requirements`,
`event_applicability`, `timing_applicability`, `lifecycle_status`.

## Claim separation (Phase 6D reused)
`SOURCE_CLAIM` / `IMPLEMENTATION_CLAIM` / `INTERPRETATION_CLAIM` /
`DEVELOPER_NOTE` are distinct types. A `DEVELOPER_NOTE` is never converted
into a `SOURCE_CLAIM`. Notebook observations are tagged
`RESEARCH_OBSERVATION`, never canonical facts.

## Sources
`source_id`, `title`, `author`, `edition`, `publication`, `locator`,
`quotation`, `tradition`, `verification_status`. VERIFIED obeys Phase 6D
policy: a developer calling a source classical does not make it VERIFIED.
Unverified-but-useful rules stay visibly UNVERIFIED.

## Claims
`claim_id`, `claim_type`, `statement`, `source_ids`, `evidence_ids`,
`rule_ids`, `tradition`, `verification_status`, `status`. Contested pairs
(SOURCE A: X vs SOURCE B: NOT X) yield CONTESTED with both preserved.

## Traditions
PARASHARI_CLASSICAL, JAIMINI_CLASSICAL, TRADITION_DEPENDENT, MODERN_COMMON,
WESTERN, CUSTOM_DEVELOPER, EXPERIMENTAL. EXPERIMENTAL ≠ CUSTOM_DEVELOPER.
Existing production tradition semantics untouched (research-layer
classification only).

## Profiles
Explicit strings (e.g. PARASHARI_CLASSICAL, MOVABLE_FIXED_DUAL,
ODD_EVEN_FOOTED). Results from different profiles are never merged;
method differences report METHOD_DIFFERENCE, not BUG.
