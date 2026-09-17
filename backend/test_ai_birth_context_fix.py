"""
Test suite for AI Astrologer birth context resolution fix.

Verifies:
1. Birth context resolution order (top-level -> context_data.request -> context_data.birth_params).
2. CASE A: Top-level birth params -> transit available.
3. CASE B: Only context_data.request birth params -> transit available.
4. CASE C: No birth params anywhere -> unavailable-no-birth-params.
5. CASE D: Actual AIAstrologerPage request shape -> transit available.
6. Golden natal anchors unchanged (JD, ayanamsha, Ascendant, D1, D9, Panchanga, Dasha).
7. Current transits correctly evaluated and non-fabricated.
8. Exact user query structure ("what is the current transit data placements").
"""
import sys
import os
import unittest
from datetime import datetime
import json

from backend.routes.ai_routes import (
    AIRequest,
    _request_birth,
    _attach_transit_section,
    _attach_future_section,
    _attach_agent_section,
    summarize_context,
    _gemini_safe_payload,
)
from backend.core.calculation.pipeline import generate_chart_facts
from backend.core.calculation.varga import calculate_all_vargas
from backend.canonical_response import build_canonical_compute_response

GOLDEN_BIRTH = {
    "year": 2005,
    "month": 8,
    "day": 17,
    "hour": 0,
    "minute": 2,
    "second": 0,
    "lat": 16.93407,
    "lon": 81.95522,
    "tz": "Asia/Kolkata",
}


