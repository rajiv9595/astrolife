import sys
sys.path.insert(0, '.')

from core.calculation.pipeline import generate_chart_facts
from core.calculation.config import DEFAULT_PROFILE
from core.calculation.varga import calculate_all_vargas
from core.jaimini.pipeline import generate_jaimini_facts
from core.jaimini.profile import JaiminiCalculationProfile
from core.jaimini.integration import evaluate_jaimini
from core.jaimini.dasha import JaiminiDashaProfile, calculate_jaimini_dasha
from core.jaimini.timing.pipeline import evaluate_jaimini_timing
from datetime import datetime, timezone

gchart = generate_chart_facts(year=2005, month=8, day=17, hour=0, minute=2, second=0,
    lat=16.93407, lon=81.95522, tz_name='Asia/Kolkata',
    location_name='Anaparthy', country_name='India', profile=DEFAULT_PROFILE)
gvf = calculate_all_vargas(gchart, DEFAULT_PROFILE)
gjf = generate_jaimini_facts(gchart, gvf, JaiminiCalculationProfile())
jeval = evaluate_jaimini(gchart, gjf, gvf)
birth_utc = datetime.fromisoformat(gchart.time.utc_datetime.replace('Z', '+00:00'))
evaluation_start = birth_utc
evaluation_end = birth_utc.replace(year=birth_utc.year + 10)

profile = JaiminiDashaProfile.from_method('CHARA_DASHA_LAGNA_START_MOVABLE_FIXED_DUAL')
dasha_result = calculate_jaimini_dasha(gchart, gjf, profile)
print('Dasha done')

timing = evaluate_jaimini_timing(
    chart_facts=gchart,
    jaimini_facts=gjf,
    jaimini_evaluation=jeval,
    dasha_result=dasha_result,
    evaluation_start=evaluation_start,
    evaluation_end=evaluation_end,
    calc_profile=DEFAULT_PROFILE,
)
print('Timing done:', timing.total_candidates)