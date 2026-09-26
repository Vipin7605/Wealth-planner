"""Educational allocation policy; no return optimization or trade execution."""
from collections import defaultdict
from .finance import summary

LABELS={'domestic_equity':'Indian equity','international_equity':'International equity','bonds':'Bonds & deposits','gold':'Gold','real_estate':'Real estate','cash':'Cash','alternatives':'Alternatives'}
def targets(s):
    if s.portfolio.mode=='custom':return s.portfolio.targets.model_dump()
    risk=s.profile.risk;years=s.portfolio.horizon_years
    # Deliberately simple illustrative policy. Horizon overrides are explicit.
    weights={'low':[15,5,55,10,0,15,0],'medium':[40,10,30,10,0,10,0],'high':[55,15,15,10,0,5,0]}[risk]
    if years<=3:weights=[0,0,35,0,0,65,0]
    elif years<=7:
        weights={'low':[10,5,55,10,0,20,0],'medium':[25,10,45,10,0,10,0],'high':[35,10,35,10,0,10,0]}[risk]
    return dict(zip(LABELS,weights))

def classify(a):
    if a.asset_class!='unclassified':return a.asset_class
    return {'cash':'cash','property':'real_estate'}.get(a.kind,'unclassified')

def allocation(s):
    sm=summary(s);plan=s.portfolio;t=targets(s)
    included=[a for a in s.assets if a.purpose=='portfolio' and a.amount>0]
    portfolio=sum(a.amount for a in included);excluded=sum(a.amount for a in s.assets if a.purpose!='portfolio')
    current=defaultdict(float)
    for a in included:current[classify(a)]+=a.amount
    unknown=current['unclassified'];can_plan=unknown<.005
    reserve_cash=sum(a.amount for a in s.assets if a.purpose=='emergency' and a.kind=='cash' and a.liquidity=='liquid')
    reserve_gap=max(0,sm['emergency_target']-reserve_cash)
    reserved=plan.reserve_contribution+plan.goal_contribution+plan.extra_debt_payment
    available=max(0,sm['surplus']-reserved)
    contribution=round(min(plan.monthly_contribution,available),2)
    desired={k:t[k]/100*(portfolio+contribution) for k in LABELS}
    deficits={k:max(0,desired[k]-current[k]) for k in LABELS}
    denom=sum(deficits.values());buys={k:0. for k in LABELS}
    if can_plan and contribution and denom:
        # Integer paise + largest remainder: allocate exactly the capped budget.
        cents=round(contribution*100);raw={k:cents*deficits[k]/denom for k in LABELS}
        counts={k:int(v) for k,v in raw.items()}
        for k in sorted(raw,key=lambda k:raw[k]-counts[k],reverse=True)[:cents-sum(counts.values())]:counts[k]+=1
        buys={k:v/100 for k,v in counts.items()}
    rows=[]
    for k,label in LABELS.items():
        value=current[k];weight=100*value/portfolio if portfolio else 0;target=portfolio*t[k]/100
        rows.append({'key':k,'label':label,'current':round(value,2),'current_pct':round(weight,2),'target_pct':t[k],'target_value':round(target,2),'drift_pp':round(weight-t[k],2),'rebalance_delta':round(target-value,2) if can_plan else None,'contribution':buys[k] if can_plan else None,'after_pct':round(100*(value+buys[k])/(portfolio+contribution),2) if can_plan and portfolio+contribution else 0,'needs_review':bool(portfolio and abs(weight-t[k])>=plan.drift_threshold)})
    alerts=[]
    if not included:alerts.append('No assets are marked for this portfolio. You can still plan new contributions.')
    if unknown:alerts.append(f'Classify ₹{unknown:,.0f} of investment holdings before using rebalancing or contribution suggestions.')
    if reserve_gap:alerts.append(f'Your designated emergency cash is ₹{reserve_gap:,.0f} below its target. The portfolio excludes emergency-designated assets, not automatically all cash.')
    if any(d.apr>=18 and d.amount>0 for d in s.debts):alerts.append('Review debt at or above the illustrative 18% APR threshold before increasing investment contributions.')
    if reserved>max(0,sm['surplus']):alerts.append('Reserved monthly commitments exceed available surplus; portfolio contributions are capped at zero.')
    if plan.monthly_contribution>available:alerts.append('Requested investing exceeds the remaining monthly surplus. The contribution plan uses the capped amount.')
    if plan.goal_contribution+.01<sm['goal_contributions']:alerts.append('Reserved goal funding is below the combined requirement from your Goals page. Reconcile these competing uses of surplus.')
    if plan.horizon_years<=3 and t['domestic_equity']+t['international_equity']+t['alternatives']>0:alerts.append('Your custom short-horizon target includes equity or alternatives. Consider the consequences of losses before the deadline.')
    if any(g.months<=36 and g.saved>0 for g in s.goals):alerts.append('You have a goal due within three years. Tag the assets earmarked for it as near-term so they are excluded from this portfolio.')
    # Tagged groups are not fund look-through data. Unknowns retain their weight.
    breakdowns={}
    for field in ['issuer','sector','geography','liquidity']:
        grouped=defaultdict(float)
        for a in included:
            key=getattr(a,field).strip() or 'Unknown'
            grouped[key.casefold()]+=a.amount
        breakdowns[field]=[{'name':k.title(),'value':round(v,2),'pct':round(v/portfolio*100,2) if portfolio else 0} for k,v in sorted(grouped.items(),key=lambda x:-x[1])]
    holdings=[{'id':a.id,'name':a.name,'amount':a.amount,'weight':round(a.amount/portfolio*100,2),'class':LABELS.get(classify(a),'Unclassified'),'vehicle':a.vehicle,'above_limit':a.amount/portfolio*100>plan.holding_limit,'liquidity':a.liquidity} for a in sorted(included,key=lambda x:-x.amount)]
    if any(h['above_limit'] for h in holdings):alerts.append(f'One or more holding rows exceed your {plan.holding_limit:g}% review threshold. A broad fund is different from a single security; inspect its underlying exposures.')
    issuer=next((x for x in breakdowns['issuer'] if x['name']!='Unknown' and x['pct']>plan.holding_limit),None)
    if issuer:alerts.append(f'{issuer["name"]} represents {issuer["pct"]:g}% by your issuer/provider tags. Verify whether this represents a true common counterparty or just a fund manager.')
    locked=sum(a.amount for a in included if a.liquidity!='liquid')
    if locked:alerts.append(f'₹{locked:,.0f} is tagged restricted or illiquid. Target gaps are not executable trade instructions.')
    if not can_plan:buys={k:0 for k in LABELS}
    return {'rows':rows,'holdings':holdings,'breakdowns':breakdowns,'portfolio_value':round(portfolio,2),'excluded_value':round(excluded,2),'unclassified':round(unknown,2),'classified_pct':round((portfolio-unknown)/portfolio*100,2) if portfolio else 0,'class_count':sum(current[k]>.005 for k in LABELS),'largest_holding_pct':holdings[0]['weight'] if holdings else 0,'top_three_pct':round(sum(h['amount'] for h in holdings[:3])/portfolio*100,2) if portfolio else 0,'can_plan':can_plan,'monthly_surplus':sm['surplus'],'reserved_monthly':reserved,'available_monthly':available,'requested_monthly':plan.monthly_contribution,'contribution_budget':contribution,'allocated_monthly':round(sum(buys.values()),2),'unallocated_monthly':round(contribution-sum(buys.values()),2),'emergency_designated_cash':reserve_cash,'emergency_gap':reserve_gap,'illiquid_value':locked,'alerts':alerts,'target_mode':plan.mode,'horizon_years':plan.horizon_years,'risk':s.profile.risk,'method':'Illustrative policy, not an optimized or personalized investment recommendation. Class gaps assume unchanged prices and no taxes, fees, lot sizes or trading restrictions. Contributions are allocated in proportion to positive target-value gaps after adding the new money. Metadata groups are user tags, not underlying fund holdings.'}
