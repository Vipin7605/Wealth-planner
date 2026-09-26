import pytest
from backend.schemas import State,Asset,Targets
from backend.demo import demo_state
from backend.portfolio import allocation,targets

def test_presets_sum_and_horizon():
    s=demo_state()
    for risk in ['low','medium','high']:
        s.profile.risk=risk
        for years in [1,3,4,7,8,30]:
            s.portfolio.horizon_years=years
            assert sum(targets(s).values())==100
            if years<=3:assert targets(s)['domestic_equity']==0

def test_legacy_defaults_and_unclassified_block():
    s=State.model_validate({'assets':[{'id':'1','name':'Old investment','amount':100,'kind':'investment'}]})
    p=allocation(s)
    assert p['unclassified']==100 and not p['can_plan']
    assert all(r['rebalance_delta'] is None for r in p['rows'])

def test_designated_reserves_excluded_without_changing_net_worth():
    s=demo_state();p=allocation(s)
    assert p['portfolio_value']==820000 and p['excluded_value']==145000
    assert p['emergency_designated_cash']==145000
    assert sum(r['current'] for r in p['rows'])==820000

def test_cash_flow_cap_and_no_double_count_of_minimums():
    s=demo_state();s.portfolio.monthly_contribution=999999
    p=allocation(s)
    assert p['monthly_surplus']==39500
    assert p['available_monthly']==21500
    assert p['allocated_monthly']==21500
    assert sum(r['contribution'] for r in p['rows'])==pytest.approx(21500)
    assert sum(r['after_pct'] for r in p['rows'])==pytest.approx(100,abs=.04)

def test_oversubscribed_budget_zero():
    s=demo_state();s.portfolio.reserve_contribution=999999
    p=allocation(s);assert p['contribution_budget']==0 and p['allocated_monthly']==0

def test_zero_portfolio_can_allocate_new_money():
    s=State.model_validate({'income':[{'id':'i','name':'Salary','amount':10000}]})
    p=allocation(s);assert p['can_plan'] and p['allocated_monthly']==10000
    assert p['portfolio_value']==0

def test_invalid_targets_and_inconsistent_metadata():
    with pytest.raises(ValueError):Targets(domestic_equity=90)
    with pytest.raises(ValueError):Asset(id='a',name='Cash',amount=5,kind='cash',asset_class='gold')

def test_unknown_tag_visible_and_normalized():
    s=demo_state();s.assets[1].issuer='DEMO BANK';s.assets[2].issuer=' demo bank '
    p=allocation(s);group=next(x for x in p['breakdowns']['issuer'] if x['name']=='Demo Bank')
    assert group['value']==550000

def test_rebalance_gaps_net_zero_and_buy_only():
    p=allocation(demo_state())
    assert sum(r['rebalance_delta'] for r in p['rows'])==pytest.approx(0,abs=.03)
    assert all(r['contribution']>=0 for r in p['rows'])

def test_paise_budget_preserved():
    s=demo_state();s.portfolio.monthly_contribution=.01
    p=allocation(s);assert sum(r['contribution'] for r in p['rows'])==.01

def test_no_double_count_of_purpose():
    s=demo_state();s.assets[1].purpose='near_term'
    p=allocation(s);assert p['portfolio_value']==470000 and p['excluded_value']==495000

def test_fire_preview_and_export_isolation():
    from fastapi.testclient import TestClient
    from backend.main import app
    with TestClient(app) as c:
        assert c.post('/api/fire-preview',json={}).status_code==401
        assert c.get('/api/portfolio').status_code==404
        c.post('/api/demo',json={});original=c.get('/api/state').json()
        changed=original['state'].copy();changed['fire']={**changed['fire'],'monthly_spending':40000}
        r=c.post('/api/fire-preview',json=changed)
        assert r.status_code==200 and r.json()['fire']['scenarios'][1]['target_today']==12000000
        assert c.get('/api/state').json()==original
        assert 'target_retirement' in c.get('/api/export?kind=fire').text
        bad=original['state'].copy();bad['fire']={**bad['fire'],'withdrawal_rate':0}
        assert c.post('/api/fire-preview',json=bad).status_code==422
