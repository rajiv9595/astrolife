# Astrolife V2 — DynamicAstrologyState Specification (Phase 3 Step 27-28)

**Version**: 1.0  
**Date**: 2026-09-02  
**Engine**: `backend/core/calculation/dynamic.py`  
**Service**: `get_dynamic_state(chart_facts, evaluation_datetime, ...)`  
**API**: `POST /dynamic/state`, `/dynamic/panchanga`, `/dynamic/transit-snapshot`, `/dynamic/transit-range`, `/dynamic/compute-dynamic`

---

## 1. Architecture — Static vs Dynamic Separation

```
STATIC NATAL (Phase 1/2): Birth Data (year/month/day/hour/min/sec, lat/lon/tz)
      ↓
  generate_chart_facts(...)  →  ChartFacts
      ↓
  D1 / Vargas / Natal Facts (houses, planets, ayanamsha, etc.)  [immutable, timeless]

DYNAMIC (Phase 3):
  ChartFacts + evaluation_datetime (+ location if different) + CalculationProfile
      ↓
  get_dynamic_state(...)
      ↓
  DynamicAstrologyState
      ↓
  Panchanga + Dasha (current) + Transits/Aspects/Events  (time-dependent facts)
```

**Rule**: `ChartFacts` holds only natal. `DynamicAstrologyState` holds only time-dependent. Never mix — `DynamicAstrologyState` is not nested inside `ChartFacts`. The API returns them side-by-side or via separate endpoint.

---

## 2. Object Shape

```python
class DynamicAstrologyState(BaseModel):
    evaluation_datetime: str          # ISO as provided (preserves tz offset)
    evaluation_jd: float              # JD(UT) of evaluation
    evaluation_utc_iso: str           # UTC ISO Z
    location: Dict[str,Any]           # {latitude, longitude, timezone} — for panchanga (defaults to birth location if not overridden)
    panchanga: PanchangaDetails       # from panchanga.py (§3)
    dasha: Dict[str,Any]              # {timeline: DashaTimeline, current: get_current_dasha(...), profile, boundary_convention}
    transits: Optional[Dict[str,Any]] # {snapshot: TransitSnapshot, western_aspects: [...], parashari_aspects: [...], relations: [...], cache_key: {...}}
    events: Optional[List[Dict]]      # if include_events True
    metadata: Dict[str,Any]           # {profile, generated_via, transit_available}
```

Example partial:

```json
{
  "evaluation_datetime": "2026-09-02T12:00:00+00:00",
  "evaluation_jd": 2461287.0,
  "evaluation_utc_iso": "2026-09-02T12:00:00Z",
  "location": {"latitude":16.93407,"longitude":81.95522,"timezone":"Asia/Kolkata"},
  "panchanga": {
    "tithi": {"index":21,"name":"Shashthi","paksha":"Krishna Paksha", "start_utc_iso":"..."},
    "karana": {"name":"Vanija","index_60":41},
    "nakshatra": {"name":"Bharani","pada":3},
    "yoga": {"name":"Dhruva"},
    "vara": {"weekday_name":"Wednesday","local_date":"2026-09-02"},
    "sunrise_sunset": {"sunrise_local":"05:48 AM"}
  },
  "dasha": {
    "current": {
      "mahadasha": {"lord":"Moon","start_utc_iso":"..."},
      "antardasha": {"lord":"Rahu"},
      "pratyantardasha": {"lord":"Jupiter"},
      "sookshma": {"lord":"Rahu"},
      "prana": {"lord":"Moon"},
      "hierarchy": ["Moon","Rahu","Jupiter","Rahu","Moon"]
    },
    "profile": {"days_per_year":365.2425},
    "boundary_convention": "[start_jd, end_jd) half-open"
  },
  "transits": {
    "snapshot": {"evaluation_jd":..., "planets":{"Sun":{"sidereal_longitude":135.8,"sign":"Leo"}}},
    "western_aspects": [...],
    "parashari_aspects": [...],
    "relations": [...],
    "cache_key": {"datetime":"2026-09-02T12:00:00Z","latitude":16.93,"profile":{...}}
  }
}
```

No interpretation (career/marriage/good-bad) — facts only.

