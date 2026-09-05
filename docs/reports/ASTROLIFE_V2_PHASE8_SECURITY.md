# ASTROLIFE V2 — PHASE 8 SECURITY

## 1. Inputs are DATA (§42)

`PredictionRequest` forbids unknown fields, so instruction smuggling has no
schema home. Free-text `notes` are scanned against 9 hostile directives
(ignore profile, pretend formation, positivity bias, conflict removal,
guarantee demands, dasha override, chart rewrite, developer-as-classical
elevation, missing-data blindness): matches become warnings, engine output
proven byte-identical with and without them. No code path mutates profiles,
birth data, dasha rows, conflicts, or certainty posture from input text.

## 2. Static calculation audit (§55)

29 forbidden tokens (Swiss Ephemeris, longitude/house/Varga/dasha/transit/
Shadbala/yoga/dosha/Jaimini calculators, formation evaluators,
`get_current_dasha`, calculation-package imports) scanned across all 19
implementation modules: zero violations. Only `catalogue.py` references the
approved 6E read-only API. `golden.py` + the test file construct fixtures
from canonical engines and are the documented exclusions.

## 3. Immutability (§43)

Entry-dict digests plus live canonical digests (ChartFacts, VargaFacts,
StrengthReport, JaiminiFacts, Dasha, Transit, rule results) identical before/
after evaluation; catalogue snapshots sealed equal; engine receives summaries
and rows only.

## 4. No live time (§44)

No `datetime.now`, `time.time`, `random`, `uuid4` in canonical code (scanned).
All times come from `PredictionRequest` or canonical rows; supported range
1900-01-01..2100-01-01 enforced (outside → INVALID).

## 5. No ML (§56), no LLM (§41 helper direction)

29-token ML scan (sklearn/torch/tensorflow/neural/embeddings/Bayes/fit/
predict_proba) clean; no OpenAI/Anthropic/text-generation calls. Phase 7
agents consume results downstream via `prediction_to_agent_summaries`
(read-only view, canonical fingerprint untouched).