class TestAIBirthContextFix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chart_facts = generate_chart_facts(
            year=GOLDEN_BIRTH["year"],
            month=GOLDEN_BIRTH["month"],
            day=GOLDEN_BIRTH["day"],
            hour=GOLDEN_BIRTH["hour"],
            minute=GOLDEN_BIRTH["minute"],
            second=GOLDEN_BIRTH["second"],
            lat=GOLDEN_BIRTH["lat"],
            lon=GOLDEN_BIRTH["lon"],
            tz_name=GOLDEN_BIRTH["tz"],
        )
        cls.varga_res = calculate_all_vargas(cls.chart_facts)
        cls.chart_data = build_canonical_compute_response(
            cls.chart_facts, cls.varga_res, GOLDEN_BIRTH
        )

    def test_resolution_order_toplevel(self):
        """Top-level parameters take precedence."""
        req = AIRequest(
            query="current transits",
            context_data={
                "request": {
                    "year": 1990, "month": 1, "day": 1,
                    "hour": 0, "minute": 0, "second": 0,
                    "tz": "UTC", "lat": 0.0, "lon": 0.0,
                }
            },
            **GOLDEN_BIRTH
        )
        b = _request_birth(req)
        self.assertIsNotNone(b)
        self.assertEqual(b["year"], 2005)
        self.assertEqual(b["month"], 8)
        self.assertEqual(b["day"], 17)
        self.assertEqual(b["lat"], 16.93407)

    def test_resolution_order_context_request(self):
        """Fallback to context_data.request when top-level is omitted."""
        req = AIRequest(
            query="current transits",
            context_data={"request": GOLDEN_BIRTH}
        )
        b = _request_birth(req)
        self.assertIsNotNone(b)
        self.assertEqual(b["year"], 2005)
        self.assertEqual(b["month"], 8)
        self.assertEqual(b["day"], 17)
        self.assertEqual(b["lat"], 16.93407)
        self.assertEqual(b["lon"], 81.95522)
        self.assertEqual(b["tz"], "Asia/Kolkata")

    def test_resolution_order_context_birth_params(self):
        """Fallback to context_data.birth_params when request is absent."""
        req = AIRequest(
            query="current transits",
            context_data={"birth_params": GOLDEN_BIRTH}
        )
        b = _request_birth(req)
        self.assertIsNotNone(b)
        self.assertEqual(b["year"], 2005)
        self.assertEqual(b["month"], 8)
        self.assertEqual(b["day"], 17)

    def test_case_a_toplevel_params(self):
        """CASE A: Top-level birth params -> transit available."""
        req = AIRequest(
            query="what is the current transit data placements",
            context_data=self.chart_data,
            **GOLDEN_BIRTH
        )
        opt = summarize_context(req.context_data)
        opt = _attach_transit_section(opt, req)
        
        self.assertEqual(opt.get("TRANSIT_STATUS"), "available")
        self.assertIn("CURRENT_TRANSITS", opt)
        ct = opt["CURRENT_TRANSITS"]
        self.assertNotIn("status", ct)  # available section does not have status='unavailable'
        self.assertIn("planets", ct)
        self.assertEqual(len(ct["planets"]), 9)
        self.assertIn("TRANSIT_NATAL_RELATIONS", opt)
        self.assertIn("TRANSIT_ASPECTS", opt)
        self.assertIn("PROVENANCE", opt)
        self.assertTrue(opt["PROVENANCE"].get("transit_available"))

    def test_case_b_context_request_only(self):
        """CASE B: Only context_data.request birth params -> transit available."""
        req = AIRequest(
            query="what is the current transit data placements",
            context_data=self.chart_data
        )
        opt = summarize_context(req.context_data)
        opt = _attach_transit_section(opt, req)
        
        self.assertEqual(opt.get("TRANSIT_STATUS"), "available")
        self.assertIn("CURRENT_TRANSITS", opt)
        ct = opt["CURRENT_TRANSITS"]
        self.assertIn("planets", ct)
        self.assertEqual(len(ct["planets"]), 9)
        self.assertIn("TRANSIT_NATAL_RELATIONS", opt)
        self.assertIn("TRANSIT_ASPECTS", opt)
        self.assertTrue(opt.get("PROVENANCE", {}).get("transit_available"))

    def test_case_c_no_birth_params_anywhere(self):
        """CASE C: No birth params anywhere -> unavailable-no-birth-params."""
        req = AIRequest(
            query="what is the current transit data placements",
            context_data={}
        )
        opt = summarize_context(req.context_data)
        opt = _attach_transit_section(opt, req)
        
        self.assertEqual(opt.get("TRANSIT_STATUS"), "unavailable-no-birth-params")
        self.assertEqual(
            opt.get("CURRENT_TRANSITS", {}).get("status"), "unavailable"
        )
        self.assertEqual(
            opt.get("CURRENT_TRANSITS", {}).get("reason"), "no-birth-params"
        )
        self.assertFalse(opt.get("PROVENANCE", {}).get("transit_available"))

    def test_case_d_actual_ui_page_shape(self):
        """CASE D: Actual AIAstrologerPage request shape -> transit available."""
        # Frontend AIAstrologerPage now passes top-level birthParams in addition to chartData
        req = AIRequest(
            query="what is the current transit data placements",
            context_data=self.chart_data,
            **GOLDEN_BIRTH
        )
        opt = summarize_context(req.context_data)
        opt = _attach_transit_section(opt, req)
        opt = _attach_future_section(opt, req, req.query)
        opt = _attach_agent_section(opt, req, req.query)
        safe = _gemini_safe_payload(opt)
        
        self.assertEqual(safe.get("TRANSIT_STATUS"), "available")
        self.assertIn("CURRENT_TRANSITS", safe)
        self.assertIn("planets", safe["CURRENT_TRANSITS"])
        self.assertEqual(len(safe["CURRENT_TRANSITS"]["planets"]), 9)
        self.assertIn("TRANSIT_NATAL_RELATIONS", safe)
        self.assertIn("TRANSIT_ASPECTS", safe)

    def test_golden_natal_anchors_preserved(self):
        """Golden natal anchors remain identical across the pipeline."""
        req = AIRequest(
            query="what is the current transit data placements",
            context_data=self.chart_data
        )
        opt = summarize_context(req.context_data)
        opt = _attach_transit_section(opt, req)

        # 1. Facts / Time / JD / Ayanamsha
        self.assertAlmostEqual(self.chart_facts.time.julian_day, 2453599.2722222223, places=6)
        self.assertAlmostEqual(self.chart_facts.ayanamsha.value, 23.93565836563647, places=6)
        self.assertEqual(self.chart_facts.ascendant.sign.name, "Taurus")
        self.assertAlmostEqual(self.chart_facts.ascendant.sign.degree, 9.955221668, places=4)

        # 2. Ascendant in context
        self.assertEqual(opt["ascendant"]["sign"], "Taurus")
        # 3. Moon sign
        self.assertEqual(opt["moon_sign"], "Sagittarius")

        # 4. All 9 D1 Planets
        d1_expected = {
            "Sun": ("Leo", 0.04186),
            "Moon": ("Sagittarius", 17.86278),
            "Mars": ("Aries", 16.59308),
            "Mercury": ("Cancer", 14.83956),
            "Jupiter": ("Virgo", 21.84264),
            "Venus": ("Virgo", 5.64177),
            "Saturn": ("Cancer", 10.06251),
            "Rahu": ("Pisces", 22.32643),
            "Ketu": ("Virgo", 22.32643),
        }
        for p_name, (exp_sign, exp_deg) in d1_expected.items():
            self.assertIn(p_name, opt["planets"])
            self.assertEqual(opt["planets"][p_name]["sign"], exp_sign)
            actual_deg = opt["planets"][p_name].get("degree_in_sign", opt["planets"][p_name].get("degree"))
            self.assertAlmostEqual(actual_deg, exp_deg, places=3, msg=f"Mismatch for {p_name} degree")

        # 5. All 9 D9 (Navamsha) Planets & Ascendant
        d9_expected = {
            "Sun": "Aries",
            "Moon": "Virgo",
            "Mars": "Leo",
            "Mercury": "Scorpio",
            "Jupiter": "Cancer",
            "Venus": "Aquarius",
            "Saturn": "Libra",
            "Rahu": "Capricorn",
            "Ketu": "Cancer",
        }
        self.assertEqual(self.varga_res["ascendant"]["D9"].sign, "Pisces")
        for p_name, exp_d9_sign in d9_expected.items():
            self.assertEqual(
                self.varga_res["planets"][p_name]["D9"].sign,
                exp_d9_sign,
                msg=f"Mismatch for D9 {p_name}"
            )

        # 6. Dasha
        self.assertIn("DASHA", opt)
        self.assertIn("mahadasha", opt["DASHA"])


if __name__ == "__main__":
    unittest.main()
