# ASTROLIFE V2 — PHASE 10 — DETERMINISM

## 50-run full pipeline (§40)
50 iterations of chart + all-Varga computation → ONE unique snapshot
fingerprint. Chart serialization byte-identical across rebuilds
(`model_dump_json` equality). No timestamps in fingerprints (volatile keys
`evaluated_at`, `evaluation_datetime`, … stripped before hashing).

## Concurrency (§41)
8-worker ThreadPoolExecutor over 64 Varga computations ×2 runs: identical
ordered outputs, all signs valid — no shared mutable state, no
cross-request contamination, deterministic ordering.

## Order-independence (§42)
Shuffled research fixtures → identical experiment fingerprint (canonical
serialization sorts by fixture/rule id). Yoga rule-id set stable.

## Production immutability (§46)
14 layer fingerprints (ChartFacts, VargaFacts, Dasha, Transit, Strength,
Yoga, Dosha, Jaimini, RuleRegistry, EvidenceGraph, KnowledgeCatalogue,
AgentRegistry, Prediction registry, Research registry — represented via
their canonical snapshots) identical before/after the full suite.
