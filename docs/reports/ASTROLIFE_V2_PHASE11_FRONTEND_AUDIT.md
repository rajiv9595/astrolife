# ASTROLIFE V2 — PHASE 11 — FRONTEND AUDIT
(Audit performed read-only; no frontend file was modified during the audit.)

## 1. Current architecture
React 18 + Vite 5 + Tailwind 3 + react-router-dom 6 + axios + framer-motion
+ lucide-react. Plain JSX (no TypeScript). No test framework installed.
Entry: `src/main.jsx` → `src/App.jsx` (BrowserRouter + AnimatePresence).
Services in `src/services/` (api, astro, ai, auth, family). No second app.

## 2. Existing routes
`/` landing, `/auth`, `/free-kundli` (guest), `/enter-details`,
`/dashboard`, `/match`, `/services`, `/learning`, `/blog`, `/about`,
`/tools/{dasha,planets,yogas,ai-astrologer,info,horoscope,api}`.
ProtectedRoute via sessionStorage token. Preserved as-is.

## 3. Existing pages
Landing/Auth/BirthInput (thin wrapper over SignupForm)/Dashboard/Match/
Services/Learning/Dasha/Yogas/Planets/ProfileInfo/GuestKundli/Horoscope/
AIAstrologer/Blog/About. GuestKundli + Horoscope are the chart surfaces.

## 4. Existing components
Charts: NorthIndianChart, SouthIndianChart (both preserved), DashaTimeline.
Horoscope cards: MangalDosha, AdvancedDoshas, Jaimini, Ashtakavarga,
Shadbala, Maitri, Panchanga, FamilyMemberModal. UI: GlassCard, VedicCard,
VedicButton, CosmicButton, Input, LocationInput, Navbar. AI: AIAstrologer,
ExpertReportCard. DeveloperAPI.

## 5. Existing visual system
Dual theme: cosmic-black marketing pages, vedic-cream tool pages;
vedic-orange/vedic-blue accents, serif display type, GlassCard/VedicCard,
framer-motion transitions, lucide icons, responsive Tailwind layouts.
Baseline for preservation.

## 6. Existing astrology UI
D1/D9/D10 tabs, South/North toggle, planet tables (sign/degree/house/
nakshatra/star-lord), Dasha timeline, yoga/dosha/Jaimini/panchanga/
shadbala cards, AI astrologer, match page. All backend-driven.

## 7. Existing API layer
`services/api.js` (axios, `VITE_API_URL` env-first with localhost:8001 dev
fallback, Bearer interceptor) + `astroService` (computeChart→POST /compute,
geocode search/suggestions, matchCharts→POST /match, expert report),
`aiService.analyze`→POST /ai/analyze, auth/family services. Centralized;
extended, not replaced.

## 8. Existing mock/static data
No mock astrology data found. Only static UI text (locked-feature teasers,
one yoga description shown as UI copy in YogasPage, BlogPage mock flag).
`localStorage 'chartData'` caches last /compute response client-side.

## 9. Existing state management
Local useState/useEffect per page; sessionStorage token; no global store.
Static (birth/ChartFacts) vs dynamic state not yet separated — added via a
hook without refactoring pages.

## 10. Existing charts
North + South Indian SVG-style components receive backend-shaped
`chartData`; house geometry from Whole Sign order + sign_num spans is
presentational. No ephemeris/ayanamsha code anywhere (only display labels).

## 11. Reusable components
VedicCard, GlassCard, Navbar, LocationInput, DashaTimeline, both chart
styles — all reused for new integration UI.

## 12. Integration opportunities
/dynamic/state (evaluation datetime), /dynamic/panchanga, transit
endpoints, Phase 9 research (no UI yet — minimum new UI required).

## 13. Gaps
No typed contracts (JS project), no UNKNOWN/INVALID/CONFLICTED display
semantics, no research UI, no request cancellation, error→toast only,
`localStorage chartData` can go stale across users/charts, CORS `*` on
backend (pre-existing).

## 14. Must be preserved
Both chart styles, vedic-cream tool design, route map, card system,
Dasha timeline, planet tables, auth flow, vercel SPA rewrites.

## 15. Require backend integration
Research Lab (new), dynamic evaluation datetime (new card), status
semantics (adapters), error taxonomy (client).

## 16. Need minimal modification
HoroscopePage (one DynamicStateCard insertion), App.jsx (one route),
ToolsLayout (no change — research linked from Services; nav untouched).

## 17. Genuinely new functionality
`src/api/` contracts+client, `src/utils/` semantics/format/params,
`useCanonicalChart` hook, ResearchLab page, Node + Python test suites.
