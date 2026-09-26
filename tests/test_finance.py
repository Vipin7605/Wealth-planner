import pytest
from backend.schemas import State,Scenario
from backend.finance import summary,project,debt_plan
from backend.demo import demo_state

def test_demo_net_worth_and_cash_flow():
    sm=summary(demo_state())
    assert sm['net_worth']==743000
    assert sm['income']==97000
    assert sm['expenses']==46500
    assert sm['payments']==11000
    assert sm['surplus']==39500
    assert sum(sm['allocation'].values())==100

def test_zero_returns_contributions_and_real_values():
    s=State.model_validate({'profile':{'investment_return':0,'income_growth':0,'expense_growth':0,'inflation':0,'invest_surplus_pct':100},'income':[{'id':'1','name':'salary','amount':1000}]})
    p=project(s,Scenario(years=1));last=p['points'][-1]
    assert last['investments']==12000
    assert last['cash']==0
    assert last['net_worth']==12000
    assert last['real_net_worth']==12000

def test_no_money_created_by_investment_transfer():
    s=demo_state();s.profile.investment_return=0;s.profile.income_growth=0;s.profile.expense_growth=0
    s.profile.invest_surplus_pct=0;a=project(s,Scenario(years=1))
    s.profile.invest_surplus_pct=100;b=project(s,Scenario(years=1))
    assert a['points'][-1]['net_worth']==b['points'][-1]['net_worth']

def test_shortfall_is_visible_and_not_borrowed_silently():
    s=State.model_validate({'profile':{'expense_growth':0},'expenses':[{'id':'1','name':'rent','amount':1000}]})
    p=project(s,Scenario(years=1))
    assert p['unfunded']==12000
    assert not p['feasible']
    assert p['points'][-1]['debt']==0

def test_zero_interest_debt_payoff():
    s=State.model_validate({'income':[{'id':'i','name':'salary','amount':1000}],'debts':[{'id':'d','name':'loan','amount':1200,'apr':0,'payment':100}]})
    p=debt_plan(s,extra=0)
    assert p['months']==12
    assert p['interest']==0
    assert p['schedule'][-1]['balance']==0

def test_debt_negative_amortization():
    s=State.model_validate({'debts':[{'id':'d','name':'loan','amount':10000,'apr':12,'payment':0}]})
    p=debt_plan(s)
    assert p['months'] is None and not p['feasible']

def test_avalanche_cost_no_more_than_snowball():
    s=demo_state();s.debts[0].apr=30;s.debts[1].apr=9
    a=debt_plan(s,'avalanche',5000);b=debt_plan(s,'snowball',5000)
    assert a['interest']<=b['interest']

def test_extra_payment_clamped_to_surplus():
    s=demo_state();p=debt_plan(s,extra=1e8)
    assert p['extra']==summary(s)['surplus']

def test_goal_zero_return_and_overfunded():
    s=State.model_validate({'profile':{'investment_return':0},'goals':[{'id':'1','name':'Goal','amount':1200,'saved':0,'months':12},{'id':'2','name':'Covered','amount':100,'saved':200,'months':12}]})
    g=summary(s)['goals']
    assert g[0]['monthly_required']==100 and g[1]['monthly_required']==0

def test_inflation_discount():
    s=State.model_validate({'profile':{'inflation':10,'investment_return':0},'assets':[{'id':'1','name':'Cash','amount':11000,'kind':'cash'}]})
    p=project(s,Scenario(years=1))['points'][-1]
    assert p['net_worth']==11000 and p['real_net_worth']==10000

def test_validation_rejects_nonfinite_duplicate_and_negative():
    for values in [[{'id':'1','name':'bad','amount':float('nan')}],[{'id':'1','name':'bad','amount':-1}],[{'id':'1','name':'a','amount':0},{'id':'1','name':'b','amount':0}]]:
        with pytest.raises(ValueError):State.model_validate({'income':values})

def test_empty_plan_stable():
    s=State();sm=summary(s)
    assert sm['score']==0 and sm['net_worth']==0
    assert project(s)['feasible']
