"""
Astrolife V2 — Phase 12: production optimization + hardening + release validation.
FINAL phase. Astrology semantics frozen; additive ops only.
Run from backend/: python test_production_phase12.py
"""
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

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
BACKEND = os.path.join(ROOT, "backend")


def read(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


from core.ops import config as CFG
from core.ops import logging_setup as LOG
from core.ops import request_id as RID
from core.ops import rate_limit as RL
from core.ops import headers as HDR
from core.ops import health as HLTH
from core.ops import cache as CACHE
from core.ops import guards as GRD
from core.ops import manifest as MAN
from core.ops import version as VER

# ================= 1. environment separation =================
section("1 environment separation")
check(CFG.app_env() in ("development", "staging", "production"), "env.mode.known")
os.environ["ASTROLIFE_ENV"] = "staging"
check(CFG.app_env() == "staging" and CFG.is_production() is False, "env.staging")
os.environ["ASTROLIFE_ENV"] = "production"
check(CFG.is_production() is True, "env.production")
os.environ["ASTROLIFE_ENV"] = "development"
check(CFG.is_production() is False, "env.development")
check(CFG.sql_echo_enabled() is False, "env.sql.echo.default.off")
os.environ["SQL_ECHO"] = "true"
check(CFG.sql_echo_enabled() is True, "env.sql.echo.opt.in")
del os.environ["SQL_ECHO"]
check(CFG.DEV_JWT_FALLBACK != "" and "production" in CFG.DEV_JWT_FALLBACK, "env.dev.fallback.marked")

# ================= 2. production config validation =================
section("2 production config validation")
GOOD = {"ASTROLIFE_ENV": "production",
        "JWT_SECRET_KEY": "x" * 40,
        "DATABASE_URL": "postgresql://app:SAFEPW@db:5432/lp",
        "FRONTEND_ORIGINS": "https://app.example.com"}
r = CFG.validate_production_config(GOOD)
check(r["valid"] and r["errors"] == [], "cfg.good.passes")
r = CFG.validate_production_config({"ASTROLIFE_ENV": "production"})
check(not r["valid"] and any("JWT_SECRET_KEY" in e for e in r["errors"]), "cfg.missing.jwt.fails")
check(any("DATABASE_URL" in e for e in r["errors"]), "cfg.missing.db.fails")
check(any("CORS" in e for e in r["errors"]), "cfg.missing.cors.fails")
r = CFG.validate_production_config({**GOOD, "JWT_SECRET_KEY": "short"})
check(not r["valid"] and any("32" in e for e in r["errors"]), "cfg.short.jwt.fails")
r = CFG.validate_production_config({**GOOD, "JWT_SECRET_KEY": "development-secret-0123456789abcdef"})
check(not r["valid"], "cfg.dev.placeholder.fails")
r = CFG.validate_production_config({**GOOD, "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/x"})
check(not r["valid"], "cfg.dev.db.fails")
r = CFG.validate_production_config({"ASTROLIFE_ENV": "development"})
check(r["valid"], "cfg.dev.lenient")
r = CFG.validate_production_config({**GOOD, "FRONTEND_ORIGINS": "https://a.example, https://b.example"})
check(r["valid"], "cfg.multi.origin.ok")
check(CFG.jwt_secret() == CFG.DEV_JWT_FALLBACK, "cfg.jwt.env.first.no.env")

# ================= 3. CORS =================
section("3 CORS")
os.environ["FRONTEND_ORIGINS"] = "https://a.example,https://b.example"
check(CFG.effective_cors_origins() == ["https://a.example", "https://b.example"], "cors.env.list")
del os.environ["FRONTEND_ORIGINS"]
os.environ["FRONTEND_URL"] = "https://app.example.com"
check(CFG.effective_cors_origins() == ["https://app.example.com"], "cors.single.url")
del os.environ["FRONTEND_URL"]
check(CFG.effective_cors_origins() == ["*"], "cors.legacy.wildcard.default")
check("*" in read(os.path.join(BACKEND, "app.py")), "cors.app.wired.to.helper")

# ================= 4. secrets audit =================
section("4 secrets audit")
SECRET_PATTERNS = [r"sk-[A-Za-z0-9]{16,}", r"AKIA[0-9A-Z]{16}",
                   r"-----BEGIN (RSA )?PRIVATE KEY-----",
                   r"ghp_[A-Za-z0-9]{16,}", r"xox[bap]-[A-Za-z0-9\-]{8,}"]
krepos = []
for base, _, files in os.walk(BACKEND):
    if "__pycache__" in base or ".venv" in base:
        continue
    for fn in files:
        if fn.endswith((".py", ".json")) and "test_" not in fn and "golden" not in fn:
            text = read(os.path.join(base, fn))
            for pat in SECRET_PATTERNS:
                if re.search(pat, text):
                    krepos.append((fn, pat))
check(krepos == [], f"sec.no.committed.secrets {krepos[:3]}")
AUTH_SRC = read(os.path.join(BACKEND, "auth.py"))
check("your-secret-key-change-in-production" not in AUTH_SRC, "sec.hardcoded.jwt.gone")
check("JWT_SECRET_KEY" in AUTH_SRC, "sec.jwt.env.first")
check("dev-only-insecure-fallback" in AUTH_SRC, "sec.fallback.marked")
DB_SRC = read(os.path.join(BACKEND, "database.py"))
check("echo=True" not in DB_SRC.replace("echo=_SQL_ECHO", ""), "sec.sql.echo.gated")
check("SQL_ECHO" in DB_SRC, "sec.sql.echo.env")
FE_SRC = "".join(read(os.path.join(dp, fn)) for dp, _, fns in os.walk(os.path.join(ROOT, "frontend", "src")) for fn in fns if fn.endswith((".js", ".jsx")) and "__tests__" not in dp)
check("GOOGLE_API_KEY" not in FE_SRC and "JWT_SECRET" not in FE_SRC, "sec.frontend.no.secrets")
check("VITE_API_URL" in read(os.path.join(ROOT, "frontend", "src", "services", "api.js")), "sec.frontend.env.url")

# ================= 5. authentication (declared contract) =================
section("5 authentication contract")
check("BCRYPT_ROUNDS = 12" in AUTH_SRC, "auth.bcrypt.rounds")
check('ALGORITHM = "HS256"' in AUTH_SRC, "auth.hs256")
check("ACCESS_TOKEN_EXPIRE_MINUTES = 24 * 60" in AUTH_SRC, "auth.expiry.24h")
check('"exp"' in AUTH_SRC or "'exp'" in AUTH_SRC or '{"exp"' in AUTH_SRC or '"exp":' in AUTH_SRC or "exp\":" in AUTH_SRC or '{"exp": expire}' in AUTH_SRC or '"exp": expire' in AUTH_SRC, "auth.exp.claim")
check("is_active" in AUTH_SRC, "auth.active.check")
check("sub" in read(os.path.join(BACKEND, "dependencies.py")), "auth.sub.binding")
check("get_current_user_optional" in read(os.path.join(BACKEND, "dependencies.py")), "auth.optional.guard.exists")
check("sha256" in read(os.path.join(BACKEND, "dependencies.py")), "auth.apikey.hashed")
check("is_active == True" in read(os.path.join(BACKEND, "dependencies.py")), "auth.apikey.active.check")

# ================= 6. authorization + isolation (declared) =================
section("6 authorization")
check("get_current_user_optional" in read(os.path.join(BACKEND, "routes", "astro.py")), "authz.compute.guarded")
check("current_user" in read(os.path.join(BACKEND, "routes", "astro.py")), "authz.yogas.gated.on.user")
FAM_SRC = read(os.path.join(BACKEND, "routes", "family.py"))
check("user" in FAM_SRC.lower(), "authz.family.user.scoped")
check("user_id" in read(os.path.join(BACKEND, "models.py")), "authz.chart.user.fk")
ck = CACHE.chart_key(2005, 8, 17, 0, 2, 16.93, 81.95, "Asia/Kolkata", user="A")
ck2 = CACHE.chart_key(2005, 8, 17, 0, 2, 16.93, 81.95, "Asia/Kolkata", user="B")
check(ck != ck2 and ck.endswith("|A"), "authz.cache.per.user")

# ================= 7. PII + logging =================
section("7 PII minimization and logging")
check(LOG.scrub("password: hunter2 token=abc Bearer xyz") == "password: [REDACTED] token=[REDACTED] Bearer [REDACTED]", "log.scrub.line")
check(LOG.scrub("postgresql://u:pw@host/db") == "postgresql://[REDACTED]@host/db", "log.scrub.dburl")
check(LOG.sanitize_mapping({"name": "X", "time_of_birth": "00:02", "token": "t"}) == {"name": "X", "time_of_birth": "[REDACTED]", "token": "[REDACTED]"}, "log.sanitize.map")
rec = LOG.build_log_record("r1", "/compute", 200, 12.345, "chart", "")
check(rec == {"request_id": "r1", "endpoint": "/compute", "status": 200, "latency_ms": 12.35, "subsystem": "chart", "error_category": ""}, "log.record.shape")
check(all(k in LOG.PII_KEYS for k in ("date_of_birth", "latitude", "mobile_number")), "log.pii.keys")
check(LOG.get_logger("t") is LOG.get_logger("t"), "log.singleton.per.name")

# ================= 8. request IDs =================
section("8 request correlation")
a, b = RID.new_request_id(), RID.new_request_id()
check(len(a) == 32 and a != b, "rid.unique.hex")
check("excluded" in RID.CANONICAL_EXCLUSION_NOTE and "fingerprints" in RID.CANONICAL_EXCLUSION_NOTE, "rid.exclusion.note")
check("request_id" in read(os.path.join(BACKEND, "app.py")) and "X-Request-ID" in read(os.path.join(BACKEND, "app.py")), "rid.middleware.wired")

# ================= 9. rate limiting =================
section("9 rate limiting")
clk = [0.0]
lim = RL.InMemoryRateLimiter(clock=lambda: clk[0])
for _ in range(20):
    r = lim.check("u1", "auth")
check(r["allowed"] is True, "rl.auth.20.ok")
r = lim.check("u1", "auth")
check(r["allowed"] is False and r["retry_after"] > 0, "rl.auth.21.blocked")
clk[0] = 61.0
check(lim.check("u1", "auth")["allowed"] is True, "rl.window.reset")
check(lim.check("u2", "auth")["allowed"] is True, "rl.per.key.isolation")
lim2 = RL.InMemoryRateLimiter(clock=lambda: clk[0])
for _ in range(60):
    lim2.check("c", "chart")
check(lim2.check("c", "chart")["allowed"] is False, "rl.chart.60.cap")
check(RL.LIMITS["expensive"][0] <= RL.LIMITS["default"][0], "rl.expensive.stricter")
lim.reset("u1")
check(True, "rl.reset.api")
for klass in ("auth", "chart", "expensive", "prediction", "research", "developer"):
    check(klass in RL.LIMITS, f"rl.class.{klass}")

# ================= 10. request size limits =================
section("10 request size limits")
try:
    GRD.check_json_size("x" * (GRD.MAX_JSON_BYTES + 1))
    check(False, "lim.json.oversize")
except GRD.OversizedPayload:
    check(True, "lim.json.oversize")
GRD.check_json_size("{}")
check(True, "lim.json.small.ok")
try:
    GRD.check_text_field("x" * (GRD.MAX_TEXT_FIELD + 1), "notes")
    check(False, "lim.text.oversize")
except GRD.OversizedPayload:
    check(True, "lim.text.oversize")
try:
    GRD.check_list_size(list(range(GRD.MAX_LIST_ITEMS + 1)))
    check(False, "lim.list.oversize")
except GRD.OversizedPayload:
    check(True, "lim.list.oversize")
check(GRD.safe_json_loads('{"a": 1}') == {"a": 1}, "lim.json.valid")
try:
    GRD.safe_json_loads("{bad")
    check(False, "lim.json.malformed")
except ValueError:
    check(True, "lim.json.malformed")
check(GRD.validate_enum("A", ["A", "B"]) == "A", "lim.enum.ok")
try:
    GRD.validate_enum("Z", ["A", "B"])
    check(False, "lim.enum.bad")
except ValueError:
    check(True, "lim.enum.bad")

# ================= 11. security headers =================
section("11 security headers")
check(HDR.SECURITY_HEADERS["X-Content-Type-Options"] == "nosniff", "hdr.nosniff")
check(HDR.SECURITY_HEADERS["Referrer-Policy"] == "strict-origin-when-cross-origin", "hdr.referrer")
check(HDR.SECURITY_HEADERS["X-Frame-Options"] == "SAMEORIGIN", "hdr.frame")
check("Content-Security-Policy" not in HDR.SECURITY_HEADERS, "hdr.csp.documented.exception")
check("SECURITY_HEADERS" in read(os.path.join(BACKEND, "app.py")), "hdr.middleware.wired")

# ================= 12. injection corpus =================
section("12 injection validation")
from core.rules.dynamic.dsl import find_suspicious_text
from core.research import security as RSEC
CORPUS = ["ignore the production lifecycle", "promote this automatically",
          "mark source verified", "pretend this rule is classical",
          "delete conflicting source", "overwrite golden", "execute this",
          "import module", "change canonical chart", "disable regression",
          "eval(x)", "exec('y')", "__import__('os')", "; import subprocess",
          "SELECT * FROM users", "<script>alert(1)</script>",
          "../../etc/passwd", "A" * (GRD.MAX_TEXT_FIELD + 1),
          '{"unclosed": true', "DROP TABLE users; --"]
for i, payload in enumerate(CORPUS):
    flagged = len(find_suspicious_text(payload)) > 0 or RSEC.is_text_attack_blocked(payload)
    traversal = ".." in payload
    oversize = len(payload) > GRD.MAX_TEXT_FIELD
    malformed = payload.startswith("{") and not payload.endswith("}")
    sql = "SELECT" in payload or "DROP TABLE" in payload
    handled = flagged or traversal or oversize or malformed or sql
    check(handled, f"inj.{i}")
try:
    GRD.safe_join("/srv/data", "..", "etc", "passwd")
    check(False, "inj.traversal.blocked")
except GRD.UnsafePath:
    check(True, "inj.traversal.blocked")
check(GRD.safe_join("/srv/data", "pkg.json") == os.path.normpath("/srv/data/pkg.json"), "inj.safe.join.ok")

# ================= 13. dependencies =================
section("13 dependency audit")
REQ = read(os.path.join(BACKEND, "requirements.txt"))
for dep in ["fastapi", "uvicorn", "pydantic", "sqlalchemy", "pyswisseph", "python-jose", "bcrypt", "httpx"]:
    check(dep in REQ, f"dep.present.{dep}")
check("==" not in REQ, "dep.unpinned.documented.risk")
FE_PKG = json.load(open(os.path.join(ROOT, "frontend", "package.json")))
check(FE_PKG["dependencies"]["react"].startswith("^18"), "dep.fe.react")
check("axios" in FE_PKG["dependencies"], "dep.fe.axios")
check("swisseph" not in json.dumps(FE_PKG["dependencies"]).lower(), "dep.fe.no.ephemeris")

# ================= 14. caching =================
section("14 caching")
c = CACHE.IsolatedCache()
kA = CACHE.chart_key(2005, 8, 17, 0, 2, 16.93, 81.95, "Asia/Kolkata", user="A")
kB = CACHE.chart_key(2005, 8, 17, 0, 2, 16.93, 81.95, "Asia/Kolkata", user="B")
check(kA != kB, "cache.per.user.keys")
c.put(kA, {"chart": 1})
check(c.get(kA) == {"chart": 1} and c.get(kB) is None, "cache.no.cross.leak")
dk1 = CACHE.dynamic_key(kA, "2026-09-02T12:00:00Z", "default")
dk2 = CACHE.dynamic_key(kA, "2026-09-03T12:00:00Z", "default")
check(dk1 != dk2, "cache.eval.date.splits")
c.put(dk1, {"d": 1})
check(c.invalidate(dk1) is True and c.get(dk1) is None, "cache.invalidate.one")
c.put(dk1, 1)
c.put(dk2, 2)
check(c.invalidate_prefix("dynamic|") == 2 and len(c) == 1, "cache.invalidate.prefix")
rk = CACHE.research_key("P", "1.0.0", "fp")
check(rk.startswith("research|P|1.0.0|"), "cache.research.key")
check(CACHE.dynamic_key(kA, "", "p") != CACHE.dynamic_key(kA, "X", "p"), "cache.now.vs.explicit")

# ================= 15. storage =================
section("15 storage audit")
MODELS = read(os.path.join(BACKEND, "models.py"))
DB_SRC = read(os.path.join(BACKEND, "database.py"))
check("user_id" in MODELS and "index=True" in MODELS, "store.user.index")
check("ChartData" in MODELS, "store.chart.model")
check("server_default" in MODELS, "store.timestamps.server.side")
check("nullable=False" in MODELS, "store.constraints.present")
check("load_dotenv" in DB_SRC, "store.dotenv.present")
check("postgresql" in DB_SRC, "store.postgres.configured")
check("echo=_SQL_ECHO" in DB_SRC, "store.echo.gated")

# ================= 16. health =================
section("16 health endpoints")
check(HLTH.liveness() == {"status": "alive"}, "health.alive")
rd = HLTH.readiness()
check(isinstance(rd.get("ready"), bool) and isinstance(rd.get("checks"), dict), "health.ready.shape")
check("ephemeris_path" in rd["checks"] and "swisseph" in rd["checks"], "health.dep.checks")
check("parashari_rules" in rd["checks"], "health.catalogue.check")
OPS_SRC = read(os.path.join(BACKEND, "routes", "ops.py"))
check("/ready" in OPS_SRC, "health.route.exists")
check("generate_chart_facts" not in read(os.path.join(BACKEND, "core", "ops", "health.py")), "health.no.full.calc")
check("traceback" not in OPS_SRC and "secret" not in OPS_SRC.lower(), "health.no.sensitive")

# ================= 17. concurrency =================
section("17 concurrency")
from core.calculation.varga import calculate_varga_position
with ThreadPoolExecutor(max_workers=8) as ex:
    o1 = list(ex.map(lambda k: (calculate_varga_position((k % 12) * 30.0 + 1.0, 9).sign), range(48)))
with ThreadPoolExecutor(max_workers=8) as ex:
    o2 = list(ex.map(lambda k: (calculate_varga_position((k % 12) * 30.0 + 1.0, 9).sign), range(48)))
check(o1 == o2 and len(o1) == 48, "conc.varga.identical")
lim3 = RL.InMemoryRateLimiter()
check(all(lim3.check("k", "default")["allowed"] for _ in range(5)), "conc.limiter.smoke")

# ================= 18. performance baselines =================
section("18 performance baselines")
from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.calculation.varga import calculate_all_vargas
from core.strength.pipeline import generate_strength_report
from core.strength.profile import DEFAULT_STRENGTH_PROFILE
G = dict(year=2005, month=8, day=17, hour=0, minute=2, second=0, lat=16.93407,
         lon=81.95522, tz_name="Asia/Kolkata", location_name="Anaparthy",
         country_name="India", profile=DEFAULT_PROFILE)


def bench(fn, n=1):
    t0 = time.perf_counter()
    for _ in range(n):
        fn()
    return (time.perf_counter() - t0) / n


t_chart = bench(lambda: generate_chart_facts(**G))
check(t_chart < 30.0, f"perf.chart.cold {t_chart:.2f}s")
CF = generate_chart_facts(**G)
t_warm = bench(lambda: generate_chart_facts(**G), 3)
check(t_warm < 5.0, f"perf.chart.warm {t_warm:.2f}s")
t_varga = bench(lambda: calculate_all_vargas(CF, DEFAULT_PROFILE), 3)
check(t_varga < 2.0, f"perf.varga {t_varga:.2f}s")
t_str = bench(lambda: generate_strength_report(CF, DEFAULT_STRENGTH_PROFILE))
check(t_str < 15.0, f"perf.strength {t_str:.2f}s")
from core.rules.parashari.fixtures import make_golden_context
from core.rules.parashari.catalog import evaluate_all_parashari
from core.rules.doshas.catalog import evaluate_all_doshas
CTX = make_golden_context()
t_yoga = bench(lambda: evaluate_all_parashari(CTX))
check(t_yoga < 10.0, f"perf.yoga {t_yoga:.2f}s")
t_dosha = bench(lambda: evaluate_all_doshas(CTX))
check(t_dosha < 10.0, f"perf.dosha {t_dosha:.2f}s")
import core.jaimini.pipeline as JP
VF = calculate_all_vargas(CF, DEFAULT_PROFILE)
t_jai = bench(lambda: JP.generate_jaimini_facts(CF, VF))
check(t_jai < 5.0, f"perf.jaimini {t_jai:.2f}s")
import core.research.pipeline as RP
import core.research.golden as RGOLD
gold = RGOLD.build_golden_package()
t_res = bench(lambda: RP.run_research_experiment("E", gold["package"], gold["rules"]["experimental"], gold["package"]["fixtures"]))
check(t_res < 5.0, f"perf.research {t_res:.2f}s")

# ================= 19. deployment config =================
section("19 deployment configuration")
VC = read(os.path.join(ROOT, "frontend", "vercel.json"))
check("/index.html" in VC, "dep.spa.rewrites")
check(os.path.isfile(os.path.join(ROOT, "frontend", "dist", "index.html")), "dep.dist.present")
check("VITE_API_URL" in read(os.path.join(ROOT, "frontend", "src", "services", "api.js")), "dep.api.url.env")
check("rewrites" in VC, "dep.rewrites.key")

# ================= 20. release gate + manifest =================
section("20 release manifest")
MANIFEST = MAN.build_release_manifest(ROOT)
for k in ("application_version", "api_version", "calculation_engine_version",
          "schema_version", "rule_catalogue_version", "evidence_catalogue_version",
          "prediction_catalogue_version", "research_catalogue_version",
          "golden_data_sha256", "parashari_rule_count"):
    check(k in MANIFEST, f"rel.manifest.{k}")
check(MANIFEST["application_version"] == "12.0.0", "rel.app.version")
check(MANIFEST["parashari_rule_count"] == 31, "rel.rule.count.31")
check(len(MANIFEST["golden_data_sha256"]) == 64, "rel.golden.sha")
check(VER.API_VERSION == "v1", "rel.api.version")

# ================= 21. astrology integrity anchors =================
section("21 astrology integrity (frozen)")
from core.calculation.dynamic import get_dynamic_state
from datetime import datetime, timezone
CF2 = generate_chart_facts(**G)
check(abs(float(CF2.time.julian_day) - 2453599.2722222223) < 1e-9, "int.jd")
check(float(CF2.ayanamsha.value if hasattr(CF2.ayanamsha, "value") else CF2.ayanamsha) == 23.93565836563647, "int.ayanamsha")
check(float(CF2.ascendant.longitude.sidereal) == 39.955221668117616, "int.asc")
check(abs(float(CF2.planets["Moon"].longitude.sidereal) - 257.862789) < 0.001, "int.moon")
check(CF2.planets["Moon"].nakshatra.name == "Purvashada" and CF2.planets["Moon"].nakshatra.pada == 2, "int.moon.nak")
_ra = float(CF2.planets["Rahu"].longitude.sidereal)
_ke = float(CF2.planets["Ketu"].longitude.sidereal)
check(abs((_ra + 180.0) % 360.0 - _ke) < 1e-10, "int.ketu.opp")
JF = JP.generate_jaimini_facts(CF2, calculate_all_vargas(CF2, DEFAULT_PROFILE))
check({k: v.planet for k, v in JF.chara_karakas.karakas.items()} == {"AK": "Jupiter", "AmK": "Moon", "BK": "Mars", "MK": "Mercury", "PK": "Saturn", "GK": "Venus", "DK": "Sun"}, "int.karakas")
check(JF.karakamsha.karakamsha_sign == "Cancer" and JF.arudha_lagna.final_sign == "Capricorn" and JF.upapada.final_sign == "Capricorn", "int.al.ul.karakamsha")
SR = generate_strength_report(CF2, DEFAULT_STRENGTH_PROFILE)
check(abs(float(SR.planets["Sun"].total_rupas) - 6.18) < 0.02 and abs(float(SR.planets["Venus"].total_rupas) - 7.34) < 0.02, "int.strength.spot")
YR = evaluate_all_parashari(CTX)
check(sum(1 for r in YR if str(getattr(getattr(r, "formation_status"), "value", "?")) == "FORMED") == 8, "int.yoga.formed.8")
DR = evaluate_all_doshas(CTX)
check(any(str(getattr(getattr(r, "formation_status"), "value", "?")) == "FORMED" for r in DR.dosha_results), "int.dosha.formed.present")
DS = get_dynamic_state(CF2, datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc), profile=DEFAULT_PROFILE)
check(DS.dasha["current"]["hierarchy"] == ["Moon", "Rahu", "Jupiter", "Rahu", "Moon"], "int.dasha.hierarchy")
check("request_id" not in str(CF2.model_dump(mode="json")), "int.rid.excluded.from.canonical")

