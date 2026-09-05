# ASTROLIFE V2 — PHASE 9 — PROMOTION

## Firewall
Experimental rules live in `research://` and can never silently appear as
production-active. There is no EXPERIMENTAL→ACTIVE transition in either
state machine.

## PromotionRequest
`request_id`, `rule_id`, `rule_version`, `package_id`, `requested_by`,
`target_catalogue` (+ `target_tradition`, `target_profile`,
`target_version`), `required_validation`, `required_review`,
`source_state`, `evidence_state`, `regression_state`, `approval_state`.
Target is mandatory — no implicit production destination.

## Twelve gates (independently inspectable, never one score)
1. `schema_valid` 2. `security_valid` 3. `dependency_valid`
4. `applicability_valid` 5. `evidence_valid` 6. `fixture_valid`
7. `regression_valid` 8. `provenance_valid` 9. `tradition_valid`
10. `profile_valid` 11. `review_complete` 12. `lifecycle_valid`.

## No automatic promotion
100% fixtures + golden + positive history + multi-system agreement still
requires an explicit request plus an APPROVE review. TESTED ≠ PROMOTED
(proven by golden negative test: fixtures pass, evidence/review incomplete
→ promotion FAILS with REJECTED audit entry).

## Review
`review_id`, rule/version, reviewer metadata (human-supplied; no simulated
reviewers), status, gate results, concerns, required changes, decision
(APPROVE / REQUEST_CHANGES / REJECT), provenance.

## Audit trail
Every attempt preserves requested state, per-gate results, reviewer
decision, package/rule/evidence fingerprints, resulting state. Failed
attempts remain visible. Positive path promotes into the designated target
only, classified USER_SUPPLIED — classical authority is never inferred
(SOURCE_VERIFIED, RULE_TESTED, RULE_PROMOTED, CLASSICAL_AUTHORITY stay
independent).
