"""
Phase 6B — production FactResolver over canonical sources.

Resolves only canonical namespaces; distinguishes RESOLVED / MISSING /
INVALID / UNAVAILABLE with typed values, source layers, and stable
evidence/dependency IDs. No astronomy is computed: dasha activity is pure
containment over canonical timelines; everything else is field reads.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from .context import DynamicEvaluationContext
from .namespace import match_namespace

RESOLVED, MISSING, INVALID, UNAVAILABLE = "RESOLVED", "MISSING", "INVALID", "UNAVAILABLE"


class FactResolution(BaseModel):
    path: str
    status: str
    value: Any = None
    value_type: str = ""
    source_layer: str = ""
    source_id: str = ""
    evidence_id: str = ""
    dependency_id: str = ""
    model_config = {"frozen": True}


def _stable_id(prefix: str, path: str) -> str:
    return f"{prefix}:{path.replace('.', ':')}"


def _dt_ge(a: datetime, b: datetime) -> bool:
    return a >= b


class CanonicalFactResolver:
    """Deterministic resolver bound to one DynamicEvaluationContext."""

    def __init__(self, context: DynamicEvaluationContext):
        object.__setattr__(self, "context", context)
        object.__setattr__(self, "accessed", [])

    def _hit(self, path: str, value: Any, vtype: str, layer: str, sid: str) -> FactResolution:
        self.accessed.append(path)
        return FactResolution(path=path, status=RESOLVED, value=value, value_type=vtype,
                              source_layer=layer, source_id=sid,
                              evidence_id=_stable_id("ev", path),
                              dependency_id=_stable_id("dep", path))

    def _miss(self, path: str, status: str, layer: str = "") -> FactResolution:
        self.accessed.append(path)
        return FactResolution(path=path, status=status, value=None, value_type="",
                              source_layer=layer, source_id="",
                              evidence_id=_stable_id("ev", path),
                              dependency_id=_stable_id("dep", path))

    # -- layer readers -----------------------------------------------------
    def _natal_planet(self, planet: str, field: str):
        cf = self.context.chart_facts
        if cf is None:
            return None, True
        pdata = cf.planets.get(planet)
        if pdata is None:
            return None, True
        table = {"sign": pdata.sign.name, "longitude": float(pdata.longitude.sidereal),
                 "house": pdata.house, "degree": pdata.sign.degree,
                 "nakshatra": pdata.nakshatra.name, "pada": pdata.nakshatra.pada,
                 "retrograde": pdata.retrograde}
        return table.get(field, None), False

    def _varga_sign(self, varga: str, planet: str):
        vf = self.context.varga_facts or {}
        entry = (vf.get("planets", {}).get(planet) or {}).get(varga)
        if entry is None:
            return None, True
        if isinstance(entry, dict):
            return entry.get("sign"), False
        return getattr(entry, "sign", None), False

    def _strength(self, metric: str, planet: str):
        rep = self.context.strength_report
        if rep is None:
            return None, True
        try:
            if metric == "shadbala":
                r = rep.planets.get(planet)
                return (None, True) if r is None else (float(r.total_rupas), False)
            if metric == "dignity":
                r = rep.dignity.get(planet)
                if r is None:
                    return None, True
                if bool(getattr(r, "is_exalted", False)):
                    return "EXALTED", False
                if bool(getattr(r, "is_debilitated", False)):
                    return "DEBILITATED", False
                if bool(getattr(r, "is_own_sign", False)):
                    return "OWN", False
                if bool(getattr(r, "is_moolatrikona", False)):
                    return "MOOLATRIKONA", False
                return str(getattr(r, "dignity", "NONE")), False
            if metric == "avastha":
                table = rep.avastha.get(planet) or {}
                first = sorted(table.values(), key=lambda x: str(x))[0] if table else None
                return (None, True) if first is None else (str(first), False)
            if metric == "functional":
                r = rep.functional_strength.get(planet)
                return (None, True) if r is None else (str(getattr(r, "nature", r)), False)
            if metric == "bhava":
                return (None, True)
            if metric in ("vimsopaka", "composite"):
                table = getattr(rep, metric, {}) or {}
                r = table.get(planet)
                return (None, True) if r is None else (float(getattr(r, "total", 0.0)), False)
        except (AttributeError, KeyError, TypeError, ValueError):
            return None, True
        return None, True

    def _field(self, obj: Any, key: str) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)
        return getattr(obj, key, None)

    def _active_sign(self, periods, when: Optional[datetime]):
        if not periods or when is None:
            return None, True
        for p in periods:
            s, e, sign = self._field(p, "start_utc_iso"), self._field(p, "end_utc_iso"), self._field(p, "sign")
            if not (s and e):
                continue
            ds = datetime.fromisoformat(s.replace("Z", "+00:00"))
            de = datetime.fromisoformat(e.replace("Z", "+00:00"))
            if ds <= when < de:
                return sign, False
        return None, True

    # -- main entry --------------------------------------------------------
    def resolve(self, path: str) -> FactResolution:
        meta = match_namespace(path)
        if meta is None:
            if path.startswith("rule:"):
                out = (self.context.rule_outcomes or {}).get(path[len("rule:"):])
                if out is None:
                    return self._miss(path, MISSING, "DynamicRuleOutcome")
                return self._hit(path, out, "string", "DynamicRuleOutcome", f"rule:{path}")
            return self._miss(path, INVALID, "namespace")
        layer, _ = meta
        parts = path.split(".")

        if parts[0] == "natal" and parts[1] == "ascendant":
            cf = self.context.chart_facts
            if cf is None:
                return self._miss(path, MISSING, layer)
            v = cf.ascendant.sign.name if parts[2] == "sign" else cf.ascendant.sign.degree
            return self._hit(path, v, "string" if parts[2] == "sign" else "float", layer, "ChartFacts.ascendant")

        if parts[0] == "natal":
            v, missing = self._natal_planet(parts[1], parts[2])
            if missing:
                return self._miss(path, MISSING, layer)
            t = {"sign": "Sign", "longitude": "float", "house": "HouseNumber",
                 "degree": "float", "nakshatra": "Nakshatra", "pada": "Pada",
                 "retrograde": "bool"}[parts[2]]
            if parts[2] == "house" and not (isinstance(v, int) and 1 <= v <= 12):
                return self._miss(path, INVALID, layer)
            if parts[2] == "pada" and v not in (1, 2, 3, 4):
                return self._miss(path, INVALID, layer)
            return self._hit(path, v, t, layer, f"ChartFacts.planets.{parts[1]}")

        if parts[0] == "houses":
            cf = self.context.chart_facts
            if cf is None:
                return self._miss(path, MISSING, layer)
            try:
                house = cf.houses.get(int(parts[1]))
            except (KeyError, ValueError):
                return self._miss(path, INVALID, layer)
            if house is None:
                return self._miss(path, MISSING, layer)
            if parts[2] == "sign":
                v = house.sign.name
            elif parts[2] == "lord":
                from core.jaimini.arudha import CLASSICAL_SIGN_LORDS
                v = CLASSICAL_SIGN_LORDS.get(house.sign.name)
            else:
                return self._miss(path, INVALID, layer)
            if v is None:
                return self._miss(path, MISSING, layer)
            return self._hit(path, v, "Sign", layer, f"ChartFacts.houses.{parts[1]}")

        if parts[0] == "varga":
            v, missing = self._varga_sign(parts[1], parts[2])
            if missing or v is None:
                return self._miss(path, UNAVAILABLE if self.context.varga_facts is None else MISSING, layer)
            return self._hit(path, v, "Sign", layer, f"VargaFacts.{parts[1]}.{parts[2]}")

        if parts[0] == "strength":
            v, missing = self._strength(parts[1], parts[2])
            if missing:
                scope = UNAVAILABLE if self.context.strength_report is None else MISSING
                return self._miss(path, scope, layer)
            t = "float" if isinstance(v, float) else "string"
            return self._hit(path, v, t, layer, f"StrengthReport.{parts[1]}.{parts[2]}")

        if parts[0] == "dasha":
            system = parts[1]
            if system == "vimshottari":
                tl, when = self.context.vimshottari_timeline, self.context.vimshottari_datetime
                if tl is None:
                    return self._miss(path, UNAVAILABLE, layer)
                if when is None:
                    return self._miss(path, MISSING, layer)
                from core.calculation.dasha import get_current_dasha
                try:
                    cur = get_current_dasha(tl, when)
                except Exception:
                    return self._miss(path, INVALID, layer)
                if parts[2] in ("mahadasha", "active_sign"):
                    lord = getattr(cur.get("mahadasha"), "lord", None)
                    if lord is None:
                        return self._miss(path, MISSING, layer)
                    return self._hit(path, lord, "Planet", layer, "DashaTimeline.vimshottari")
                if parts[2] == "antardasha":
                    lord = getattr(cur.get("antardasha"), "lord", None)
                    if lord is None:
                        return self._miss(path, MISSING, layer)
                    return self._hit(path, lord, "Planet", layer, "DashaTimeline.vimshottari")
            else:
                res, when = self.context.jaimini_dasha_result, self.context.jaimini_dasha_datetime
                if res is None:
                    return self._miss(path, UNAVAILABLE, layer)
                get = (lambda k: res.get(k)) if isinstance(res, dict) else (lambda k: getattr(res, k, None))
                if parts[2] == "profile":
                    return self._hit(path, get("profile_method") or get("method"), "string", layer, "JaiminiDashaResult")
                if parts[2] in ("mahadasha", "active_sign"):
                    sign, missing = self._active_sign(get("periods") or [], when)
                    if missing:
                        return self._miss(path, MISSING, layer)
                    return self._hit(path, sign, "Sign", layer, "JaiminiDashaResult")
                if parts[2] == "period_id":
                    return self._hit(path, get("profile_method"), "string", layer, "JaiminiDashaResult")
            return self._miss(path, INVALID, layer)

        if parts[0] == "transit":
            snap = self.context.transit_snapshot
            if snap is None:
                return self._miss(path, UNAVAILABLE, layer)
            planets = snap.get("planets") if isinstance(snap, dict) else getattr(snap, "planets", {})
            p = planets.get(parts[1])
            if p is None:
                return self._miss(path, MISSING, layer)
            v = (p.get(parts[2]) if isinstance(p, dict) else getattr(p, parts[2], None))
            if v is None:
                return self._miss(path, MISSING, layer)
            t = {"sign": "Sign", "longitude": "float", "house": "HouseNumber"}[parts[2]]
            return self._hit(path, v, t, layer, f"TransitSnapshot.{parts[1]}")

        if parts[0] == "jaimini":
            jf = self.context.jaimini_facts
            if jf is None:
                return self._miss(path, UNAVAILABLE, layer)
            if parts[1] == "karaka":
                item = jf.chara_karakas.karakas.get(parts[2])
                if item is None:
                    return self._miss(path, MISSING, layer)
                return self._hit(path, item.planet, "Planet", layer, "JaiminiFacts.chara_karakas")
            if parts[1] == "drishti":
                return self._hit(path, {s: list(v) for s, v in jf.rashi_drishti.sign_aspects.items()},
                                 "map", layer, "JaiminiFacts.rashi_drishti")
            if parts[1] == "pada":
                pada = jf.arudha_padas.get(int(parts[2]))
                if pada is None:
                    return self._miss(path, MISSING, layer)
                return self._hit(path, pada.final_sign, "Sign", layer, "JaiminiFacts.arudha_padas")
            if parts[1] == "karakamsha":
                return self._hit(path, jf.karakamsha.karakamsha_sign, "Sign", layer, "JaiminiFacts.karakamsha")
            if parts[1] == "swamsa":
                return self._hit(path, jf.karakamsha.swamsa_navamsha_lagna_sign, "Sign", layer,
                                 "JaiminiFacts.karakamsha")
            return self._miss(path, INVALID, layer)

        if parts[0] == "aspects":
            table = self.context.aspect_map or {}
            if parts[1] not in table:
                return self._miss(path, MISSING, layer)
            return self._hit(path, list(table[parts[1]]), "list", layer, "RuleContext.aspects")

        return self._miss(path, INVALID, layer)

    def resolve_many(self, paths: List[str]) -> Dict[str, FactResolution]:
        return {p: self.resolve(p) for p in paths}