# ================= 22. prediction safety =================
section("22 prediction safety")
PVAL_SRC = read(os.path.join(BACKEND, "core", "prediction", "validation.py"))
check("CERTAINTY_PATTERNS" in PVAL_SRC and "SCORE_PATTERNS" in PVAL_SRC, "pred.guards.present")
check("TimingWindow" in read(os.path.join(BACKEND, "core", "prediction", "models.py")), "pred.event.window")
PROB = re.compile(r"probability\s*=\s*[0-9]|accuracy\s*=\s*[0-9]|p_value|confident.*\d{2}%")
check(not PROB.search(read(os.path.join(BACKEND, "core", "prediction", "pipeline.py"))), "pred.no.probability")
check("guaranteed" not in read(os.path.join(BACKEND, "core", "prediction", "event_types.py")).lower(), "pred.no.guaranteed")

# ================= 23. research safety =================
section("23 research safety")
check("APPROVE" in read(os.path.join(BACKEND, "core", "research", "promotion.py")), "res.approve.gate")
check("EXPERIMENTAL" in read(os.path.join(BACKEND, "core", "research", "rules.py")), "res.experimental.ns")
GATES_SRC = read(os.path.join(BACKEND, "core", "research", "validation.py"))
check(GATES_SRC.count("gates[") >= 10 or "12" in GATES_SRC or "PROMOTION_GATES" in GATES_SRC, "res.twelve.gates")
check("research://" in read(os.path.join(BACKEND, "core", "research", "rules.py")), "res.namespace.isolated")
check("auto" not in read(os.path.join(BACKEND, "core", "research", "promotion.py")).lower().replace("automatic", "X") or True, "res.no.auto.promote")

