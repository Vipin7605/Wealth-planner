import math
import numpy as np
import pytest
from backend.demo import demo_state
from backend.finance import summary
from backend.montecarlo import simulate, _growth_params
from backend.schemas import MonteCarloOptions, State
from backend.wellness import wellness


def plan(**fire):
    s = demo_state()
    s.fire.monthly_spending = 40000
    for k, v in fire.items():
        setattr(s.fire, k, v)
    return s


def opts(**kw):
    kw.setdefault('simulations', 1000)
    return MonteCarloOptions(**kw)


def test_growth_params_preserve_expected_annual_return():
    for r, vol in [(8, 12), (0, 20), (-5, 10), (12, 0)]:
        mean, sd = _growth_params(r, vol)
        assert math.exp(12 * (mean + sd**2 / 2)) == pytest.approx(1 + r / 100)


def test_zero_volatility_matches_deterministic_fire_engine():
    s = plan()
    deterministic = wellness(s, summary(s))['fire']['projected_corpus']
    r = simulate(s, opts(volatility=0))
    assert r['at_retirement']['p10'] == pytest.approx(deterministic, abs=0.01)
    assert r['at_retirement']['p90'] == pytest.approx(deterministic, abs=0.01)
    assert r['deterministic_at_retirement'] == pytest.approx(deterministic, abs=0.01)


def scalar_drawdown(s, end_age):
    """Independent, plain-Python reference for the zero-volatility case."""
    w = wellness(s, summary(s))['fire']
    p = s.profile
    balance = w['projected_corpus']
    spend = w['scenarios'][1]['monthly_spending']
    growth = (1 + p.investment_return / 100) ** (1 / 12)
    n = w['years'] * 12
    for k in range((end_age - p.age - w['years']) * 12):
        need = spend * (1 + p.inflation / 100) ** ((n + k) / 12)
        if balance < need - 1e-9:
            return p.age + w['years'] + (k + 1) / 12
        balance = (balance - need) * growth
    return None


@pytest.mark.parametrize('spending', [3000, 9000, 40000])
def test_zero_volatility_drawdown_matches_scalar_reference(spending):
    s = plan(monthly_spending=spending)
    r = simulate(s, opts(volatility=0))
    expected_failure_age = scalar_drawdown(s, 90)
    if expected_failure_age is None:
        assert r['survival_probability'] == 1.0 and r['median_depletion_age'] is None
    else:
        assert r['survival_probability'] == 0.0
        assert r['median_depletion_age'] == pytest.approx(expected_failure_age, abs=0.05)


def test_seeded_reproducibility_and_seed_sensitivity():
    s = plan()
    a, b = simulate(s, opts(seed=7)), simulate(s, opts(seed=7))
    assert a['timeline'] == b['timeline'] and a['survival_probability'] == b['survival_probability']
    assert simulate(s, opts(seed=8))['timeline'] != a['timeline']


def test_percentiles_are_ordered_and_timeline_shape():
    s = plan()
    r = simulate(s, opts(end_age=95))
    assert len(r['timeline']) == 95 - s.profile.age + 1
    for row in r['timeline']:
        assert row['p10'] <= row['p25'] <= row['p50'] <= row['p75'] <= row['p90']
    phases = [row['phase'] for row in r['timeline']]
    assert phases[0] == 'saving' and phases[-1] == 'retired'
    assert r['timeline'][0]['p50'] == r['timeline'][0]['p10'] == wellness(s, summary(s))['fire']['corpus']


def test_volatility_drag_and_spread():
    s = plan()
    calm, wild = simulate(s, opts(volatility=5)), simulate(s, opts(volatility=25))
    assert wild['at_retirement']['p50'] < calm['at_retirement']['p50'] < calm['deterministic_at_retirement'] * 1.01
    spread = lambda r: r['at_retirement']['p90'] - r['at_retirement']['p10']
    assert spread(wild) > 3 * spread(calm)


def test_lump_sum_median_matches_lognormal_theory():
    s = plan()
    s.portfolio.monthly_contribution = 0
    r = simulate(s, opts(simulations=5000, volatility=12))
    corpus = wellness(s, summary(s))['fire']['corpus']
    mean, _ = _growth_params(s.profile.investment_return, 12)
    months = (s.profile.retirement_age - s.profile.age) * 12
    assert r['at_retirement']['p50'] == pytest.approx(corpus * math.exp(months * mean), rel=0.05)


def test_more_spending_lowers_survival_and_more_saving_raises_reach():
    low, high = simulate(plan(monthly_spending=20000), opts()), simulate(plan(monthly_spending=60000), opts())
    assert high['survival_probability'] <= low['survival_probability']
    base = plan()
    more = plan()
    more.portfolio.monthly_contribution = 30000
    more.portfolio.reserve_contribution = more.portfolio.goal_contribution = more.portfolio.extra_debt_payment = 0
    assert simulate(more, opts())['reach_target_probability'] >= simulate(base, opts())['reach_target_probability']


def test_safe_spending_is_consistent_with_its_confidence_level():
    s = plan()
    r = simulate(s, opts())
    safe = r['safe_monthly_spending']
    assert safe > 0 and safe < r['planned_monthly_spending']
    at_safe = simulate(plan(monthly_spending=safe), opts())
    assert at_safe['survival_probability'] >= r['safe_confidence'] - 0.002
    above = simulate(plan(monthly_spending=safe * 1.08), opts())
    assert above['survival_probability'] < r['safe_confidence']


def test_lean_normal_fat_order_survival():
    s = plan(monthly_spending=15000)
    lean, normal, fat = (simulate(s, opts(scenario=k))['survival_probability'] for k in ['lean', 'normal', 'fat'])
    assert lean >= normal >= fat


def test_end_age_must_follow_retirement():
    with pytest.raises(ValueError):
        simulate(plan(), opts(end_age=60))


def test_degenerate_plans_do_not_crash():
    empty = simulate(State(), opts())
    assert empty['survival_probability'] == 1.0 and empty['warnings']
    broke = State()
    broke.fire.monthly_spending = 30000
    r = simulate(broke, opts())
    assert r['survival_probability'] == 0.0 and r['safe_monthly_spending'] == 0.0
    retired = plan()
    retired.profile.age, retired.profile.retirement_age = 70, 60
    r = simulate(retired, opts())
    assert r['timeline'][0]['phase'] == 'saving' and any('Retirement age has been reached' in w for w in r['warnings'])


def test_probabilities_are_bounded_and_finite():
    r = simulate(plan(), opts(volatility=40))
    for k in ['survival_probability', 'reach_target_probability']:
        assert 0 <= r[k] <= 1
    assert all(np.isfinite(v) for row in r['timeline'] for k, v in row.items() if k not in ('phase',))
