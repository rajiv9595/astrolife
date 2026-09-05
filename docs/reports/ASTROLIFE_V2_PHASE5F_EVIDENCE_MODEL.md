# ASTROLIFE V2 — PHASE 5F: EVIDENCE MODEL

**Module:** `backend/core/jaimini/evidence.py`

## 1. Tiers

| Tier | Meaning | Examples |
| :--- | :--- | :--- |
| `DIRECT_FACT` | Canonical upstream observation | `d1:planet:Jupiter:sign = Virgo`, `d9:planet:X:sign`, `d1:lagna` |
| `DERIVED_FACT` | 5D engine derivation | `karaka:AK = Jupiter 21.84°`, `pada:A1:final = Capricorn` (with src/lord/raw/exc in label), `karakamsha:sign`, `swamsa:lagna` |
| `RULE_DERIVED` | 5E rule layer | `rule:<ID>:formation` (condition list + pass flags), `rule:<ID>:result` (formed/status/cancellation/mitigation) |

## 2. Node IDs & Edges

IDs are stable deterministic strings (`d1:planet:<P>:sign`, `karaka:<CODE>`,
`pada:<CODE>:final`, `karakamsha:sign`, `swamsa:lagna`, `d9:planet:<P>:sign`,
`rule:<ID>:formation`, `rule:<ID>:result`). Relations: `derives`,
`supports`, `feeds`, `evaluates-to`, `co-chart-fact`, `context`,
`tracked-separately` (Karakamsha↔Swamsa guard edge). Nodes/edges emitted
sorted → byte-stable serialization. Golden graph: 64 nodes / 220 edges.

## 3. Fan-out Wiring

`chara_karakas` → every `karaka:*` node; `arudha_padas` → every `pada:*`;
`upapada` → `pada:A12:final`; `karakamsha` → both Karakamsha and Swamsa nodes;
`varga_facts.D9` → every `d9:*` node; `ChartFacts.planets` → every `d1:*` node;
`rashi_drishti` → `context` edge (lookup table, no per-fact nodes by design).

## 4. Completeness Contract (`rule_validators.validate_evidence_completeness`)

FORMED ⇒ ≥1 passing formation item + deps + provenance. NOT_FORMED ⇒ ≥1
(golden: exactly the failing) evidence item + deps + provenance. UNKNOWN ⇒
missing-dependency explanation in cancellation evidence/notes. Every result ⇒
stable ID + declared spec. Golden: zero violations.