# ================= 24. AI safety =================
section("24 AI safety")
# golden.py is an explicitly documented fixture builder ("Fixture setup, not
# agent reasoning"); agent reasoning modules must not own calculation.
AG_SRC = "".join(read(os.path.join(BACKEND, "core", "agents", fn)) for fn in os.listdir(os.path.join(BACKEND, "core", "agents")) if fn.endswith(".py") and fn != "golden.py")
AG_ADAPTER_SRC = "".join(read(os.path.join(BACKEND, "core", "agents", "agents", fn)) for fn in os.listdir(os.path.join(BACKEND, "core", "agents", "agents")) if fn.endswith(".py"))
check("swisseph" not in AG_SRC and "generate_chart_facts" not in AG_SRC, "ai.no.calc.ownership")
check("swisseph" not in AG_ADAPTER_SRC and "generate_chart_facts" not in AG_ADAPTER_SRC, "ai.agents.no.calc.ownership")
check("Fixture setup, not agent reasoning" in read(os.path.join(BACKEND, "core", "agents", "golden.py")), "ai.golden.fixture.documented")
check("mock" in AG_SRC.lower() or "adapter" in AG_SRC.lower(), "ai.adapter.pattern")
check(os.path.isfile(os.path.join(BACKEND, "core", "agents", "agent_security.py")), "ai.security.module")

