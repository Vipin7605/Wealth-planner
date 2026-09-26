"""Deterministic planning mathematics. No market data or guaranteed returns."""
from .schemas import State, Scenario
import math

def total(items):return sum(x.amount for x in items)
def summary(s:State):
    income=total(s.income);expenses=total(s.expenses)
    payments=sum(min(d.payment,d.amount*(1+d.apr/1200)) for d in s.debts)
    cash=sum(a.amount for a in s.assets if a.kind=='cash')
    investments=sum(a.amount for a in s.assets if a.kind=='investment')
    essential=sum(e.amount for e in s.expenses if e.essential)
    assets=total(s.assets);liabilities=total(s.debts);surplus=income-expenses-payments
    target=(essential+payments)*s.profile.emergency_months
    reserve=sum(a.amount for a in s.assets if a.purpose=='emergency' and a.liquidity=='liquid' and a.kind=='cash')
    gap=max(0,target-reserve);savings_rate=surplus/income if income else 0
    from .wellness import health_score
    factors=health_score(s,income,expenses,payments,surplus,target)
    score=sum(factors.values())
    from .portfolio import targets, LABELS
    allocation={LABELS[k]:v for k,v in targets(s).items()}
    r=(1+s.profile.investment_return/100)**(1/12)-1
    goals=[]
    for g in s.goals:
        future_saved=g.saved*(1+r)**g.months
        need=max(0,g.amount-future_saved)
        monthly=need/g.months if abs(r)<1e-12 else need*r/((1+r)**g.months-1)
        goals.append({'id':g.id,'name':g.name,'target':g.amount,'saved':g.saved,'months':g.months,'progress':min(100,g.saved/g.amount*100) if g.amount else 100,'monthly_required':round(monthly,2)})
    contributions=sum(g['monthly_required'] for g in goals)
    insights=[]
    if surplus<0:insights.append({'tone':'warning','title':'Your monthly plan has a shortfall','body':f'Expenses and loan payments exceed income by ₹{abs(surplus):,.0f}. Reduce commitments before adding investments.'})
    elif income:insights.append({'tone':'good','title':'Put your monthly surplus to work','body':f'₹{surplus:,.0f} remains after living expenses and scheduled debt payments.'})
    if gap:insights.append({'tone':'warning','title':'Build your emergency cushion','body':f'Add ₹{gap:,.0f} to reach {s.profile.emergency_months} months of essential expenses and debt payments.'})
    costly=[d for d in s.debts if d.apr>=18 and d.amount>0]
    if costly:insights.append({'tone':'warning','title':'Review expensive debt first','body':f'{max(costly,key=lambda d:d.apr).name} has the highest rate among debts at or above 18%. Compare repayment strategies.'})
    if contributions>max(0,surplus):insights.append({'tone':'warning','title':'Your goals compete for the same budget','body':f'Combined goal contributions exceed your available surplus by ₹{contributions-max(0,surplus):,.0f}. Adjust targets or deadlines.'})
    if sum(g.saved for g in s.goals)>assets:insights.append({'tone':'warning','title':'Review goal earmarks','body':'Goal savings exceed total assets. Earmarks must be subsets of assets, not additional wealth.'})
    return dict(income=income,expenses=expenses,payments=payments,surplus=surplus,cash=cash,investments=investments,assets=assets,liabilities=liabilities,net_worth=assets-liabilities,savings_rate=savings_rate*100,essential=essential,emergency_target=target,emergency_gap=gap,emergency_reserve=reserve,emergency_months_covered=reserve/(essential+payments) if essential+payments else None,score=score,score_factors=factors,allocation=allocation,goals=goals,goal_contributions=contributions,insights=insights)