---

## 3. Service Function — Purity Requirement

```
get_dynamic_state(
    chart_facts: ChartFacts,
    evaluation_datetime: datetime,  # EXPLICIT — no clock inside (Step Critical Rule)
    latitude: Optional[float] = None,   # panchanga/transit location (default = birth lat)
    longitude: Optional[float] = None,  # (default = birth lon)
    tz_name: Optional[str] = None,      # (default = birth tz)
    profile: Optional[CalculationProfile] = None,  # (default = chart_facts.profile or DEFAULT_PROFILE)
    include_events: bool = False,
    event_window_days: int = 7,
) -> DynamicAstrologyState
```

**Critical Rule Enforcement**: Inside `dynamic.py`, `panchanga.py`, `dasha.py`, `transit/*` there is **no** `datetime.now()` / `utcnow()` / `time.time()`. Search of `backend/core/` confirms zero occurrences (except in comments). The *only* place allowed to read wall clock is the **API boundary**:

```python
# In routes/dynamic.py
if not req.evaluation_datetime:
    eval_dt = datetime.now(timezone.utc)  # UI request -> "now"
else:
    eval_dt = parse_iso(req.evaluation_datetime)  # tests/historical/future pass fixed
state = get_dynamic_state(chart_facts, eval_dt, ...)  # explicit passed
```

Thus tests are deterministic (fixed `2026-09-02T12:00:00Z`), UI gets live data, historical analysis works with past date, forecasting works with future date — all through same pure core.

---

## 4. Sub-components Orchestrated

| Step | Call | Inputs | Outputs |
|------|------|--------|---------|
| Panchanga (§4) | `calculate_panchanga(evaluation_datetime, lat, lon, tz, profile)` | explicit datetime + location | Tithi/Karana/Nakshatra/Yoga/Vara/Sunrise |
| Dasha (§5) | `calculate_vimshottari_timeline(chart_facts, profile, years_ahead=...)` + `get_current_dasha(timeline, evaluation_datetime)` | ChartFacts + eval datetime | current MD/AD/PD/Sookshma/Prana |
| Transits (§6) | `calculate_transit_positions(evaluation_datetime, profile)` | explicit datetime | 9 planets sidereal/tropical/etc. |
| Relations | `compute_transit_natal_relations`, `compute_western_aspects`, `compute_parashari_aspects` | transits + chart_facts | house/aspect facts |
| Events (optional) | `detect_transit_events(chart_facts, evaluation_datetime, evaluation+window)` | start/end datetimes | ingress/station/conjunction list |

Each is pure.

---

## 5. Dasha Current State Detail

- Timeline generated for `years_ahead` covering evaluation (if evaluation is 80y after birth, generate 120y; if further, cap 200). Minimal `120y` always.
- Current extracted via half-open rule; hierarchy list flows down until mismatch (if evaluation before birth or beyond timeline, `note` field explains, remains deterministic).

Example for golden chart at `2026-09-02`:

```
Birth 2005-08-17 Venus 13.206y -> Venus until 2018-10-xx
Sun 2018-2024, Moon 2024-2034
So at 2026-09-02: MD Moon, AD Rahu (Rahu 18y*10y/120=1.5y slice etc.),
PD Jupiter ( ... ), Sookshma Rahu, Prana Moon  (levels 1-5 exact per calculation)
```

Verified against JHora approximate check.

---

## 6. Panchanga Context

Same as `ASTROLIFE_V2_PANCHANGA_SPECIFICATION.md` — embedded. Vara uses panchanga location's local civil date.

---

## 7. Transit Caching Structure (Step 29)

**Not prematurely optimized** — current implementation computes transits on demand, but structures code so cache can be added later **without changing call sites**.

Cache key design (already in code):

```python
transits["cache_key"] = {
    "datetime": eval_utc_iso,           # evaluation moment
    "latitude": latitude,               # only affects sunrise/transit topography? Not transit lon (geocentric) but kept for uniformity
    "longitude": longitude,
    "timezone": tz_name,                # for local formatting
    "profile": profile.model_dump(),    # MUST include — different ayanamsha/node gives different longitudes
    "ephemeris_version": swe.version,   # SWE version for reproducibility
    "jd": eval_jd,
}
```

