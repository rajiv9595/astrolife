# MIGRATION #10 — AI AGENTS PRODUCTION WIRING + SPECIALIST ROUTING VERIFICATION
## FINAL REPORT

**Verdict: PASS**
**NO COMMIT / NO PUSH — awaiting review.**

Golden chart: MEDAPATI BHASKARA VENKATA RAJEEV REDDY, 17/08/2005, 12:02 AM IST,
Anaparthy AP India (16.93407, 81.95522), Sidereal / Swiss Ephemeris / Lahiri /
Mean Rahu / Whole Sign / PARASHARI_CLASSICAL.

---

## 1. Executive Summary

The six Phase 7 deterministic specialist agents existed with a complete
registry, deterministic router, orchestrator, contracts, validators, and
security module — but **nothing in production imported them**: both AI routes
called only `ai_engine` + `knowledge_base` + `ai_transit_context`. Agents were
TEST ONLY.

Migration #10 closes the gap with the thinnest bridge (`backend/canonical_agents.py`,
new, zero astrology): singleton over the existing registry, deterministic
routing, `AgentContext` built from canonical `/compute` projections (+ transit
section + verbatim prediction summary), direct deterministic draft execution
(no LLM in the agent path) with strict validation, and additive `AGENT_FINDINGS`
in both AI routes' LLM context plus synthesis-firewall prompt lines. One
security hardening: 7 narrow prompt-injection patterns for the spec's attack
sentences (no astrology logic). New test file 103/103. Full regression green.
Frontend build green. Live `/ai/analyze` + `/ai/expert_report` verified with
mocked LLM (proves agents invoked and findings delivered; no API key in env).

## 2. Six-Agent Inventory

