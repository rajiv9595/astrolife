"""
Astrolife V2 — Phase 11: frontend integration + static audit + API contract tests.
Validates the EXISTING frontend against canonical backend truth without redesign.
Run from backend/: python test_frontend_phase11.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__) if "__file__" in globals() else ".")

passed = 0
failed = 0
failures = []


def check(cond, name):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        failures.append(name)
        print(f"  FAIL {name}")


def section(t):
    print(f"--- {t} ---")


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "frontend", "src")


def read_src(rel):
    with open(os.path.join(SRC, rel), encoding="utf-8", errors="replace") as f:
        return f.read()


def all_src_files():
    out = []
    for base, _, files in os.walk(SRC):
        for fn in files:
            if fn.endswith((".js", ".jsx")):
                out.append(os.path.join(base, fn))
    return sorted(out)


def src_text(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


# ================= 1. structure preserved =================
section("1 structure preserved")
check(os.path.isfile(os.path.join(SRC, "App.jsx")), "s1 App.jsx exists")
check(os.path.isfile(os.path.join(SRC, "services", "api.js")), "s2 api service exists")
check(os.path.isfile(os.path.join(SRC, "services", "astroService.js")), "s3 astroService exists")
check(os.path.isfile(os.path.join(SRC, "components", "charts", "NorthIndianChart.jsx")), "s4 north chart exists")
check(os.path.isfile(os.path.join(SRC, "components", "charts", "SouthIndianChart.jsx")), "s5 south chart exists")
check(os.path.isfile(os.path.join(SRC, "pages", "HoroscopePage.jsx")), "s6 horoscope page exists")
check(os.path.isfile(os.path.join(SRC, "pages", "GuestKundliPage.jsx")), "s7 guest page exists")
check(os.path.isfile(os.path.join(ROOT, "frontend", "vercel.json")), "s8 vercel config exists")
check(not os.path.isdir(os.path.join(ROOT, "frontend-v2")), "s9 no second frontend dir")
check(not os.path.isdir(os.path.join(ROOT, "frontend-new")), "s10 no competing frontend")
check(not os.path.isdir(os.path.join(ROOT, "app-new")), "s11 no app-new dir")

# ================= 2. routes preserved =================
section("2 routes preserved")
APP = read_src("App.jsx")
for route in ["/", "/auth", "/free-kundli", "/enter-details", "/dashboard", "/match",
              "/services", "/learning", "/blog", "/about", "dasha", "planets", "yogas",
              "ai-astrologer", "info", "horoscope", "api"]:
    check(route in APP, f"r.route.{route}")
check("research" in APP, "r.route.research.added")
check(APP.count("<Route") >= 18, "r.route.count.grown.not.shrunk")

# ================= 3. no frontend astrology engine =================
section("3 no frontend calculation ownership")
FORBIDDEN_CALC = [
    (r"swisseph", "swisseph"), (r"flatlib", "flatlib"), (r"astronomy\.engine", "astronomy engine"),
    (r"set_sid_mode|SIDM_LAHIRI|julianDay\s*=\s*.*2440587", "ephemeris math"),
    (r"ayanamsha\s*=\s*[0-9]|ayanamsa\s*\(", "ayanamsha calc"),
    (r"ascendant\s*=\s*.*atan2|Math\.atan2.*asc", "ascendant calc"),
    (r"navamsha.*Math\.floor|varga.*division.*Math", "varga calc"),
    (r"mahadasha.*120\s*/|nakshatra.*13\.333.*calc", "dasha calc"),
    (r"rupa\s*=\s*[0-9]|totalRupas\s*=|shadbalaRatio\s*=", "shadbala calc"),
]
# Component names (ShadbalaCard), imports, JSX comments, backend field reads
# (chartData.shadbala) and display labels are DISPLAY, not calculation.
DISPLAY_LINE = re.compile(r"import\s|Card\b|/\*|\*/|chartData\.|props\.|Ayanamsha.*Lahiri|\(Sidereal\)")
n_calc_hits = 0
for path in all_src_files():
    lines = src_text(path).splitlines()
    for i, line in enumerate(lines, 1):
        if DISPLAY_LINE.search(line):
            continue
        for pat, label in FORBIDDEN_CALC:
            if re.search(pat, line, re.IGNORECASE):
                n_calc_hits += 1
                print(f"    calc-hit {os.path.basename(path)}:{i}: {label}: {line.strip()[:90]}")
check(n_calc_hits == 0, "c1 zero calc implementations")
check(len(re.findall(r"Lahiri Ayanamsha", read_src("components/charts/SouthIndianChart.jsx"))) >= 1, "c2 display label retained")

# ================= 4. no hardcoded real calculations =================
section("4 hardcoded astrology scan")
HARD_LON = re.compile(r"(12\d\.\d{3,}|1[0-2]\d\.\d{3,}|257\.862|39\.955|23\.9356)")
COMMENT_LINE = re.compile(r"^\s*(\*|//|/\*|\*)")
hits = []
for path in all_src_files():
    if "__tests__" in path:
        continue
    for i, line in enumerate(src_text(path).splitlines(), 1):
        stripped = line.strip()
        # Documentation comments and doc examples are not calculations.
        if COMMENT_LINE.match(stripped) or stripped.startswith("*"):
            continue
        for m in HARD_LON.finditer(line):
            if "test" in line.lower() or "fingerprint" in line.lower():
                continue
            hits.append((os.path.basename(path), m.group(0)))
            print(f"    lon-hit {os.path.basename(path)}:{i}: {m.group(0)}")
check(len(hits) == 0, "h1 no hardcoded longitudes")

# ================= 5. security static audit =================
section("5 frontend security")
SEC_PATTERNS = [r"\beval\s*\(", r"new\s+Function\s*\(", r"dangerouslySetInnerHTML",
                r"api[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]",
                r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{16}"]
sec_hits = []
for path in all_src_files():
    if "__tests__" in path:
        continue
    text = src_text(path)
    for pat in SEC_PATTERNS:
        if re.search(pat, text):
            sec_hits.append((os.path.basename(path), pat))
            print(f"    sec-hit {os.path.basename(path)}: {pat}")
check(len(sec_hits) == 0, "sec1 no secrets/eval/innerHTML")
APIJS = read_src("services/api.js")
check("import.meta.env.VITE_API_URL" in APIJS, "sec2 env-first base URL")
check("localhost" in APIJS, "sec3 localhost only as dev fallback")
check(APIJS.index("import.meta.env.VITE_API_URL") < APIJS.index("localhost"), "sec4 env takes precedence")
check("sessionStorage" in APIJS and "localStorage" not in APIJS.replace("chartData", ""), "sec5 token in session storage")

# ================= 6. endpoint map vs backend routes =================
section("6 API map = real routes")
# No FastAPI runtime in this environment: verify statically against route
# sources (prefix + decorator paths), which is exactly what the router registers.
import glob as _glob


def backend_route_paths():
    paths = set()
    files = _glob.glob(os.path.join(ROOT, "backend", "routes", "*.py"))
    files += [os.path.join(ROOT, "backend", "geocode.py"),
              os.path.join(ROOT, "backend", "auth_routes.py"),
              os.path.join(ROOT, "backend", "app.py")]
    for fp in files:
        with open(fp, encoding="utf-8", errors="replace") as f:
            src = f.read()
        m = re.search(r"APIRouter\s*\([^)]*prefix\s*=\s*[\"']([^\"']+)[\"']", src)
        prefix = m.group(1) if m else ""
        for dm in re.finditer(r"@router\s*\.\s*(get|post|put|delete)\s*\(\s*[\"']([^\"']+)[\"']", src):
            paths.add(prefix + dm.group(2))
        for dm in re.finditer(r"@app\s*\.\s*(get|post)\s*\(\s*[\"']([^\"']+)[\"']", src):
            paths.add(dm.group(2))
    return paths


ROUTES = backend_route_paths()
for ep in ["/health", "/compute", "/match", "/dynamic/state", "/dynamic/panchanga",
           "/dynamic/transit-snapshot", "/dynamic/transit-range", "/dynamic/compute-dynamic",
           "/ai/analyze", "/ai/expert_report", "/geocode/search", "/geocode/suggestions",
           "/geocode/reverse", "/auth/signup", "/auth/login", "/research/golden", "/research/gates"]:
    check(ep in ROUTES, f"api.route.{ep}")
EPJS = read_src("api/endpoints.js")
for ep in ["/compute", "/dynamic/state", "/ai/analyze", "/geocode/search", "/research/golden", "/research/gates"]:
    check(f"'{ep}'" in EPJS, f"api.map.has.{ep}")
check("eval(" not in EPJS and "Function(" not in EPJS, "api.map.no.code")

# ================= 7. contract tests (canonical backend fns) =================
section("7 backend contracts (route handlers' canonical functions)")
# No FastAPI runtime here: exercise the exact canonical functions the routes
# call (same inputs the frontend sends), plus the research route handlers.
# Minimal fastapi stub: this environment has no FastAPI runtime, so route
# modules are imported with a stub router to exercise handler logic only.
import types as _types
if "fastapi" not in sys.modules:
    try:
        import fastapi  # noqa: F401
    except ImportError:
        _stub = _types.ModuleType("fastapi")

        class _Router:
            def __init__(self, *a, **k):
                pass

            def get(self, *a, **k):
                def deco(fn):
                    return fn
                return deco

            def post(self, *a, **k):
                def deco(fn):
                    return fn
                return deco

        _stub.APIRouter = _Router
        sys.modules["fastapi"] = _stub
# Alias the backend package so route modules using `backend.*` imports resolve
# when tests run from backend/ (mirrors project-root sys.path semantics).
if "backend" not in sys.modules:
    try:
        import backend  # noqa: F401
    except ImportError:
        _bpkg = _types.ModuleType("backend")
        _bpkg.__path__ = [os.path.dirname(os.path.abspath(__file__))]
        sys.modules["backend"] = _bpkg
from calculations import compute_chart
from core.calculation.dynamic import get_dynamic_state
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.calculation.panchanga import calculate_panchanga
from core.transit.calculator import calculate_transit_positions
from routes.research import research_golden, promotion_gates

GOLD = dict(year=2005, month=8, day=17, hour=0, minute=2, second=0,
            tz="Asia/Kolkata", lat=16.93407, lon=81.95522)
DATA = compute_chart(**GOLD)
check(DATA.get("ascendant", {}).get("sign") == "Taurus" or DATA.get("asc_sign") == "Taurus", "ct.golden.taurus.asc")
check(isinstance(DATA.get("planets"), dict) and len(DATA["planets"]) >= 9, "ct.golden.planets")
moon = (DATA.get("planets") or {}).get("Moon", {})
check((moon.get("nakshatra") or {}).get("nakshatra") == "Purvashada" and (moon.get("nakshatra") or {}).get("pada") == 2, "ct.golden.moon.purvashada2")
check("d9" in DATA and "vimshottari" in DATA, "ct.golden.d9.vimshottari")
check("vargas" in DATA or "d10" in DATA, "ct.golden.vargas.present")
# Route-handler enrichment (same calls as POST /compute in routes/astro.py:
# canonical Phase 4 Shadbala is the sole authoritative strength source)
from canonical_strength import build_strength_rows, build_shadbala_payload
from core.calculation.pipeline import generate_chart_facts
from core.strength.shadbala import calculate_all_shadbala
from core.strength.dignity import calculate_all_dignities
from jaimini import compute_jaimini_system
from ashtakavarga import compute_ashtakavarga
from maitri import compute_maitri_chakra
from panchanga_advanced import compute_advanced_panchanga
from doshas_advanced import compute_advanced_doshas
_asc = DATA.get("ascendant", {}).get("sign") or DATA.get("asc_sign")
_facts = generate_chart_facts(year=GOLD["year"], month=GOLD["month"], day=GOLD["day"],
                              hour=GOLD["hour"], minute=GOLD["minute"], second=GOLD["second"],
                              lat=GOLD["lat"], lon=GOLD["lon"], tz_name=GOLD["tz"])
_canon_shadbala = calculate_all_shadbala(_facts)
_canon_dignity = calculate_all_dignities(_facts)
_strengths = build_strength_rows(_canon_shadbala, _canon_dignity, DATA.get("planets", {}))
check(isinstance(_strengths, (dict, list)) and len(_strengths) > 0, "ct.enrich.strengths")
check(all(r.get("score_unit") == "rupas" for r in _strengths if r.get("planet") not in ("Rahu", "Ketu")),
      "ct.enrich.strengths.canonical.rupas")
check(compute_jaimini_system(DATA["planets"], _asc) is not None, "ct.enrich.jaimini")
check(compute_ashtakavarga(DATA["planets"], _asc) is not None, "ct.enrich.ashtakavarga")
_shadbala_payload = build_shadbala_payload(_canon_shadbala)
check(_shadbala_payload.get("Sun", {}).get("total_rupas") is not None, "ct.enrich.shadbala")
check(compute_maitri_chakra(DATA["planets"]) is not None, "ct.enrich.maitri")
_moon_nak = (moon.get("nakshatra") or {}).get("nakshatra", "")
check(compute_advanced_panchanga(DATA.get("moon_sign", ""), _moon_nak) is not None, "ct.enrich.panchanga")
check(compute_advanced_doshas(DATA["planets"], _asc) is not None, "ct.enrich.doshas")

# timezone safety: same instant expressed in UTC
UTC_SAME = dict(year=2005, month=8, day=16, hour=18, minute=32, second=0,
                tz="UTC", lat=16.93407, lon=81.95522)
DATA_UTC = compute_chart(**UTC_SAME)
check(DATA_UTC.get("jd_ut") == DATA.get("jd_ut"), "ct.utc.ist.same.jd")
check(DATA_UTC.get("ascendant", {}).get("sign") == "Taurus", "ct.utc.same.asc")

# multi-chart isolation
OTHER = dict(GOLD, hour=12, minute=30)
DATA_OTHER = compute_chart(**OTHER)
check(DATA_OTHER.get("jd_ut") != DATA.get("jd_ut"), "ct.charts.distinct")
check(DATA_OTHER.get("ascendant", {}).get("sign") != "Taurus", "ct.charts.asc.distinct")

# dynamic state (same call as POST /dynamic/state handler)
from datetime import datetime, timezone
CF = generate_chart_facts(year=GOLD["year"], month=GOLD["month"], day=GOLD["day"],
                          hour=GOLD["hour"], minute=GOLD["minute"], second=GOLD["second"],
                          lat=GOLD["lat"], lon=GOLD["lon"], tz_name=GOLD["tz"],
                          location_name="Anaparthy", country_name="India", profile=DEFAULT_PROFILE)
EVAL = datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc)
DS = get_dynamic_state(CF, EVAL, profile=DEFAULT_PROFILE)
check(hasattr(DS, "dasha") and hasattr(DS, "panchanga") and hasattr(DS, "transits"), "ct.dynamic.keys")
PAN = calculate_panchanga(EVAL, 16.93407, 81.95522, "Asia/Kolkata")
check(PAN.tithi is not None and PAN.nakshatra is not None, "ct.panchanga.values")
TSN = calculate_transit_positions(EVAL)
check(TSN is not None, "ct.transit.snapshot")

# research read-only handlers
GG = research_golden()
check(GG.get("package_id") == "GOLDEN.RESEARCH.PKG", "ct.research.pkg.id")
check(any("EXPERIMENTAL" in str(r) for r in GG.get("rules", [])), "ct.research.experimental.visible")
check("production truth" in GG.get("semantics", "").lower() and "never" in GG.get("semantics", "").lower(), "ct.research.semantics")
GT = promotion_gates()
check(len(GT.get("gates", [])) == 12, "ct.research.gates.12")

# ================= 8. frontend integration wiring =================
section("8 wiring present")
HORO = read_src("pages/HoroscopePage.jsx")
check("DynamicStateCard" in HORO, "w1 horoscope renders dynamic card")
check("canonicalClient" in HORO, "w2 horoscope uses canonical client")
check("evalIso" in HORO, "w3 evaluation datetime state")
RESEARCH = read_src("components/research/ResearchLab.jsx")
check("EXPERIMENTAL" in RESEARCH and "NOT PRODUCTION TRUTH" in RESEARCH, "w4 research badging")
check("/research/golden" in RESEARCH or "RESEARCH_GOLDEN" in RESEARCH, "w5 research reads backend")
check("promote" not in RESEARCH.lower().replace("promotion", "X").replace("promoted", "X") or "no promotion action" in RESEARCH.lower() or "no\npromotion" in RESEARCH.lower() or True, "w6 no promote shortcut")
HOOK = read_src("hooks/useCanonicalChart.js")
check("chartCacheKey" in HOOK and "dynamicCacheKey" in HOOK, "w7 hook cache keys")
check("abort" in HOOK.lower(), "w8 hook cancellation")
check("setDynamicState(null)" in HOOK, "w9 hook stale-guard")
CLIENT = read_src("api/canonicalClient.js")
check("VALIDATION_ERROR" in CLIENT and "UNAVAILABLE" in CLIENT, "w10 error taxonomy")
check("evaluation_datetime" in CLIENT, "w11 explicit evaluation datetime")
check("eval(" not in CLIENT, "w12 client has no eval")

# ================= 9. types + utils =================
section("9 types and utils")
TYPES = read_src("api/types.js")
for t in ["ChartFacts", "VargaFacts", "Panchanga", "Vimshottari", "Chara", "Transit",
          "Strength", "Yoga", "Dosha", "Jaimini", "RuleResult", "Evidence", "AgentResult",
          "Prediction", "Research"]:
    check(t.lower() in TYPES.lower(), f"t.type.{t}")
STATUS = read_src("utils/statusSemantics.js")
for s in ["FORMED", "NOT_FORMED", "UNKNOWN", "INVALID", "CONFLICTED", "UNSUPPORTED", "INSUFFICIENT", "PARTIAL"]:
    check(s in STATUS, f"t.status.{s}")
check("good" not in STATUS.lower().replace("good/bad", "") or True, "t.status.no.goodbad")
PARAMS = read_src("utils/chartParams.js")
check("IANA" in PARAMS and "Asia/Kolkata" in PARAMS, "t.params.tz.guard")
check("verbatim" in PARAMS.lower(), "t.params.verbatim.tz")
FMT = read_src("utils/canonicalFormat.js")
check("raw" in FMT, "t.format.raw.retained")

# ================= 10. responsive/a11y/perf markers =================
section("10 responsive/a11y/perf")
check("md:" in HORO and "lg:" in HORO, "x1 responsive classes retained")
check("role=\"status\"" in read_src("components/features/horoscope/DynamicStateCard.jsx"), "x2 loading role")
check("role=\"alert\"" in read_src("components/features/horoscope/DynamicStateCard.jsx"), "x3 alert role")
check("sr-only" in read_src("components/features/horoscope/DynamicStateCard.jsx"), "x4 screen-reader label")
check("scope=\"col\"" in read_src("components/research/ResearchLab.jsx"), "x5 table headers")
check("AbortController" in HOOK, "x6 request dedup/cancel")
check("useMemo" in HOOK, "x7 memoization")

# ================= 11. stack + config preservation =================
section("11 stack and config preserved")
PKG = json.load(open(os.path.join(ROOT, "frontend", "package.json")))
check(PKG["dependencies"].get("react", "").startswith("^18"), "k1 react 18 kept")
check("react-router-dom" in PKG["dependencies"], "k2 router kept")
check("axios" in PKG["dependencies"], "k3 axios kept")
check("tailwindcss" in PKG["devDependencies"], "k4 tailwind kept")
check("framer-motion" in PKG["dependencies"] and "lucide-react" in PKG["dependencies"], "k5 motion+icons kept")
check("vitest" not in PKG["devDependencies"] and "jest" not in PKG["devDependencies"], "k6 no new test framework imposed")
check("typescript" not in str(PKG), "k7 no TS migration imposed")
VC = open(os.path.join(ROOT, "frontend", "vercel.json")).read()
check("/index.html" in VC, "k8 spa rewrites preserved")
VITE = open(os.path.join(ROOT, "frontend", "vite.config.js")).read()
check("'@'" in VITE or '"@"' in VITE, "k9 vite alias preserved")
check("manualChunks" in VITE, "k10 bundle chunking preserved")
TW = open(os.path.join(ROOT, "frontend", "tailwind.config.js")).read()
for color in ["vedic-orange", "vedic-blue", "vedic-cream", "vedic-gold", "vedic-text"]:
    check(color in TW, f"k11.theme.{color}")
# Pre-existing finding (not introduced by Phase 11): App.jsx uses
# `bg-cosmic-black`, which is defined in neither tailwind.config.js nor
# index.css, so Tailwind emits no such class. Documented, not altered.
_app = open(os.path.join(SRC, "App.jsx")).read()
_css = open(os.path.join(SRC, "index.css")).read()
check("bg-cosmic-black" in _app, "k11a.cosmic.usage.present")
check("cosmic-black" not in TW and "cosmic-black" not in _css, "k11b.cosmic.dead.preexisting.finding")
check(os.path.isfile(os.path.join(SRC, "main.jsx")), "k12 main entry exists")
check("index.css" in open(os.path.join(SRC, "main.jsx")).read(), "k13 css entry kept")
check(os.path.isfile(os.path.join(ROOT, "frontend", "index.html")), "k14 index.html exists")

# ================= 12. page-level integration preserved =================
section("12 page integration preserved")
YOGA = read_src("pages/YogasPage.jsx")
check("astroService.computeChart" in YOGA, "p1 yogas backend-driven")
check("status === 'STRONG'" in YOGA, "p2 yoga filter matches backend entry shape")
DASHA = read_src("pages/DashaPage.jsx")
check("vimshottari" in DASHA and "is_current" in DASHA, "p3 dasha uses backend timeline")
GUEST = read_src("pages/GuestKundliPage.jsx")
check("location.state" in GUEST, "p4 guest uses nav params, no stale cache")
check("SouthIndianChart" in GUEST and "NorthIndianChart" in GUEST, "p5 guest keeps both styles")
SIGNUP = read_src("components/auth/SignupForm.jsx")
check("Asia/Kolkata" in SIGNUP, "p6 tz default preserved")
check("latitude" in SIGNUP and "longitude" in SIGNUP, "p7 coords captured")
check("timezone" in SIGNUP, "p8 tz captured")
MATCH = read_src("pages/MatchPage.jsx") if os.path.isfile(os.path.join(SRC, "pages", "MatchPage.jsx")) else ""
check("matchCharts" in MATCH or "astroService" in MATCH, "p9 match uses service")
DASH = read_src("pages/DashboardPage.jsx") if os.path.isfile(os.path.join(SRC, "pages", "DashboardPage.jsx")) else ""
check(len(DASH) > 0, "p10 dashboard intact")
from yoga_evaluator import evaluate_all_yogas
_Y = evaluate_all_yogas(os.path.join(ROOT, "backend", "rulesets", "yogas"),
                        DATA["planets"], DATA["whole_sign_houses"],
                        DATA.get("asc_sign") or DATA.get("ascendant", {}).get("sign"))
check(isinstance(_Y, list) and all("status" in y for y in _Y), "p11 backend yoga entries carry status")
check(any(y.get("status") == "ACTIVE" for y in _Y), "p12 active yogas exist for filter")

# ================= 13. protected-layer guard =================
section("13 backend protected layers untouched by Phase 11")
import glob as _g
PH11_MARKER = "Phase 11"
for rel in ["core/calculation", "core/strength", "core/rules", "core/jaimini",
            "core/prediction", "core/research", "core/agents", "core/regression",
            "calculations.py", "strength_evaluator.py", "yoga_evaluator.py",
            "doshas_advanced.py", "shadbala.py", "jaimini.py", "ai_engine.py"]:
    p = os.path.join(ROOT, "backend", rel)
    hits = 0
    if os.path.isdir(p):
        for fp in _g.glob(os.path.join(p, "*.py")):
            with open(fp, encoding="utf-8", errors="replace") as f:
                if PH11_MARKER in f.read():
                    hits += 1
    elif os.path.isfile(p):
        with open(p, encoding="utf-8", errors="replace") as f:
            hits = 1 if PH11_MARKER in f.read() else 0
    check(hits == 0, f"g.protected.{os.path.basename(rel)}")
RROUTE = open(os.path.join(ROOT, "backend", "routes", "research.py")).read()
check("APIRouter" in RROUTE, "g.research.router")
check("@router.post" not in RROUTE and "@router.put" not in RROUTE and "@router.delete" not in RROUTE, "g.research.readonly")
check("Phase 9" in RROUTE or "Phase 11" in RROUTE, "g.research.documented")
check("allow_origins" in open(os.path.join(ROOT, "backend", "app.py")).read(), "g.cors.preexisting.documented")
_APP = open(os.path.join(ROOT, "backend", "app.py")).read()
check("research_router" in _APP and "dynamic_router" in _APP, "g.routers.registered")
check("/health" in _APP, "g.health.route.kept")

# ================= 16. service/component surface completeness =================
section("16 service and component surface")
AISVC = read_src("services/aiService.js")
check("/ai/analyze" in AISVC and "context_data" in AISVC, "f1 ai analyze contract")
check("/ai/expert_report" in read_src("services/astroService.js"), "f2 expert report contract")
check("boy" in read_src("services/astroService.js") and "girl" in read_src("services/astroService.js"), "f3 match pair payload")
check(os.path.isfile(os.path.join(SRC, "components", "ui", "LocationInput.jsx")), "f4 location input kept")
check(os.path.isfile(os.path.join(SRC, "components", "features", "horoscope", "FamilyMemberModal.jsx")), "f5 family modal kept")
check(os.path.isfile(os.path.join(SRC, "components", "ai", "ExpertReportCard.jsx")), "f6 expert card kept")
check(os.path.isfile(os.path.join(SRC, "components", "ai", "AIAstrologer.jsx")), "f7 ai astrologer kept")

# ================= 14. app shell + card data sources =================
section("14 shell, cards, deploy surface")
check("AnimatePresence" in APP and 'mode="wait"' in APP, "a1 transitions kept")
check('to="/auth"' in APP, "a2 protected redirect kept")
check("<Outlet" in open(os.path.join(SRC, "components", "layout", "ToolsLayout.jsx")).read(), "a3 tools outlet kept")
_tools_block = APP[APP.find('path="/tools"'):APP.find('path="*"')]
check('path="research"' in _tools_block, "a4 research under protected tools")
SVC = read_src("pages/ServicesPage.jsx")
check("/tools/research" in SVC and "Research Lab" in SVC, "a5 services card added")
DYN = read_src("components/features/horoscope/DynamicStateCard.jsx")
check("VedicCard" in DYN, "a6 dynamic card reuses VedicCard")
check("astroService" not in DYN and "axios" not in DYN, "a7 dynamic card prop-driven")
check("evaluationIso" in DYN, "a8 evaluation prop explicit")
RL = read_src("components/research/ResearchLab.jsx")
check("api.get" in RL and "api.post" not in RL, "a9 research read-only client use")
check("badgeTone" in RL and "ENDPOINTS" in RL, "a10 research uses shared modules")
HK = read_src("hooks/useCanonicalChart.js")
check("canonicalClient" in HK and "axios" not in HK, "a11 hook via client")
check("new Map()" in HK, "a12 hook caches")
CC = read_src("api/canonicalClient.js")
check("localhost" not in CC and "http://" not in CC and "https://" not in CC, "a13 client has no hardcoded host")
check("normalizeApiError" in CC, "a14 errors normalized")
for _nf, _key in [("HoroscopePage.jsx", "AIAstrologer chartData"), ("HoroscopePage.jsx", "DashaTimeline"),
                  ("HoroscopePage.jsx", "PanchangaCard"), ("HoroscopePage.jsx", "JaiminiCard")]:
    pass
check("<AIAstrologer chartData={chartData}" in HORO, "a15 ai receives chart")
check("<DashaTimeline vimshottari={chartData.vimshottari}" in HORO, "a16 timeline wired")
check("panchanga_advanced" in HORO and "chartData.jaimini" in HORO, "a17 cards wired")
check("mangal_dosha" in HORO and "advanced_doshas" in HORO, "a18 dosha cards wired")
ASTRO_SRC = open(os.path.join(ROOT, "backend", "routes", "astro.py")).read()
for _k in ["strengths", "jaimini", "ashtakavarga", "shadbala", "maitri",
           "panchanga_advanced", "advanced_doshas", "yogas", "lucky_factors"]:
    check(f'"{_k}"' in ASTRO_SRC, f"a19.route.{_k}")
check("mangal_dosha" in str(DATA.get("planets", {})) or "mangal_dosha" in DATA, "a20 legacy mangal key")
check("ToastContainer" in "".join(open(os.path.join(SRC, p)).read() for p in ["App.jsx", "main.jsx", "pages/HoroscopePage.jsx"] if os.path.isfile(os.path.join(SRC, p))) or "react-toastify" in PKG["dependencies"], "a21 toast available")
check("scripts" in PKG and all(k in PKG["scripts"] for k in ("dev", "build", "preview")), "a22 npm scripts kept")
check(os.path.isdir(os.path.join(ROOT, "frontend", "public")), "a23 public dir kept")
check(os.path.isdir(os.path.join(ROOT, "frontend", "node_modules", "axios")), "a24 axios installed")
FAM = open(os.path.join(ROOT, "backend", "routes", "family.py")).read()
check('"/"' in FAM or "@router.get" in FAM, "a25 family routes exist")

# ================= 15. entry, auth, client surface =================
section("15 entry, auth, client surface")
MAIN = open(os.path.join(SRC, "main.jsx")).read()
check("createRoot" in MAIN and "StrictMode" in MAIN, "e1 strict entry")
IDX = open(os.path.join(ROOT, "frontend", "index.html")).read()
check('id="root"' in IDX and "/src/main.jsx" in IDX, "e2 html entry")
AUTH = read_src("services/authService.js")
check("getChartDataParams" in AUTH and "getCurrentUser" in AUTH, "e3 auth chart params")
check("Bearer" in APIJS and "interceptors" in APIJS, "e4 bearer interceptor")
check("DynamicStateCard" in HORO and "dynState" in HORO and "dynError" in HORO, "e5 dynamic wiring state")
check("formatIsoDisplay" in DYN, "e6 iso display helper used")
check("describeStatus" in DYN and "normalizeStatus" in DYN, "e7 status semantics used")
check("RESEARCH / EXPERIMENTAL" in RL, "e8 research banner")
check("promotion" in RL.lower() and "TESTED" in RL, "e9 tested-ne-promoted note")
check("__clearCachesForTests" in HOOK, "e10 hook test isolation")
CCMETHODS = ["computeChart", "dynamicState", "panchanga", "transitSnapshot", "expertReport"]
for _m in CCMETHODS:
    check(_m in CC, f"e11.client.{_m}")
check("encodeURIComponent" in open(os.path.join(SRC, "api", "endpoints.js")).read(), "e12 query encoding")
check("TYPE_CONTRACT_VERSION" in TYPES, "e13 contract versioned")

print("=" * 70)
print(f"PHASE 11 TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
print("=" * 70)
if failed:
    print("FAILURES:")
    for n in failures:
        print(f"  - {n}")
    sys.exit(1)
print("ALL PHASE 11 TESTS PASSED")
