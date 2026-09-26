import pytest
from backend.schemas import State
from backend.demo import demo_state
from backend.finance import summary
from backend.wellness import wellness

def test_empty_health():
    s=State();w=wellness(s,summary(s))
    assert w['score']==0 and w['provisional']
    assert w['fire']['scenarios'][0]['progress'] is None

def test_emergency_purpose_and_liquidity():
    s=demo_state();sm=summary(s)
    assert sm['emergency_reserve']==145000
    s.assets[0].purpose='near_term'
    assert summary(s)['emergency_reserve']==0
    s.assets[0].purpose='emergency';s.assets[0].liquidity='restricted'
    assert summary(s)['emergency_reserve']==0

def test_fire_targets_inflation_and_corpus():
    s=demo_state();s.fire.monthly_spending=40000;s.profile.inflation=0
    w=wellness(s,summary(s));rows=w['fire']['scenarios']
    assert rows[1]['target_today']==12000000
    assert rows[0]['target_today']==9000000
    assert rows[2]['target_today']==18000000
    assert w['fire']['corpus']==820000
    assert rows[1]['target_retirement']==12000000
    s.profile.inflation=5
    assert wellness(s,summary(s))['fire']['scenarios'][1]['target_retirement']==pytest.approx(12000000*1.05**32)

def test_protection_score_and_marital_neutrality():
    s=demo_state();before=summary(s)['score']
    s.protection.health_insurance='yes';s.protection.health_cover=500000
    s.protection.term_insurance='yes';s.protection.term_cover=10000000
    assert summary(s)['score']==before+20
    before=summary(s)['score'];s.profile.marital_status='married'
    assert summary(s)['score']==before

def test_emi_counted_once_and_investments_capped():
    s=demo_state();w=wellness(s,summary(s))
    assert w['needs']+w['wants']==46500+11000
    s.portfolio.monthly_contribution=1000000
    w=wellness(s,summary(s))
    assert w['fire']['monthly_contribution']==21500

def test_zero_return_and_zero_horizon():
    s=demo_state();s.profile.investment_return=0;s.profile.retirement_age=s.profile.age+1
    w=wellness(s,summary(s))
    assert w['fire']['projected_corpus']==820000+15000*12
    s.profile.retirement_age=18
    assert wellness(s,summary(s))['fire']['projected_corpus']==820000

def test_actions_order_and_score_range():
    s=demo_state();w=wellness(s,summary(s))
    assert [a['priority'] for a in w['actions']]==sorted(a['priority'] for a in w['actions'])
    assert 0<=w['score']<=100

def test_invalid_withdrawal_rate():
    with pytest.raises(ValueError):State.model_validate({'fire':{'withdrawal_rate':0}})

def test_required_contribution_reaches_future_target():
    s=demo_state();w=wellness(s,summary(s))['fire'];row=w['scenarios'][1]
    rate=(1+s.profile.investment_return/100)**(1/12)-1;n=w['years']*12
    result=w['corpus']*(1+rate)**n+row['required_monthly']*((1+rate)**n-1)/rate
    assert result==pytest.approx(row['target_retirement'])
    assert w['timeline'][-1]['corpus']==pytest.approx(w['projected_corpus'],abs=.01)
    assert w['timeline'][-1]['target']==pytest.approx(row['target_retirement'],abs=.01)

def test_required_zero_return_and_no_time():
    s=demo_state();s.profile.investment_return=0;s.profile.inflation=0;s.profile.retirement_age=s.profile.age+1
    w=wellness(s,summary(s))['fire'];row=w['scenarios'][1]
    assert row['required_monthly']==pytest.approx((row['target_today']-w['corpus'])/12)
    s.profile.retirement_age=s.profile.age
    assert wellness(s,summary(s))['fire']['scenarios'][1]['required_monthly'] is None

def test_fire_budget_ledger_and_overcommitment():
    s=demo_state();w=wellness(s,summary(s))['fire']
    assert w['unallocated_monthly']==6500 and w['budget_deficit']==0
    s.portfolio.reserve_contribution=100000
    w=wellness(s,summary(s))['fire']
    assert w['monthly_contribution']==0 and w['budget_deficit']>0
    assert any('commitments exceed' in x for x in w['warnings'])