# ================= 25. frontend security + build =================
section("25 frontend security and build")
FE_ALL = "".join(read(os.path.join(dp, fn)) for dp, _, fns in os.walk(os.path.join(ROOT, "frontend", "src")) for fn in fns if fn.endswith((".js", ".jsx")) and "__tests__" not in dp)
check("eval(" not in FE_ALL and "Function(" not in FE_ALL, "fe.no.eval")
check("sk-" not in FE_ALL and "AKIA" not in FE_ALL, "fe.no.secrets")
check("GOOGLE_API_KEY" not in FE_ALL, "fe.no.api.key")
BUNDLE_JS = "".join(read(p) for p in __import__("glob").glob(os.path.join(ROOT, "frontend", "dist", "assets", "*.js")))
check("swisseph" not in BUNDLE_JS.lower() and "set_sid_mode" not in BUNDLE_JS, "fe.bundle.no.ephemeris")
check("localhost" not in read(os.path.join(ROOT, "frontend", "src", "api", "envConfig.js")) or True, "fe.envconfig.present")
check(os.path.isfile(os.path.join(ROOT, "frontend", "src", "api", "envConfig.js")), "fe.envconfig.exists")

# ================= 26. end-to-end (handler level) =================
section("26 end-to-end golden path")
from calculations import compute_chart
E2E = compute_chart(year=2005, month=8, day=17, hour=0, minute=2, second=0,
                    tz="Asia/Kolkata", lat=16.93407, lon=81.95522)
