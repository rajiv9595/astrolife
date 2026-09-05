# ASTROLIFE V2 — PHASE 11 — INTEGRATION

## Chart input → backend (§8–10)
SignupForm (tz/lat/lon + place search, Asia/Kolkata default) →
`buildComputeParams` (validated, tz verbatim) → POST /compute →
ChartFacts → existing UI. GuestKundli uses nav params (no stale cache);
HoroscopePage uses family/person params. No longitude/ascendant/house math
in JS.

## Subsystem wiring (all backend-driven)
D1 charts (both styles), D1/D9/D10 tabs, planet tables, Dasha timeline
(`is_current` from backend), Panchanga/Shadbala/Jaimini/Maitri/
Ashtakavarga/Dosha cards, yogas (backend `status` shape verified),
match, AI chat/report, family selector — all preserved and verified
against live canonical functions.

## New integration surfaces
DynamicStateCard (evaluation ISO + hierarchy + transit note, VedicCard
style, role=status/alert, sr-only semantics) inserted once in
HoroscopePage; ResearchLab route `/tools/research` + Services card entry
(FlaskConical icon, existing card pattern).

## States (§12–14, §52–55)
Loading spinners in existing visual language; errors show kind+message;
UNKNOWN/INVALID/CONFLICTED/UNSUPPORTED/INSUFFICIENT render amber/red/
purple/neutral tones with explanations, never as negatives or
true/false. Tradition labels shown verbatim; Chara profiles never merged
(UI surfaces the backend-selected profile only — no switcher invented).

## Research/promotion (§30–31)
Read-only; gates listed; no "Make production" control exists.

## Responsiveness/accessibility/performance (§32–34, §76)
Tailwind responsive system untouched; table scope cols, alert/status
roles, sr-only labels added; memoization + abort + cache keys; vendor
bundle ~494KB gzip ~159KB; no ephemeris in browser bundle (verified);
1MB ganesha asset is pre-existing (recommendation: compress, not changed).