def project(s:State,scenario:Scenario|None=None):
    scenario=scenario or Scenario();p=s.profile;sm=summary(s)
    cash=sm['cash'];inv=sm['investments'];prop=sum(a.amount for a in s.assets if a.kind=='property')
    debts=[{'balance':d.amount,'payment':d.payment,'rate':d.apr/1200} for d in s.debts]
    income=sm['income']+scenario.extra_income;expense=sm['expenses']*(1-scenario.expense_reduction/100)
    ig=(1+(scenario.income_growth if scenario.income_growth is not None else p.income_growth)/100)**(1/12)
    eg=(1+p.expense_growth/100)**(1/12)
    ret=(1+(scenario.investment_return if scenario.investment_return is not None else p.investment_return)/100)**(1/12)-1
    gap=0;points=[];interest_total=0
    def point(m):
        liability=sum(d['balance'] for d in debts);nw=cash+inv+prop-liability
        return {'year':m//12,'net_worth':round(nw,2),'real_net_worth':round(nw/(1+p.inflation/100)**(m/12),2),'cash':round(cash,2),'investments':round(inv,2),'debt':round(liability,2),'cumulative_unfunded':round(gap,2)}
    points.append(point(0))
    for m in range(1,scenario.years*12+1):
        inv*=1+ret;paid=0
        for debt in debts:
            charge=debt['balance']*debt['rate'];interest_total+=charge
            payment=min(debt['balance']+charge,debt['payment']);debt['balance']+=charge-payment;paid+=payment
        net=income-expense-paid
        if net>=0:
            contribution=net*p.invest_surplus_pct/100;inv+=contribution;cash+=net-contribution
        else:
            required=-net;use=min(cash,required);cash-=use;required-=use
            use=min(inv,required);inv-=use;required-=use;gap+=required
        if m%12==0:points.append(point(m))
        income*=ig;expense*=eg
    return {'points':points,'unfunded':round(gap,2),'feasible':gap<.01,'interest_paid':round(interest_total,2),'assumptions':{'years':scenario.years,'return_pct':scenario.investment_return if scenario.investment_return is not None else p.investment_return,'inflation_pct':p.inflation,'income_growth_pct':scenario.income_growth if scenario.income_growth is not None else p.income_growth,'expense_growth_pct':p.expense_growth,'contribution_pct':p.invest_surplus_pct},'note':'End-of-month contributions; property value fixed; no taxes, fees, retirement income change or market volatility. Unfunded spending is reported separately; infeasible paths are not achievable forecasts.'}

def debt_plan(s:State,strategy='avalanche',extra=0):
    balances=[{'id':d.id,'name':d.name,'balance':d.amount,'apr':d.apr,'minimum':d.payment} for d in s.debts if d.amount>0]
    sm=summary(s);extra=min(max(0,extra),max(0,sm['surplus']))
    budget=sum(d['minimum'] for d in balances)+extra
    if not balances:return {'months':0,'interest':0,'schedule':[],'payoff_order':[],'extra':extra,'feasible':True}
    timeline=[];order=[];interest=0
    for month in range(1,601):
        for d in balances:
            charge=d['balance']*d['apr']/1200;d['balance']+=charge;interest+=charge
        remaining=budget
        for d in balances:
            pay=min(d['balance'],d['minimum'],remaining);d['balance']-=pay;remaining-=pay
        ordered=sorted(balances,key=lambda x:(-x['apr'],x['balance']) if strategy=='avalanche' else (x['balance'],-x['apr']))
        for d in ordered:
            pay=min(d['balance'],remaining);d['balance']-=pay;remaining-=pay
        for d in balances:
            if d['balance']<.005 and d['id'] not in [p['id'] for p in order]:order.append({'id':d['id'],'name':d['name'],'month':month})
        balance=sum(d['balance'] for d in balances);timeline.append({'month':month,'balance':round(balance,2),'interest_to_date':round(interest,2)})
        if balance<.005:return {'months':month,'interest':round(interest,2),'schedule':timeline,'payoff_order':order,'extra':extra,'feasible':sm['surplus']>=0}
    return {'months':None,'interest':round(interest,2),'schedule':timeline,'payoff_order':order,'extra':extra,'feasible':False,'warning':'Not repaid within 50 years at this budget. Payments may not cover interest.'}

def advisor(s:State,question:str):
    sm=summary(s);q=question.lower();fmt=lambda x:f'₹{x:,.0f}'
    if 'fire' in q:
        from .wellness import wellness
        w=wellness(s,sm)['fire'];normal=w['scenarios'][1]
        extra=''
        try:
            from .montecarlo import simulate
            from .schemas import MonteCarloOptions
            mc=simulate(s,MonteCarloOptions(simulations=1000))
            extra=f" Allowing for market volatility (1,000 simulated paths), there is roughly a {mc['survival_probability']:.0%} chance your investments last to age {mc['assumptions']['end_age']} at your planned spending, and a {mc['reach_target_probability']:.0%} chance of reaching the target by retirement."
        except ValueError:pass
        return {'answer':f"Your Normal FIRE target is {fmt(normal['target_today'])} in today's money using an illustrative {w['withdrawal_rate']}% withdrawal rate. Your eligible portfolio is {fmt(w['corpus'])}.{extra} Adjust lifestyle spending and assumptions on the FIRE planner. This is a scenario, not a guarantee of retirement readiness.",'mode':'rule_based','label':'Calculation-based FIRE guide'}
    if any(x in q for x in ['emergency','reserve','cushion']):
        text=f"Your emergency target is {fmt(sm['emergency_target'])}, including essential living expenses and scheduled debt payments for {s.profile.emergency_months} months. You hold {fmt(sm['emergency_reserve'])} in designated liquid emergency cash, leaving a gap of {fmt(sm['emergency_gap'])}."
    elif any(x in q for x in ['debt','loan','credit']):
        d=debt_plan(s,extra=max(0,sm['surplus'])*.25)
        text=f"You owe {fmt(sm['liabilities'])}, with scheduled monthly payments of {fmt(sm['payments'])}. An avalanche plan adding {fmt(d['extra'])} per month " + (f"would take approximately {d['months']} months and incur {fmt(d['interest'])} in interest." if d['months'] is not None else 'does not repay all balances within 50 years. Review the payment budget.')
    elif any(x in q for x in ['spend','expense','saving','save']):
        discretionary=sum(e.amount for e in s.expenses if not e.essential)
        text=f"Living expenses total {fmt(sm['expenses'])} per month; {fmt(discretionary)} is marked non-essential. A 10% reduction in that spending releases {fmt(discretionary*.1)} monthly. Your current surplus after debt payments is {fmt(sm['surplus'])}."
    elif any(x in q for x in ['house','home','goal','invest monthly']):
        text=f"Your saved goals require a combined {fmt(sm['goal_contributions'])} per month under the assumed {s.profile.investment_return}% return. Available monthly surplus is {fmt(sm['surplus'])}. Goal savings must be earmarked from existing assets, and contributions share one budget."
    elif any(x in q for x in ['retir','future','worth','wealth']):
        years=min(30,max(1,s.profile.retirement_age-s.profile.age));pr=project(s,Scenario(years=years));last=pr['points'][-1]
        text=f"Over {years} years, the assumption-based projection ends at {fmt(last['net_worth'])}, or {fmt(last['real_net_worth'])} in today's money. This does not model a change in income at retirement. " + ('There is an unfunded cash-flow shortfall; revise this scenario before relying on it.' if not pr['feasible'] else 'This is a scenario, not a guaranteed outcome or retirement-readiness assessment.')
    else:text=f"Your net worth is {fmt(sm['net_worth'])} and monthly surplus is {fmt(sm['surplus'])}. I can explain emergency reserves, spending, debts, goals and wealth projections. Ask about one of these to get calculations from your saved plan."
    return {'answer':text,'mode':'rule_based','label':'Calculation-based guide'}