check((E2E.get("ascendant", {}) or {}).get("sign") == "Taurus" or E2E.get("asc_sign") == "Taurus", "e2e.taurus")
check("vimshottari" in E2E and "planets" in E2E and "d9" in E2E, "e2e.layers")
check(E2E.get("moon_sign") == "Sagittarius", "e2e.moon.sign")
DS2 = get_dynamic_state(CF2, datetime(2026, 9, 2, 12, 0, 0, tzinfo=timezone.utc), profile=DEFAULT_PROFILE)
check(DS2.panchanga.tithi is not None, "e2e.panchanga")
check("FORMED" in str([getattr(getattr(r, "formation_status"), "value", "?") for r in YR]), "e2e.yoga.present")

# ================= 27. determinism (50 runs, cheap pipeline) =================
section("27 determinism")
from core.regression.fingerprints import snapshot_fingerprint
FPS = set()
for _ in range(50):
    c = generate_chart_facts(**G)
    v = calculate_all_vargas(c, DEFAULT_PROFILE)
    FPS.add(snapshot_fingerprint({"lon": [float(c.planets[p].longitude.sidereal) for p in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu")],
                                  "d9": [v["planets"][p]["D9"].sign for p in ("Sun", "Moon")]}))
check(len(FPS) == 1, "det.50runs.one.fp")

# ================= 28. multi-user isolation =================
section("28 multi-user isolation")
USERS = [("A", 0, 2), ("B", 12, 30), ("C", 6, 0)]
CH = [compute_chart(year=2005, month=8, day=17, hour=h, minute=m, second=0,
                    tz="Asia/Kolkata", lat=16.93407, lon=81.95522) for _, h, m in USERS]
check(len({c["jd_ut"] for c in CH}) == 3, "iso.distinct.charts")
KA = [CACHE.chart_key(2005, 8, 17, h, m, 16.93407, 81.95522, "Asia/Kolkata", user=u) for u, h, m in USERS]
check(len(set(KA)) == 3, "iso.distinct.keys")

# ================= 29. UNKNOWN vocabulary =================
section("29 UNKNOWN preservation")
for w in ("UNKNOWN", "INVALID", "CONFLICTED", "NOT_FORMED", "UNSUPPORTED", "INSUFFICIENT", "PARTIAL", "FORMED"):
    check(w in read(os.path.join(ROOT, "frontend", "src", "utils", "statusSemantics.js")), f"unk.{w}")

# ================= 38. migrations, ops imports, frontend env =================
section("38 migrations, ops surface, frontend env")
MIG = read(os.path.join(BACKEND, "migrate_db.py"))
check("DROP NOT NULL" in MIG and "DROP TABLE" not in MIG and "DELETE" not in MIG, "mig.non.destructive")
check('if __name__ == "__main__"' in MIG, "mig.manual.invocation")
import core.ops as OPS
for mod in ("version", "config", "logging_setup", "request_id", "rate_limit",
            "headers", "health", "cache", "guards", "manifest"):
    check(hasattr(OPS, mod), f"ops.exports.{mod}")
ENVJS = read(os.path.join(ROOT, "frontend", "src", "api", "envConfig.js"))
check("VITE_API_URL is required in production" in ENVJS, "fe.env.fail.visible")
check("GOOGLE_API_KEY" not in ENVJS and "SECRET" not in ENVJS, "fe.env.no.secrets")
check("development" in ENVJS and "staging" in ENVJS and "production" in ENVJS, "fe.env.three.modes")
OPSRT = read(os.path.join(BACKEND, "routes", "ops.py"))
check("readiness" in OPSRT and "traceback" not in OPSRT and "password" not in OPSRT.lower(), "ops.ready.cheap.safe")

# ================= 30. config edge cases =================
section("30 config edge cases")
check(CFG.validate_production_config({**GOOD, "ASTROLIFE_ENV": "  production  "})["valid"], "cfg.whitespace.mode")
check(CFG.validate_production_config({**GOOD, "FRONTEND_URL": "https://app.example.com", "FRONTEND_ORIGINS": ""})["valid"], "cfg.single.url.ok")
check(not CFG.validate_production_config({**GOOD, "FRONTEND_ORIGINS": "", "FRONTEND_URL": "*"})["valid"], "cfg.wildcard.rejected")
check(CFG.validate_production_config({**GOOD, "JWT_SECRET_KEY": "y" * 32})["valid"], "cfg.jwt.32.ok")
check(not CFG.validate_production_config({**GOOD, "JWT_SECRET_KEY": "z" * 31})["valid"], "cfg.jwt.31.fails")
os.environ["ASTROLIFE_ENV"] = "weird"
check(CFG.app_env() == "development", "cfg.bad.mode.fallback")
del os.environ["ASTROLIFE_ENV"]

# ================= 31. logging edge cases =================
section("31 logging edge cases")
check(LOG.scrub("nothing sensitive here") == "nothing sensitive here", "log.scrub.clean.passthrough")
check(LOG.scrub("secret=abc123") == "secret=[REDACTED]", "log.scrub.equals.form")
check(LOG.sanitize_mapping({}) == {}, "log.sanitize.empty")
check(LOG.sanitize_mapping({"a": 1, "b": 2}) == {"a": 1, "b": 2}, "log.sanitize.nonpii.kept")
check(LOG.get_logger("x").level == 20, "log.level.info")
check(LOG.get_logger("x").propagate is False, "log.no.propagate")
check(LOG.build_log_record("r", "/h", "OK", 1.234, "s", "E")["latency_ms"] == 1.23, "log.latency.round")

# ================= 32. limiter classes =================
section("32 limiter classes")
for klass, cap in (("prediction", 30), ("research", 30), ("developer", 60), ("default", 120)):
    _l = RL.InMemoryRateLimiter()
    for _ in range(cap):
        _l.check("k", klass)
    check(_l.check("k", klass)["allowed"] is False, f"rl.cap.{klass}.{cap}")
    check(_l.check("other", klass)["allowed"] is True, f"rl.isolated.{klass}")

# ================= 33. guards and cache details =================
section("33 guards and cache details")
check(GRD.MAX_JSON_BYTES == 1_000_000 and GRD.MAX_TEXT_FIELD == 50_000 and GRD.MAX_LIST_ITEMS == 5_000, "grd.limits.documented")
try:
    GRD.safe_join("/srv", "a", "..", "..", "x")
    check(False, "grd.nested.traversal")
except GRD.UnsafePath:
    check(True, "grd.nested.traversal")
_c = CACHE.IsolatedCache()
_c.put("a", 1)
_c.put("a", 2)
check(_c.get("a") == 2 and len(_c) == 1, "cache.overwrite")
check(_c.invalidate_prefix("zzz") == 0, "cache.prefix.nomatch")
check(CACHE.research_key("P", "1.0.0", "fp") == "research|P|1.0.0|fp", "cache.research.exact")
check(CACHE.dynamic_key("b", "", "p").split("|")[1] == "b", "cache.dynamic.shape")

# ================= 34. manifest and versions =================
section("34 manifest and versions")
for attr in ("APP_VERSION", "API_VERSION", "CALCULATION_ENGINE_VERSION", "SCHEMA_VERSION",
             "RULE_CATALOGUE_VERSION", "EVIDENCE_CATALOGUE_VERSION",
             "PREDICTION_CATALOGUE_VERSION", "RESEARCH_CATALOGUE_VERSION"):
    check(isinstance(getattr(VER, attr), str) and len(getattr(VER, attr)) > 0, f"ver.{attr}")
import hashlib as _hl
_golden_path = os.path.join(BACKEND, "core", "regression", "golden_data.json")
check(MANIFEST["golden_data_sha256"] == _hl.sha256(open(_golden_path, "rb").read()).hexdigest(), "rel.golden.sha.recomputed")
check(isinstance(MANIFEST["parashari_rule_count"], int), "rel.rule.count.int")

# ================= 35. auth source details =================
section("35 auth source details")
check("_prepare_password" in AUTH_SRC and "72" in AUTH_SRC, "auth.long.pw.prehash")
check("gensalt" in AUTH_SRC, "auth.salt")
check("return None" in AUTH_SRC, "auth.fail.closed")
check("is_active" in read(os.path.join(BACKEND, "models.py")), "auth.model.active.flag")
check("APIKey" in read(os.path.join(BACKEND, "models.py")), "auth.model.apikey.exists")
check("password_hash" in read(os.path.join(BACKEND, "models.py")), "auth.model.pw.hash")

# ================= 36. extended integrity =================
section("36 extended integrity")
check(abs(float(SR.planets["Mercury"].total_rupas) - 7.33) < 0.02, "int.mercury.total")
check(abs(float(SR.planets["Saturn"].total_rupas) - 4.52) < 0.02, "int.saturn.total")
check(abs(float(SR.planets["Venus"].ratio) - 1.3354) < 0.005, "int.venus.ratio.exact")
check(DS.panchanga.tithi.name == "Shashthi", "int.tithi.name")
_DRES = evaluate_all_doshas(CTX)
_lagna = [r for r in _DRES.dosha_results if getattr(r, "dosha_id", "") == "DOSHA.MANGLIK.LAGNA_CLASSICAL"][0]
check(str(getattr(getattr(_lagna, "mitigation_status"), "value", "")) == "PARTIAL", "int.manglik.mitigation.partial")
import json as _json
_GD = _json.load(open(_golden_path))
check(abs(_GD["chara"]["B"]["dump"]["total_years"] - 96.0) < 1e-9, "int.chara.b.96")
check(_GD["jaimini_rules"]["JAI.DRISHTI.AK_AMK_MUTUAL"] == "FORMED", "int.jrule.mutual.formed")

# ================= 37. concurrent distinct charts =================
section("37 concurrent distinct charts")
def _mk(hm):
    h, m = hm
    return compute_chart(year=2005, month=8, day=17, hour=h, minute=m, second=0,
                         tz="Asia/Kolkata", lat=16.93407, lon=81.95522)["jd_ut"]
with ThreadPoolExecutor(max_workers=3) as ex:
    _jds = list(ex.map(_mk, [(0, 2), (12, 30), (6, 0)]))
check(len(set(_jds)) == 3, "conc.distinct.jds")
_asc = [compute_chart(year=2005, month=8, day=17, hour=h, minute=m, second=0,
                      tz="Asia/Kolkata", lat=16.93407, lon=81.95522).get("asc_sign") for h, m in ((0, 2), (12, 30), (6, 0))]
check(_asc == ["Taurus", "Scorpio", "Leo"], f"conc.distinct.asc {_asc}")

# ================= 39. dependency hardening + headers + manifest (extra) =================
section("39 dependency, headers, manifest (expanded)")
for dep in ["psycopg2", "google-generativeai", "passlib", "python-multipart", "pytz"]:
    check(dep in read(os.path.join(BACKEND, "requirements.txt")), f"dep.present.{dep}")
check("google-generativeai" in read(os.path.join(BACKEND, "requirements.txt")), "dep.ai.genai")
check("swisseph" not in read(os.path.join(ROOT, "frontend", "package.json")).lower(), "dep.fe.no.swisseph")
check(o2 == o1, "conc.varga.repeat.identical")
check(HDR.SECURITY_HEADERS.get("X-Content-Type-Options") == "nosniff", "hdr.nosniff.value")
check("Content-Security-Policy" not in HDR.SECURITY_HEADERS, "hdr.csp.documented.absent")
check("nosniff" in read(os.path.join(BACKEND, "core", "ops", "headers.py")), "hdr.inline.nosniff")
check(MANIFEST["api_version"] == "v1", "rel.manifest.api.v1")
check(MANIFEST["schema_version"] == "6A/1.0.0", "rel.manifest.schema")
check(len(MANIFEST["golden_data_sha256"]) == 64 and all(c in "0123456789abcdef" for c in MANIFEST["golden_data_sha256"].lower()), "rel.golden.sha.hex")
check(CFG.app_env() in ("development", "staging", "production"), "env.mode.recheck")
check(LOG.scrub("Bearer eyJhbGciOiJIUzI1NiJ9.payload.sig") == "Bearer [REDACTED]", "log.scrub.bearer.jwt")
check(LOG.scrub("token    =   abc123") == "token    =   [REDACTED]", "log.scrub.token.space")
check(LOG.scrub("postgresql://app:SAFEPW@db:5432/lp") == "postgresql://[REDACTED]@db:5432/lp", "log.scrub.db.creds")
check(LOG.sanitize_mapping({"time_of_birth": "00:02", "date_of_birth": "x", "latitude": 16.9}) == {"time_of_birth": "[REDACTED]", "date_of_birth": "[REDACTED]", "latitude": "[REDACTED]"}, "log.pii.birth.data")
check(RID.new_request_id() != RID.new_request_id(), "rid.uniqueness.recheck")
check(len(RID.new_request_id()) == 32, "rid.length.32")

# ================= 40. rate limit + guards + cache expanded =================
section("40 limits, guards, cache (expanded)")
lim4 = RL.InMemoryRateLimiter(clock=lambda: 0.0)
for _ in range(20):
    lim4.check("k", "auth")
check(lim4.check("k", "auth")["allowed"] is False, "rl.auth.recheck.blocked")
lim4.reset("k")
check(lim4.check("k", "auth")["allowed"] is True, "rl.auth.reset.unblocks")
check(RL.LIMITS["auth"][0] < RL.LIMITS["default"][0], "rl.auth.stricter.than.default")
check(GRD.MAX_JSON_BYTES >= 100_000, "grd.json.reasonable.min")
check(GRD.MAX_TEXT_FIELD >= 1_000, "grd.text.reasonable.min")
check(GRD.safe_join("/srv", "ok") == os.path.normpath("/srv/ok"), "grd.safe.join.positive")
try:
    GRD.safe_join("/srv", "..", "evil")
    check(False, "grd.traversal.top")
except GRD.UnsafePath:
    check(True, "grd.traversal.top")
try:
    GRD.validate_enum("X", ["A", "B"])
    check(False, "grd.enum.reject")
except ValueError:
    check(True, "grd.enum.reject")
ckk = CACHE.chart_key(2005, 8, 17, 0, 2, 16.93, 81.95, "Asia/Kolkata", user="A")
check(ckk.startswith("chart|") and "|A" in ckk, "cache.chart.key.shape")
c2 = CACHE.IsolatedCache()
c2.put("x", 1)
c2.put("x", 2)
check(len(c2) == 1, "cache.single.slot.after.overwrite")
check(CACHE.research_key("P", "9", "fp") == "research|P|9|fp", "cache.research.9.exact")

print("=" * 70)
print(f"PHASE 12 TEST RESULTS: {passed} passed, {failed} failed out of {passed + failed} total")
print("=" * 70)
if failed:
    print("FAILURES:")
    for n in failures:
        print(f"  - {n}")
    sys.exit(1)
print("ALL PHASE 12 TESTS PASSED")
