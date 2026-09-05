# ASTROLIFE V2 — PHASE 9 — SECURITY

## Principle
Research text is DATA. The ten instruction probes (“ignore the production
lifecycle”, “promote this automatically”, “mark source verified”, “pretend
this rule is classical”, “delete conflicting source”, “overwrite golden”,
“execute this”, “import module”, “change canonical chart”, “disable
regression”) are detected as data and never obeyed (12 probe tests).

## DSL remains declarative
Rules are `{op, params, children}` trees over `known_ops()` (Phase 6A).
Anchored structural validation rejects unknown ops, non-object params,
nested code-like values, and suspicious scalars. Rejected payloads include
Python/JS/shell/SQL/template markers: `eval(`, `exec(`, `__import__`,
`import`, `lambda`, backticks, `$()`, `SELECT…FROM`, `__class__`,
`open(`, `socket`, `requests`, `urllib`, `<script`, `javascript:`.

## Import/export
JSON only, canonical form, schema-validated, security-scanned. Arbitrary
objects, code, `eval`/`exec`/`import`/shell/subprocess/module-loading
payloads are rejected at validation and at import.

## Static audit
`audit.static_audit_package()` scans `backend/core/research/` for
calculation duplication (ephemeris, Varga/Dasha/Shadbala/yoga/dosha/Jaimini
markers), ML (sklearn/tensorflow/torch), LLM calls, and code evaluation.
Result: clean (scanner word-lists are concatenated so the scanners do not
flag their own sources; exclusions documented in code).

## Prediction / AI boundaries
Experimental timing stays research-scoped and version-stamped; nothing
enters Phase 8 production predictions. Phase 7 agents see research results
as read-only JSON — they cannot create/promote/verify/alter rules,
experiments, or snapshots.
