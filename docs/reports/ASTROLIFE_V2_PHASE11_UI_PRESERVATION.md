# ASTROLIFE V2 — PHASE 11 — UI PRESERVATION

## Visual preservation assessment

### UNCHANGED
Routes (17/17 kept), both Indian chart styles, VedicCard/GlassCard system,
Tailwind vedic palette, Dasha timeline, planet tables, all horoscope cards,
auth flow, AnimatePresence transitions, responsive layouts, vercel SPA
rewrites, vite alias/chunking, npm scripts, dependency set (zero new deps).

### MINIMALLY CHANGED
- `App.jsx`: +2 lines (ResearchLab import + `/tools/research` route).
- `HoroscopePage.jsx`: DynamicStateCard import, dynamic-state state/effect
  (~25 lines), one card insertion — same column, same card style.
- `ServicesPage.jsx`: +2 lines (icon import, Research Lab card entry).
- `api/endpoints.js`: +2 constants (research pair).

### NECESSARILY CHANGED
- New files only: `api/{endpoints,types,canonicalClient}`, `utils/`
  (statusSemantics, canonicalFormat, chartParams), `hooks/useCanonicalChart`,
  `DynamicStateCard`, `ResearchLab`, test suites. No existing visual altered
  to accommodate them.

## Change budget
PRESERVATION: everything above unchanged. INTEGRATION: endpoint map,
client, hook, DynamicStateCard, ResearchLab, Services entry. BUG_FIX: none
required. ACCESSIBILITY: roles, scope cols, sr-only labels. PERFORMANCE:
memo/abort/keys. NEW_REQUIRED_FEATURE: research read-only UI. Zero cosmetic
redesign.

## Before/after inventory (major pages)
Landing/Auth/Dashboard/Match/Services(+1 card)/Learning/Blog/About/
Dasha/Planets/Yogas/ProfileInfo/GuestKundli/Horoscope(+1 card)/AI —
layout, spacing, typography, charts, cards, navigation identical except the
two noted insertions. Screenshots not captured (no visual tooling in env);
preservation proven by diff-small-change + full test suites + green build.
