# ASTROLIFE V2 — PHASE 11 — API MAP

Every endpoint below was verified against backend route sources (prefix +
decorator). No endpoint was invented. Frontend constants live in
`frontend/src/api/endpoints.js` (17 entries, frozen).

| UI feature | Backend endpoint | Response | Component | Adapter | Display |
|---|---|---|---|---|---|
| Health | GET /health | {status} | api layer | pass-through | status dot |
| Chart creation | POST /compute | ComputeResponse (planets, ascendant, houses, d9/d10/vargas, vimshottari, nakshatra, tithi/karana, yogas auth-only, strengths, jaimini, ashtakavarga, shadbala, maitri, panchanga_advanced, advanced_doshas) | HoroscopePage, GuestKundliPage, YogasPage, DashaPage | getChartDataByType, getActiveDasha, formatters | South/North charts, tables, cards |
| Match | POST /match | ashta_koota + moon signs | MatchPage | matchCharts | compatibility view |
| Dynamic state | POST /dynamic/state | dasha/panchanga/transits | DynamicStateCard | canonicalClient.dynamicState | evaluation + hierarchy |
| Panchanga | POST /dynamic/panchanga | panchanga | PanchangaCard / client | canonicalClient.panchanga | card rows |
| Transit snapshot/range | POST /dynamic/transit-snapshot, /dynamic/transit-range | snapshots | DynamicStateCard | canonicalClient | snapshot note |
| AI analyze/report | POST /ai/analyze, /ai/expert_report | text/context | AIAstrologer, ExpertReportCard | aiService/astroService | chat + report |
| Geocode | GET /geocode/search, /suggestions, /reverse | places | LocationInput, SignupForm | astroService builders | dropdown |
| Auth | POST /auth/signup, /auth/login | token | AuthPage, ProtectedRoute | authService | session |
| Family | /family/* | members | HoroscopePage selector | familyService | dropdown |
| API keys | /api-keys | keys | DeveloperAPI | api directly | key table |
| Learning | /learn/* | lessons | LearningPage | existing | lessons |
| Research golden/gates | GET /research/golden, /research/gates | package + 12 gates | ResearchLab | api.get read-only | badges + gate grid |

Missing-endpoint analysis: no required endpoint was missing. The only
backend addition is the read-only `/research/*` pair (Phase 9 had no HTTP
surface). No fake frontend data was created for any feature.
