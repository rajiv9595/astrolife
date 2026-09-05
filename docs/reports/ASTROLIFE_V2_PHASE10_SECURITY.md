# ASTROLIFE V2 — PHASE 10 — SECURITY

Unified 15-item hostile corpus (`core/regression/security.py`): 10
instruction probes + eval/exec/import/SQL/script payloads. Each item is
asserted as DATA in both the Phase 6A DSL (`find_suspicious_text`) and the
Phase 9 research firewall (`is_text_attack_blocked`) — 30 checks, all
blocking, zero behavior changes.

Static audit of Phase 10 code: `backend/core/regression/` contains no
ephemeris, Varga/Dasha/transit/Shadbala/yoga/dosha/Jaimini/prediction
formulas, no ML/LLM, no eval/exec — it only CALLS canonical pipelines and
compares against frozen goldens. Golden provenance: HISTORICAL_ACCEPTED
with anchor verification recorded in `golden_data.json`; no fabricated
external references (no “matches JHora/Swiss Ephemeris/classical text”
claims; INDEPENDENTLY_CROSS_CHECKED used only where Phase reports document
it).
