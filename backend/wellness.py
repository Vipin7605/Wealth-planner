"""Explainable academic heuristics; FIRE figures are adjustable scenarios."""
def health_score(s,income,expenses,payments,surplus,target):
    if not (s.income or s.expenses or s.assets or s.debts):
        return dict.fromkeys(['Cash flow','Emergency reserve','Debt burden','Protection','Investment habit'],0)
    reserve=sum(a.amount for a in s.assets if a.kind=='cash' and a.purpose=='emergency' and a.liquidity=='liquid')
    term_needed=s.profile.dependants>0 or any(d.amount>0 for d in s.debts)
    protection=10*int(s.protection.health_insurance=='yes' and s.protection.health_cover>0)
    protection+=10*int(not term_needed or (s.protection.term_insurance=='yes' and s.protection.term_cover>0))
    available=max(0,surplus-s.portfolio.reserve_contribution-s.portfolio.goal_contribution-s.portfolio.extra_debt_payment)
    contribution=min(s.portfolio.monthly_contribution,available)
    return {'Cash flow':round(25*max(0,min(1,surplus/income/.3))) if income else 0,
            'Emergency reserve':round(25*min(1,reserve/target)) if target else 0,
            'Debt burden':round(20*max(0,1-payments/income/.5)) if income else (20 if not any(d.amount for d in s.debts) else 0),
            'Protection':protection,
            'Investment habit':round(10*min(1,contribution/income/.15)) if income else 0}

def wellness(s,sm):
    p=s.profile;f=s.fire
    spending=f.monthly_spending if f.monthly_spending is not None else sm['expenses']+sm['payments']
    corpus=sum(a.amount for a in s.assets if a.purpose=='portfolio' and a.kind!='property')
    years=max(0,p.retirement_age-p.age)
    contribution=min(s.portfolio.monthly_contribution,max(0,sm['surplus']-s.portfolio.reserve_contribution-s.portfolio.goal_contribution-s.portfolio.extra_debt_payment))
    rate=(1+p.investment_return/100)**(1/12)-1;n=years*12
    future=corpus*(1+rate)**n+contribution*((1+rate)**n-1)/rate if abs(rate)>1e-12 else corpus+contribution*n
    available=max(0,sm['surplus']-s.portfolio.reserve_contribution-s.portfolio.goal_contribution-s.portfolio.extra_debt_payment)
    reserved=s.portfolio.reserve_contribution+s.portfolio.goal_contribution+s.portfolio.extra_debt_payment
    annuity=((1+rate)**n-1)/rate if abs(rate)>1e-12 else n
    scenarios=[]
    for name,multiplier in [('Lean FIRE',f.lean_multiplier),('Normal FIRE',1),('Fat FIRE',f.fat_multiplier)]:
        today=spending*12*multiplier/(f.withdrawal_rate/100);target=today*(1+p.inflation/100)**years
        required=max(0,(target-corpus*(1+rate)**n)/annuity) if n else (0 if corpus>=target else None)
        scenarios.append(dict(required_monthly=required,extra_monthly=max(0,required-contribution) if required is not None else None,name=name,multiplier=multiplier,monthly_spending=spending*multiplier,target_today=today,target_retirement=target,gap=max(0,target-future),progress=min(100,corpus/today*100) if today else None))
    timeline=[]
    for year in range(years+1):
        months=year*12
        growth=(1+rate)**months
        projected=corpus*growth+contribution*((growth-1)/rate if abs(rate)>1e-12 else months)
        timeline.append({'age':p.age+year,'corpus':round(projected,2),'target':round(scenarios[1]['target_today']*(1+p.inflation/100)**year,2)})
    warnings=[]
    if sm['surplus']<0:warnings.append('Monthly expenses exceed income. This accumulation scenario does not fund that shortfall.')
    if reserved>max(0,sm['surplus']):warnings.append('Your emergency, goal and extra-debt commitments exceed the monthly surplus.')
    if not spending:warnings.append('Enter a retirement spending budget to calculate a meaningful target.')
    if p.retirement_age<p.age:warnings.append('Target retirement age is in the past; calculations use your current age and existing investments.')
    if sum(g.saved for g in s.goals)>0:warnings.append('Check that savings earmarked for other goals are excluded from FIRE using the asset purpose field.')
    swot={'Strengths' :[],'Weaknesses':[],'Opportunities':[],'Threats':[]};actions=[]
    def action(priority,title,detail,page):actions.append(dict(priority=priority,title=title,detail=detail,page=page))
    if sm['income']<=0 or sm['expenses']<=0:action(1,'Complete your financial inputs','Add income and actual spending before interpreting the score or FIRE targets.','financials')
    if sm['surplus']>0:swot['Strengths'].append(f"Monthly surplus of ₹{sm['surplus']:,.0f} after expenses and EMIs.")
    else:
        swot['Weaknesses'].append('No positive monthly surplus.');action(1,'Balance your monthly budget','Review wants and essential commitments before allocating new investments.','financials')
    if sm['emergency_gap']>0:
        swot['Weaknesses'].append(f"Emergency reserve shortfall: ₹{sm['emergency_gap']:,.0f}.")
        action(2,'Build your emergency reserve',f"Target ₹{sm['emergency_target']:,.0f}; designate liquid cash assets as emergency funds. Contributions share your monthly surplus.",'financials')
    elif sm['emergency_target']>0:swot['Strengths'].append('Designated emergency cash meets your chosen target.')
    if any(d.apr>=18 and d.amount>0 for d in s.debts):
        swot['Threats'].append('Debt at 18% APR or above can slow wealth accumulation.');action(1,'Review high-interest debt','Compare avalanche and snowball repayment within your available budget.','debt')
    if s.protection.health_insurance!='yes' or s.protection.health_cover<=0:
        swot['Weaknesses'].append('Active health coverage has not been recorded.');action(1,'Review health protection','Record active cover and review exclusions, family coverage and affordability.','healthsetup')
    if (p.dependants or sm['liabilities']>0) and (s.protection.term_insurance!='yes' or s.protection.term_cover<=0):
        swot['Threats'].append('Dependants or debt obligations without recorded life/term protection.');action(1,'Review life/term protection','Assess income replacement and obligations; record active cover.','healthsetup')
    wants=sum(e.amount for e in s.expenses if not e.essential)
    if wants:swot['Opportunities'].append(f"Reducing wants by 10% could release ₹{wants*.1:,.0f}/month.")
    swot['Opportunities'].append('Compare Lean, Normal and Fat FIRE budgets against your affordable monthly contribution.')
    swot['Threats'].append('Inflation, market losses and changing family costs can alter FIRE outcomes.')
    action(3,'Review your FIRE plan','Compare lifestyle targets, retirement age and the affordable monthly contribution.','fire')
    unknown=[k for k in ['health_insurance','term_insurance'] if getattr(s.protection,k)=='unknown']
    return dict(score=sm['score'],factors=sm['score_factors'],provisional=bool(unknown or not s.income or not s.expenses),swot=swot,actions=sorted(actions,key=lambda x:x['priority']),fire=dict(timeline=timeline,warnings=warnings,available_monthly=available,reserved_monthly=reserved,unallocated_monthly=max(0,sm['surplus']-reserved-contribution),budget_deficit=max(0,reserved-sm['surplus']),scenarios=scenarios,corpus=corpus,years=years,projected_corpus=future,monthly_contribution=contribution,withdrawal_rate=f.withdrawal_rate),needs=sm['essential']+sm['payments'],wants=wants)