| Agent | Purpose | Production import? | Inputs | Outputs | Canonical dependencies |
|-------|---------|--------------------|--------|---------|------------------------|
| PARASHARI_AGENT | Restate Parashari yoga RuleResults + facts | Yes (via bridge, #10) | facts, vargas, rules, dasha/transit summaries | FACT/RULE_RESULT/INTERPRETATION/UNKNOWN findings | Yoga RuleResults, evidence IDs, sources |
| JAIMINI_AGENT | Restate Jaimini facts + yoga outcomes | Yes (via bridge) | jaimini, jaimini_rules, facts, vargas | same | Jaimini facts, yoga outcomes |
| STRENGTH_AGENT | Restate classical/custom strength + dignity | Yes (via bridge) | strength, dignity, facts | same | StrengthReport projections |
| YOGA_DOSHA_AGENT | Restate yoga + dosha outcomes | Yes (via bridge) | rules, doshas, jaimini_rules | same | Yoga/Dosha RuleResults |
| TIMING_AGENT | Restate precomputed timing candidates | Yes (via bridge) | dasha, transit, timing | same (UNKNOWN when absent) | Prediction candidates, dasha/transit |
| CHART_SYNTHESIS_AGENT | Synthesize validated sub-results | Yes (via bridge) | all + sub-results | synthesis findings | Sub-agent results |

Before #10: all six TEST ONLY. After #10: all six REACHABLE (5 + synthesis).
No renames, no replacements, no new agents.

## 3. Production Reachability

Proven live (not from unit tests alone):

```
/compute (golden) → build_agent_context_from_compute → run_full_production_with_synthesis
  → 5 specialists + synthesis → AGENT_FINDINGS → /ai/analyze + /ai/expert_report LLM context
```

Verified with mocked `ai_engine`: both routes return 200 and the exact prompt
payload delivered to the LLM contains `AGENT_FINDINGS` with all six agent IDs.
Live statuses on golden chart: 4× PARTIAL (optional transit/timing absent),
1× UNKNOWN (TIMING, no candidates supplied), synthesis PARTIAL — all honest.

## 4. Registry

Existing immutable `AgentRegistry` reused via singleton
`get_production_agent_registry()` (fingerprint-stable). No duplicate registry.
Unknown IDs raise `KeyError`; rejected, never dynamically loaded. Registry
validates: deterministic_mode, PREDICT/CALCULATE forbidden, non-empty
required inputs + traditions.

## 5. Deterministic Routing

Existing `route()` reused: config-based domain → agent mapping, tradition/
profile rejection, sorted output. Bridge defaults to FULL (all six, sorted);
unknown domains rejected with notes. Repeated runs identical; no randomness,
no LLM authority, no user module names, no hidden global state (registry is
frozen; builders are pure functions).

## 6. Canonical Input Firewall

`AgentContext` holds JSON string summaries only: 19 facts (Moon Sagittarius —
see §25 correction), D1/D9/D10 tables, 42 strength + 7 dignity entries,
77 yoga + 6 dosha + 12 Jaimini-yoga summaries, dasha strings, optional transit
signs, optional timing candidates, evidence IDs, sources. Missing sections
stay missing → gates yield UNKNOWN/PARTIAL (verified: transit {} and timing []
with no candidates). Facts built once by the caller and shared — never
regenerated per agent (bridge source contains no chart-facts generation).

## 7. Agent Output Contract

Existing `AgentResult`: agent_id/version, status, summary, findings
(FACT with {fact_key, value} / RULE_RESULT with full outcome /
INTERPRETATION / UNKNOWN / WARNING), facts_used, rule_results_used,
interpretations, unknowns, conflicts, evidence, dependencies, warnings,
provenance chain, input/output fingerprints. Strict validator rejects unknown
fields, invented rule/evidence/fact/source IDs, numeric confidence,
prediction content, canonical overrides. No fields invented (all pre-existing).

## 8. No-Astrology-Calculation Audit

Source scan over all six agent modules: no `swisseph`/`swe_*`, no chart/varga/
dasha/transit/shadbala/yoga/dosha/jaimini engine imports — only counting,
sorting, restating (`_shared.py` docstring states this explicitly). BLOCK
conditions not triggered. Calculation stays in canonical engines.

## 9. Rule Engine Integration

Yoga/Dosha `RuleResultSummary` (id, tradition, formation, cancellation,
mitigation, activation, evidence/source IDs) supplied from `/compute`
projections; Gaja Kesari FORMED restated with registered evidence IDs and
source records. Agents restate outcomes; `validate_model_output` rejects any
rule outcome mismatch. No independent re-evaluation (no rule-engine imports
in agents, §8).

## 10. Strength Integration

Canonical StrengthReport projections consumed: `classical.shadbala.*` rupas
strings, dignity enum labels, bhava/avastha entries, `custom.composite.*`
kept distinct. Saturn firewall verified: facts Saturn_sign=Cancer,
dignity=ENEMY (D1), varga D9 Saturn=Libra — separate keys, never merged.
No strength scores calculated or invented (validator rejects numerics).

## 11. Jaimini Integration

All anchors verified in agent context: Jupiter AK, Moon AmK, Mars BK,
Mercury MK, Saturn PK, Venus GK, Sun DK, Karakamsha Cancer, AL/UL Capricorn.
No Chara-Karaka recalculation (no jaimini engine imports in agents).

## 12. Prediction Integration

`/prediction/evaluate` candidates → `TimingCandidateSummary` (id/kind/window
verbatim) → TIMING_AGENT restates windows exactly, states no outcome. No date
calculation, no timestamp invention, no Dasha invention, no UNKNOWN→FORMED
upgrade (KEMADRUMA-type statuses pass through verbatim).

## 13. Transit Integration

Canonical transit section → `transit` sign table (Jupiter=Cancer verified);
Parashari vs Western aspects remain separate keys upstream. Agents never see
longitudes and recalculate nothing; absent transit input → honest UNKNOWN.

## 14. Evidence

Findings carry evidence IDs drawn only from registered context IDs (asserted
across all PARASHARI findings); provenance chains present on every result.
Validator rejects invented evidence. No LLM sentence becomes evidence
(structured findings are generated deterministically before any LLM sees them).

## 15. Provenance

Per-result provenance (agent_id/version, input fingerprint, evidence/source
IDs, chain) + context/request/registry fingerprints + `_source:
production_agents` on every serialized result. No classical references
fabricated (source records only from supplied provenance).

## 16. AI Synthesis Firewall

LLM may summarize/explain/compare/prioritize/communicate/contextualize over
`AGENT_FINDINGS`. May not calculate, override, invent, fabricate, promote
research, or override UNKNOWN — now explicit in `SYSTEM_PROMPT_TEMPLATE`
(added grounding lines). Deterministic facts remain authoritative (validator
rejects overrides before the LLM ever runs; agents run without any LLM).

## 17. Prompt Injection

All six §17 attack sentences verified: detected by extended patterns (≥4
hits on the combined payload) → WARNING findings, canonical outcomes
unchanged (Gaja Kesari still FORMED), interpretations identical. User question
is DATA throughout (builders never branch on it except warnings).

## 18. Research Firewall

Bridge imports no research/lab/dynamic modules (asserted); no EXPERIMENTAL
strings in any agent output; production AI receives production canonical
summaries only. No user→AI→experimental path exists (no agent-execution
endpoint; agents run server-side over fixed inputs).

## 19. Calculation Profile Firewall

Context profile is informational (`DEFAULT`); router profile "" constrains
nothing; JAIMINI_AGENT rejects bogus profiles (verified). No Tropical/
Western/True-Node/Placidus values anywhere; natural-language prompts cannot
reach calculation code (no channel exists).

## 20. Agent Composition

Deterministic sorted order, one shared context, no duplicate calculations
(pure restatement), no contradictory authority (contracts scope reads;
conflicts propagate as CONFLICTED), evidence/provenance preserved, synthesis
receives all validated sub-results. Disagreements resolve to canonical source
+ REPORT_ONLY conflict semantics, never LLM choice of fact.

## 21. Error Handling

Simulated builder exception → per-agent INVALID with warning; sibling results
intact; canonical facts untouched; no fabricated replacement (invalid results
carry no findings). Missing facts → UNKNOWN; malformed output → INVALID via
strict validator. Catalogue-mutation seal retained in orchestrator path.

## 22. Authentication / Authorization

No new endpoints created (no `/agents/*` route — asserted). Existing
`get_current_user_optional` posture unchanged on both AI routes. No registry,
class loading, or rule execution exposed to callers.

## 23. API Verification

`POST /ai/analyze` and `POST /ai/expert_report`: existing response fields
unchanged (`{response}`, `{report}`); `AGENT_FINDINGS`/`AGENT_STATUS` are
LLM-context-internal additions (additive, frontend-compatible). Both verified
live with mocked LLM.

## 24. Frontend Verification

No redesign, no agent-selection UI, no frontend astrology logic (services pass
query + chart context + birth params; backend computes). Existing AI screens
compatible (payload shapes unchanged). Backend Phase 11 suite green; `vite
build` green (13.5 s).

## 25. Golden Chart Verification

Correction recorded: golden Moon sign is **Sagittarius** (257.862789°;
Purvashada Pada 2 falls in Sagittarius) — two initial test expectations
wrongly said Scorpio and were fixed; canonical calculations were never wrong.
Dasha (Venus ≈13.2058y; Moon/Rahu/Jupiter/Rahu/Moon), Jaimini anchors (§11),
Shadbala (Jupiter 6.81, Saturn 4.52) all retained verbatim from `/compute`
into agent context. No calculation modified.

## 26. Determinism

Repeated full runs byte-identical (JSON-sorted); routing identical; same
agents/order/inputs/findings. LLM prose nondeterminism correctly isolated
outside the deterministic boundary (fingerprints cover structured outputs only).

## 27. Concurrency

4-thread burst byte-identical; frozen registry/context models (no shared
mutable state); per-request contexts → no cross-user/request leakage; no
registry mutation (fingerprint constant).

## 28. Security

Arbitrary agent IDs (`../../../etc/passwd`, `os.system`) rejected with zero
execution; no eval/exec/`__import__`/subprocess/importlib/`os.system` in
bridge (word-boundary scan); 200k-char question inert; research/experimental
excluded; hostile notes warned; agent contracts forbid CALCULATE/PREDICT.

## 29. Performance

Context build ≈ 0.00 s, routing ≈ 0.000 s, full 6-agent execution ≈ 0.07 s
(shared context built once — Good pattern, §30). Note: serialized findings
≈ 400 KB (full restatements); acceptable for Gemini-class windows but flagged
for future context-budget review (§34).

## 30. Legacy AI Path Audit

| Caller | Classification |
|--------|----------------|
| `ai_routes` → `ai_engine` + canonical contexts + `AGENT_FINDINGS` | CANONICAL PRIMARY |
| `canonical_agents` → Phase 7 registry/router/builders | CANONICAL PRIMARY |
| `knowledge_base` (static text lookup) | CANONICAL PRIMARY (unchanged) |
| `DeterministicMockAdapter` + fixtures | TEST ONLY |
| Legacy calc modules on disk | retained, unimported by bridge/agents |

No legacy astrology overwrites canonical facts. Nothing deleted.

## 31. Tests

New `backend/test_ai_agents_production_10.py`: **103/103 pass** covering all
27 §32 items (inventory, registry, reachability, routing, firewall, no-calc
scan, rules/evidence/provenance, strength incl. Saturn D1/D9, Jaimini anchors,
prediction, transit, synthesis firewall, injection, research/profile firewalls,
composition, errors, auth, API compat incl. live mocked-LLM routes, goldens,
determinism, concurrency, security, performance, legacy isolation).

## 32. Full Regression Results

| Suite | Result |
|-------|--------|
| Migration #10 (new) | 103/103 |
| Phase 7 agents | 176/176 (unchanged — patterns additive) |
| Migrations #8 / #9 | 105/105, 74/74 |
| Phase 8 / 10 / 12 | 211 / all-pass / all-pass |
| Migrations #4/#5/#6/#7 | 91 / 149 / 87 / 39 |
| Phase 5A/5B/5C, 6A–6E | pass (185/695/✓, 48/51/115/86/105) |
| #3B/#3C, Ph 9/11, 5D–5GH, 4B, Ph 3 family, goldens, hotfixes | all pass |
| `test_timing_engine.py` | NOT RUN — pre-existing env gap (needs `pytest`) |
| `vite build` | PASS |

## 33. Files Changed

- NEW `backend/canonical_agents.py` — production agent bridge. Wiring only
  (registry/routing/summarization/orchestration); astrology formulas changed: none;
  canonical source-of-truth changed: none (reads canonical projections).
- NEW `backend/test_ai_agents_production_10.py` — tests only.
- NEW `MIGRATION_10_AI_AGENTS_PRODUCTION_FINAL_REPORT.md` — docs only.
- `backend/routes/ai_routes.py` (pre-existing mods retained): + `_attach_agent_section`
  helper, 2 call sites, 3 synthesis-firewall prompt lines. Wiring + prompt text;
  astrology formulas: none.
- `backend/core/agents/agent_security.py`: +7 narrow injection regexes.
  Security detection only; agent/detection semantics otherwise unchanged
  (Phase 7 suite still 176/176); astrology formulas: none.
- Deleted: none. Unrelated changes: none (pre-existing tree untouched).

## 34. Remaining Limitations

1. `AGENT_FINDINGS` ≈ 400 KB per AI request — full-fidelity restatements;
   future work may budget context, but truncation needs care (§20).
2. TIMING_AGENT is UNKNOWN without a supplied prediction summary (honest;
   plain `/compute` carries no candidates).
3. Live-LLM wording not asserted (no API key); guarantees are structural +
   prompt level.
4. Route auth posture unchanged (optional-user, parity with existing AI routes).
5. `test_timing_engine.py` unrunnable here (missing `pytest`, pre-existing).

## 35. Final PASS/BLOCKED Verdict

**PASS** — all §38 criteria met: six agents audited; reachability established
(live, all six); registry/routing verified; input firewall verified; no
astrology calculation in agents; RuleResult/evidence/provenance retained;
strength/Jaimini/prediction/transit integrations verified; synthesis firewall
+ prompt-injection protection verified (incl. new patterns); research/profile
firewalls verified; composition + error isolation verified; auth unchanged, no
bypass; API compatible; golden live routes verified; determinism + concurrency
verified; security + performance verified; legacy paths audited; frontend
tests/build pass; full regression green; no formulas modified; no new
astrology; Ashtakavarga and Category-E untouched; no redesign; no commit; no push.

**NO COMMIT / NO PUSH — awaiting review.**