**Do not cache without including `calculation profile`** — enforced because key contains profile dump.

Future `functools.lru_cache` or Redis can use this key. Place of cache would be `calculate_transit_positions` memoized wrapper; not yet added to keep Phase 3 focused on facts, not performance.

---

## 8. API Backwards Compatibility (Step 30)

| Endpoint | Previous | After Phase 3 | Change |
|----------|----------|--------------|--------|
| `POST /compute` | Exists: birth → chart + legacy dasha/panchanga | Preserved unchanged (still returns `vimshottari`, `tithi`, `karana`, etc. via legacy shape) | Non-breaking: adds no breaking field, retains `dasha` as before (now pure) |
| `POST /match` | Exists | Preserved | No change |
| `POST /dynamic/state` | New | Added | Pure dynamic state |
| `POST /dynamic/panchanga` | New | Added | Panchanga for any date |
| `POST /dynamic/transit-snapshot` | New | Added | Single transit snapshot |
| `POST /dynamic/transit-range` | New | Added | Arbitrary range (5-month forecast) |
| `POST /dynamic/compute-dynamic` | New | Added | Legacy compute + dynamic merge for incremental frontend migration |

Existing frontend continues to work against `/compute`. New dynamic features use `/dynamic/*`.

---

## 9. Inputs / Outputs Table

| Field | Source | Example |
|-------|--------|---------|
| `evaluation_datetime` | Caller (UI/test/historical) | `2026-09-02T12:00:00Z` |
| `location` | caller or birth fallback | `16.93407, 81.95522, Asia/Kolkata` |
| `calculation_profile` | caller or ChartFacts or DEFAULT | SIDEREAL LAHIRI MEAN WHOLE_SIGN + dasha 365.2425 |
| `ephemeris_version` | SWE library | `2.10.03` |
| `jd` | derived UT | 2461287.0 |

---

## 10. Testing

`backend/test_dynamic_phase3.py`:

- Dynamic state at birth yields MD Venus (not overwritten by now)
- At 2026-09-02 produces same hierarchy as standalone `get_current_dasha`
- Panchanga via dynamic equals standalone `calculate_panchanga` (same tithi etc.)
- Transit snapshot via dynamic equals standalone `calculate_transit_positions`
- Cache key includes datetime+profile+ephemeris_version; different profile yields different cache key for same datetime
- `include_events=True` populates events non-empty over 30-day window containing known sign ingress

---

## 11. What Is NOT Done (Step 33)

- No scoring, interpretation, predictions, marriage/career, remedies, AI.
- This phase only produces facts; later phase will consume `DynamicAstrologyState` for yoga transit activation etc. but not here.

---

## 12. How to Call

```python
from core.calculation.pipeline import generate_chart_facts
from core.calculation.dynamic import get_dynamic_state
from datetime import datetime, timezone

facts = generate_chart_facts(2005,8,17,0,2,0,16.93407,81.95522,"Asia/Kolkata")
now = datetime.now(timezone.utc)  # UI boundary reads clock
state = get_dynamic_state(facts, now)  # core is pure

# Test
fixed = datetime(2026,9,2,12,0,0, tzinfo=timezone.utc)
state2 = get_dynamic_state(facts, fixed)
assert state2.dasha["current"]["hierarchy"] == ["Moon","Rahu","Jupiter","Rahu","Moon"]

# Range (5-month forecast)
from core.calculation.dynamic import get_transit_range
from datetime import datetime
start = datetime(2026,9,2, tzinfo=timezone.utc)
end   = datetime(2027,2,2, tzinfo=timezone.utc)
forecast = get_transit_range(start, end, 16.93407, 81.95522, "Asia/Kolkata")
```

---

## 13. Tradition Separation

Dynamic state carries `system` fields per component:

- Panchanga: `"VEDIC_PANCHANGA"`
- Western aspects: `system: "WESTERN", type:"DEGREE_ASPECT"`
- Parashari: `system: "PARASHARI", type:"GRAHA_DRISHTI"`
- Transit snapshot: `system: "SIDEREAL"` per profile

Never mixed in one list without label.

