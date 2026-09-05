# ASTROLIFE V2 — PHASE 6B: CANONICAL BINDING AUDIT

**Date:** 2026-09-04
**Scope:** Pre-implementation audit for Phase 6B (canonical FactResolver + evaluation)
**Status:** Audit Complete — Ready for Implementation

---

## 1. Canonical Sources (all accepted, read-only)

| Namespace root | Source | Accessor |
| :--- | :--- | :--- |
| `natal.*` | ChartFacts (Ph1) | planets[].sign/houses/nakshatra/pada, ascendant, houses[].lord |
| `varga.*` | VargaFacts D1–D60 (Ph2) | `planets[P][Dx]` VargaPosition |
| `strength.*` | StrengthReport (Ph4) | `generate_strength_report(chart)`; dignity/shadbala/avastha/functional |
| `dasha.vimshottari.*` | Vimshottari timeline (Ph3) | `calculate_vimshottari_timeline` + `get_current_dasha(timeline, dt)` (explicit dt) |
| `dasha.jaimini.*` | Chara result (5G/5G-H) | periods ISO dates + method; containment lookup |
| `transit.*` | TransitSnapshot (`core/transit`) | `calculate_transit_positions(dt)` (explicit dt, no clock) |
| `jaimini.*` | JaiminiFacts (5D) | karakas, drishti maps, padas, karakamsha/swamsa |
| `aspects.*` | 5A RuleContext aspect queries | caller-supplied map (no recompute in 6B) |
| `rule:*` | prior DynamicRuleOutcomes | caller-supplied map |

## 2. Reuse / Extend / Protect

* Reuse: 6A schema/DSL/evaluator/validators/registry/serialization untouched;
  5A `RuleContext` accessor names for path vocabulary; 5F UNKNOWN semantics.
* Extend (new files in `core/rules/dynamic/`): `namespace.py`, `context.py`,
  `resolver.py`, `bindings.py`, `results.py`, `engine.py`.
* Protect: every accepted engine above; 6B computes nothing astronomical —
  containment/lookup over canonical outputs only. Evaluation datetimes are
  fixed test constants, never wall-clock.

## 3. Primitive Binding Plan (22/22 bound, 0 invented)

natal-sign/house, varga-sign, lordship, kendra/trikona (pure sets),
conjunction (same-sign compare), aspects (caller map), rashi_drishti
(JaiminiFacts map), karaka/pada (JaiminiFacts), dignity states (StrengthReport
mapping), dasha_active (timeline containment), transit signs (snapshot),
strength_threshold (numeric compare). No primitive needs new calculation;
any future unbindable primitive would be marked UNSUPPORTED (none required).

## 4. Risks

R1 recalculation creep → astronomy import scan test. R2 wall-clock →
fixed-datetime tests + `datetime.now` scan. R3 tradition bleed → firewall
re-check on accessed paths in audit function. R4 type confusion → typed
FactResolution + structured INVALID diagnostics.
