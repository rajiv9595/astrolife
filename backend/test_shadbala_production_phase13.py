"""
Astrolife — Phase 13: canonical Phase 4 Shadbala production integration.

Proves the REAL production POST /compute path (live uvicorn server +
HTTP) returns canonical Phase 4 Shadbala values, and that no legacy
strength module is authoritative in the production route.

Run from repo root with the backend venv:
  backend/.venv/Scripts/python backend/test_shadbala_production_phase13.py

Golden chart: MEDAPATI BHASKARA VENKATA RAJEEV REDDY, 17/08/2005,
00:02 Asia/Kolkata, Anaparthy (16.93407, 81.95522). Lahiri, Mean Node,
Whole Sign houses.

Canonical targets (accepted Phase 4 engine, tolerance 0.02 Rupas):
  Sun 6.18 / Moon 5.73 / Mars 5.50 / Mercury 7.33 /
  Jupiter 6.81 / Venus 7.34 / Saturn 4.52
Statuses: Sun/ Moon/ Saturn Moderate; Mars/ Mercury/ Jupiter/ Venus Strong.

Exit 0 = all pass, 1 = any failure.
"""
import json
import os
import subprocess
import sys
import time
import urllib.request

REPO_ROOT = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
# Allow running as `python backend/test_...py` from repo root.
if os.path.basename(REPO_ROOT) == "backend":
    REPO_ROOT = os.path.dirname(REPO_ROOT)
sys.path.insert(0, REPO_ROOT)

PORT = 8131
BASE = f"http://127.0.0.1:{PORT}"

GOLDEN_RUPAS = {
    "Sun": 6.18, "Moon": 5.73, "Mars": 5.50, "Mercury": 7.33,
    "Jupiter": 6.81, "Venus": 7.34, "Saturn": 4.52,
}
GOLDEN_LABELS = {
    "Sun": "Moderate", "Moon": "Moderate", "Mars": "Strong",
    "Mercury": "Strong", "Jupiter": "Strong", "Venus": "Strong",
    "Saturn": "Moderate",
}
TOL = 0.02

passed = 0
failed = 0
failures = []


def check(cond, name, detail=""):
    global passed, failed
    if cond:
        passed += 1
    else:
        failed += 1
        failures.append(name)
        print(f"  FAIL {name} {detail}")


def post_compute():
    payload = json.dumps({
        "year": 2005, "month": 8, "day": 17,
        "hour": 0, "minute": 2, "second": 0,
        "tz": "Asia/Kolkata", "lat": 16.93407, "lon": 81.95522,
    }).encode()
    req = urllib.request.Request(
        f"{BASE}/compute", data=payload,
        headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode())


def main():
    global passed, failed
    server = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=REPO_ROOT,
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        # Wait for boot.
        up = False
        for _ in range(36):
            time.sleep(5)
            try:
                with urllib.request.urlopen(f"{BASE}/health", timeout=10) as r:
                    if json.loads(r.read().decode()).get("status") == "active":
                        up = True
                        break
            except Exception:
                pass
        check(up, "http.server.boot")
        if not up:
            print("server did not boot; aborting HTTP checks")
            return 1

        resp = post_compute()
        check(isinstance(resp, dict), "http.compute.200.dict")

        # Response must be fully JSON-serializable (FastAPI contract).
        try:
            json.dumps({"strengths": resp["strengths"], "shadbala": resp["shadbala"]})
            check(True, "http.response.json.serializable")
        except Exception as e:
            check(False, "http.response.json.serializable", str(e))

        rows = {s["planet"]: s for s in resp.get("strengths", [])}
        shadbala = resp.get("shadbala", {}) or {}

        # TEST 1-7: golden Rupas through the real /compute path.
        for planet, exp in GOLDEN_RUPAS.items():
            got = rows.get(planet, {}).get("score")
            check(isinstance(got, (int, float)) and abs(float(got) - exp) < TOL,
                  f"TEST.rupas.{planet}", f"expected~{exp} got={got}")
            sgot = (shadbala.get(planet) or {}).get("total_rupas")
            check(isinstance(sgot, (int, float)) and abs(float(sgot) - exp) < TOL,
                  f"TEST.shadbala.{planet}", f"expected~{exp} got={sgot}")

        # TEST 8: canonical statuses.
        for planet, exp in GOLDEN_LABELS.items():
            check(rows.get(planet, {}).get("label") == exp,
                  f"TEST.status.{planet}", f"got={rows.get(planet, {}).get('label')}")

        # Canonical dignity wiring (anti legacy-Enemy-Sign proof).
        check(rows.get("Mars", {}).get("nature") == "Own Sign",
              "TEST.dignity.mars.ownsign", f"got={rows.get('Mars', {}).get('nature')}")
        check(rows.get("Venus", {}).get("nature") == "Debilitated",
              "TEST.dignity.venus.debilitated",
              f"got={rows.get('Venus', {}).get('nature')}")
        check(all(rows[p].get("score_unit") == "rupas" for p in GOLDEN_RUPAS),
              "TEST.score.unit.rupas")
        check(all(isinstance(rows[p].get("reasons"), list) and len(rows[p]["reasons"]) > 0
                  for p in GOLDEN_RUPAS), "TEST.reasons.present")

        # STEP 7: nodes explicitly not evaluated, no fabricated scores.
        for node in ("Rahu", "Ketu"):
            n = rows.get(node, {})
            check(n.get("label") == "Not Evaluated", f"TEST.nodes.{node}.label",
                  f"got={n.get('label')}")
            check(n.get("score") is None, f"TEST.nodes.{node}.no.score",
                  f"got={n.get('score')}")
            check(node not in shadbala, f"TEST.nodes.{node}.no.shadbala")

        # TEST 9/10: legacy modules must not be authoritative in the route.
        route_path = os.path.join(REPO_ROOT, "backend", "routes", "astro.py")
        with open(route_path, encoding="utf-8") as f:
            route_src = f.read()
        check("calculate_chart_strengths(" not in route_src,
              "TEST9.no.legacy.strength_evaluator")
        check("from backend.strength_evaluator import" not in route_src,
              "TEST9.no.legacy.strength_evaluator.import")
        check("compute_shadbala(" not in route_src,
              "TEST10.no.legacy.backend.shadbala")
        check("from backend.shadbala import" not in route_src,
              "TEST10.no.legacy.backend.shadbala.import")
        check("calculate_all_shadbala" in route_src,
              "TEST.canonical.wired.calculate_all_shadbala")
        check("calculate_all_dignities" in route_src,
              "TEST.canonical.wired.calculate_all_dignities")
    finally:
        try:
            server.terminate()
            server.wait(timeout=30)
        except Exception:
            try:
                server.kill()
            except Exception:
                pass

    print("=" * 70)
    print(f"PHASE 13 SHADBALA PRODUCTION INTEGRATION: {passed} passed, {failed} failed")
    if failures:
        print("FAILURES:")
        for n in failures:
            print(f"  - {n}")
    print("=" * 70)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
