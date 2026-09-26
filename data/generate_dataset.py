"""Reproducible fictional financial panel; Python standard library only."""
import csv, json, random, math, calendar, pathlib, shutil, collections

SEED = 20260919
OUT = pathlib.Path(__file__).resolve().parent / 'data'
OUT.mkdir(exist_ok=True)
rng = random.Random(SEED)
tables = collections.defaultdict(list)
def add(table, **row): tables[table].append(row)
def money(x): return round(x, 2)
categories = ['Food','Shopping','Travel','Education','Utilities','Healthcare','Entertainment','Insurance','Housing','Other']
descriptions = ['Groceries and meals','Clothing and household purchases','Commute and fuel','Tuition and course fees','Electricity and broadband','Clinic and medicines','Cinema and streaming','Health and term premiums','Rent and maintenance','Gifts and miscellaneous']
for i in range(1000):
    uid=f'U{i+1:04d}'; split='train' if i%10<7 else 'validation' if i%10<9 else 'test'
    age=rng.randint(22,60); risk=rng.choice(['low','medium','high']); job=rng.choice(['salaried','self_employed','freelance'])
    base=money(min(250000,max(15000,rng.lognormvariate(math.log(55000),.58))))
    growth=round(rng.uniform(.02,.12),6); inflation=round(rng.uniform(.03,.08),6)
    expbase=base*rng.uniform(.4,.9); cash=money(base*rng.uniform(.1,9)); inv=money(base*rng.uniform(0,24))
    mu={'low':.04,'medium':.07,'high':.10}[risk]; sigma={'low':.008,'medium':.025,'high':.045}[risk]; allocation={'low':.25,'medium':.5,'high':.7}[risk]
    add('users',user_id=uid,age_at_start=age,dependants=rng.randint(0,4),employment_type=job,risk_tolerance=risk,retirement_age=max(60,age+5),split=split,is_synthetic=True)
    add('assumptions',user_id=uid,annual_income_growth_rate=growth,annual_expense_growth_rate=inflation,annual_return_mean=mu,monthly_return_std=sigma,surplus_investment_fraction=allocation)
    loans=[]
    def snapshot(loan,date):
        add('debts',user_id=uid,as_of_date=date,debt_id=loan['id'],debt_type=loan['type'],balance_inr=loan['balance'],annual_interest_rate=loan['apr'],scheduled_payment_inr=loan['payment'])
    for j in range(rng.choice([0,0,1,1,2])):
        kind=rng.choice(['personal','education','credit_card']); rate={'personal':.15,'education':.09,'credit_card':.30}[kind]
        bal=money(base*rng.uniform(1,15)); n=rng.randint(18,84); rate_m=rate/12
        loan=dict(id=f'{uid}D{j+1}',type=kind,apr=rate,balance=bal,payment=money(bal*rate_m/(1-(1+rate_m)**(-n))))
        loans.append(loan);snapshot(loan,'2022-12-31')
    for typ,v in [('cash',cash),('investments',inv)]: add('assets',user_id=uid,as_of_date='2022-12-31',asset_type=typ,value_inr=v)
    weights=[rng.uniform(.5,1.5)*v for v in [.2,.08,.08,.07,.07,.06,.05,.06,.28,.05]]; weights=[v/sum(weights) for v in weights]
    panel=[]
    for t in range(36):
        year=2023+t//12;month=t%12+1;date=f'{year}-{month:02d}-{calendar.monthrange(year,month)[1]:02d}'
        oc=cash;oi=inv;od=money(sum(l['balance'] for l in loans))
        income=money(base*(1+growth)**(t/12)*max(.15,rng.gauss(1,.03 if job=='salaried' else .16)))
        if month==12: income=money(income*(1+rng.uniform(.1,.7)))
        expense=money(expbase*(1+inflation)**(t/12)*max(.55,rng.gauss(1,.12)))
        if rng.random()<.025: expense=money(expense+base*rng.uniform(.2,1))
        values=[money(expense*w) for w in weights[:-1]];values.append(money(expense-sum(values)))
        for cat,value,desc in zip(categories,values,descriptions):
            add('expense_records',record_id=f'E{len(tables['expense_records'])+1:07d}',user_id=uid,month_end=date,description=rng.choice(['Monthly ','Payment for ','Total for '])+desc,category=cat,amount_inr=value,record_grain='monthly_category_total',split=split)
        essential=money(sum(v for c,v in zip(categories,values) if c not in ['Shopping','Entertainment','Other']))
        interest=payment=0.
        for loan in loans:
            start=loan['balance'];charge=money(start*loan['apr']/12);paid=money(min(start+charge,loan['payment']));loan['balance']=money(start+charge-paid)
            interest+=charge;payment+=paid
            add('debt_schedule',user_id=uid,debt_id=loan['id'],month_end=date,opening_balance_inr=start,interest_inr=charge,payment_inr=paid,closing_balance_inr=loan['balance'])
        interest=money(interest);payment=money(payment);net=money(income-expense-payment)
        gain=money(inv*max(-.5,rng.gauss(mu/12,sigma))); inv=money(inv+gain)
        available=money(cash+net);withdrawal=borrowing=contribution=0.
        if available<0:
            withdrawal=money(min(inv,-available));inv=money(inv-withdrawal);available=money(available+withdrawal)
            if available<0:
                borrowing=money(-available);available=0.
                loan=dict(id=f'{uid}B{t+1:02d}',type='cash_shortfall',apr=.24,balance=borrowing,payment=money(borrowing*.06))
                loans.append(loan);snapshot(loan,date)
        else:
            contribution=money(max(0,net)*allocation);available=money(available-contribution);inv=money(inv+contribution)
        cash=available;debt=money(sum(l['balance'] for l in loans));assets=money(cash+inv)
        row=dict(user_id=uid,month_end=date,age=age+t//12,take_home_income_inr=income,living_expenses_inr=expense,essential_expenses_inr=essential,opening_cash_inr=oc,opening_investments_inr=oi,opening_debt_inr=od,debt_interest_inr=interest,debt_payment_inr=payment,net_cash_flow_inr=net,investment_gain_inr=gain,investment_contribution_inr=contribution,investment_withdrawal_inr=withdrawal,new_borrowing_inr=borrowing,cash_inr=cash,investments_inr=inv,total_assets_inr=assets,total_liabilities_inr=debt,net_worth_inr=money(assets-debt),emergency_target_inr=money(essential*6),emergency_gap_inr=money(max(0,essential*6-cash)),split=split)
        add('monthly_financials',**row);panel.append(row)
    for typ,v in [('cash',cash),('investments',inv)]:add('assets',user_id=uid,as_of_date='2025-12-31',asset_type=typ,value_inr=v)
    for loan in loans:
        # An origination in the final month is already the ending snapshot.
        if not any(x['debt_id']==loan['id'] and x['as_of_date']=='2025-12-31' for x in tables['debts'][-len(loans)-1:]): snapshot(loan,'2025-12-31')
    latest=dict(panel[-1]);latest.update(risk_tolerance=risk,employment_type=job,dependants=tables['users'][-1]['dependants']);add('wealth_planner_dataset',**latest)
    for j,kind in enumerate(['emergency_fund','education','home_deposit']):
        target=panel[-1]['emergency_target_inr'] if j==0 else money(base*rng.uniform(12,80))
        add('goals',goal_id=f'{uid}G{j+1}',user_id=uid,as_of_date='2025-12-31',goal_type=kind,target_amount_inr=target,target_date=f'{2026+j*3}-12-31',earmarked_amount_inr=money(cash*.2) if j==0 else money(inv*.1),priority=j+1)
    for t in range(24):
        row=panel[t];future=panel[t+12]
        feature={k:row[k] for k in ['user_id','month_end','age','take_home_income_inr','living_expenses_inr','essential_expenses_inr','debt_payment_inr','cash_inr','investments_inr','total_liabilities_inr','net_worth_inr','split']}
        feature.update(risk_tolerance=risk,employment_type=job,target_date=future['month_end'],simulated_net_worth_12m_inr=future['net_worth_inr'],simulated_change_12m_inr=money(future['net_worth_inr']-row['net_worth_inr']));add('ml_training_12m',**feature)

def close(a,b):return abs(a-b)<.031
expense_totals=collections.defaultdict(float)
for x in tables['expense_records']:expense_totals[x['user_id'],x['month_end']]+=x['amount_inr']
last={};users={x['user_id']:x for x in tables['users']}
for x in tables['monthly_financials']:
    assert close(expense_totals[x['user_id'],x['month_end']],x['living_expenses_inr'])
    assert close(x['net_worth_inr'],x['cash_inr']+x['investments_inr']-x['total_liabilities_inr'])
    assert close(x['cash_inr'],x['opening_cash_inr']+x['take_home_income_inr']-x['living_expenses_inr']-x['debt_payment_inr']-x['investment_contribution_inr']+x['investment_withdrawal_inr']+x['new_borrowing_inr'])
    assert close(x['investments_inr'],x['opening_investments_inr']+x['investment_gain_inr']+x['investment_contribution_inr']-x['investment_withdrawal_inr'])
    assert close(x['total_liabilities_inr'],x['opening_debt_inr']+x['debt_interest_inr']-x['debt_payment_inr']+x['new_borrowing_inr'])
    assert min(x['cash_inr'],x['investments_inr'],x['total_liabilities_inr'])>=0
    if x['user_id'] in last:
        old=last[x['user_id']]
        assert all(close(old[a],x[b]) for a,b in [('cash_inr','opening_cash_inr'),('investments_inr','opening_investments_inr'),('total_liabilities_inr','opening_debt_inr')])
    last[x['user_id']]=x
for rows in tables.values():
    for row in rows:
        assert row['user_id'] in users
        if 'split' in row:assert row['split']==users[row['user_id']]['split']
lookup={(x['user_id'],x['month_end']):x for x in tables['monthly_financials']}
assert len(lookup)==36000 and len(users)==1000
for x in tables['ml_training_12m']:assert x['simulated_net_worth_12m_inr']==lookup[x['user_id'],x['target_date']]['net_worth_inr']
assert len({(x['debt_id'],x['as_of_date']) for x in tables['debts']})==len(tables['debts'])

notes={
 'user_id':'Fictional user join key; never a predictive feature.',
 'age_at_start':'Age at 2023-01-01, years.', 'age':'Starting age plus complete calendar years elapsed; birthdays not modeled.',
 'split':'User-disjoint partition: 700 train / 200 validation / 100 test. Exclude from features.',
 'month_end':'ISO month-end date; flows cover that calendar month.',
 'as_of_date':'Snapshot date or debt origination date. Filter before summing snapshots.',
 'debt_id':'Loan key; debts contains origination and final snapshots. Join using key and date.',
 'description':'Templated text of a monthly category total, not a real bank narration.',
 'record_grain':'Monthly category total; no individual transaction timing.',
 'category':'Expense label; exclude from text-classifier features.',
 'risk_tolerance':'Random fictional preference: low / medium / high; not a validated risk assessment.',
 'target_date':'Future label date in ML table or goal deadline in goals table.',
 'simulated_net_worth_12m_inr':'Synthetic net worth exactly 12 months later; prediction target only.',
 'simulated_change_12m_inr':'Future minus current net worth; alternative target, never a feature for the other target.',
 'earmarked_amount_inr':'Subset of existing assets, not additional wealth; may exceed target.',
 'net_cash_flow_inr':'Take-home income minus living expenses and debt payments, before investment transfers.',
 'new_borrowing_inr':'End-month borrowing after using all cash and selling investments to cover shortfall.',
 'annual_return_mean':'Illustrative annual arithmetic mean; monthly simulation mean is this / 12.',
 'monthly_return_std':'Standard deviation of simulated monthly returns, decimal.',
 'surplus_investment_fraction':'Share of positive monthly cash flow transferred into investments.',
 'annual_income_growth_rate':'Annual income growth assumption, decimal.',
 'annual_expense_growth_rate':'Annual living-cost growth assumption, decimal.',
 'annual_interest_rate':'Nominal annual loan rate, decimal. Monthly interest = opening balance * rate / 12.',
 'emergency_target_inr':'Six times essential expenses.', 'emergency_gap_inr':'max(0, emergency target minus cash).',
 'essential_expenses_inr':'Living expenses excluding Shopping, Entertainment, Other.',
 'is_synthetic':'Always true; the entire package is synthetic.',
 'scheduled_payment_inr':'Fixed monthly scheduled loan payment; actual payment capped at balance plus interest.'}
dictionary=[]
for table,rows in tables.items():
    for col,value in rows[0].items():
        typ='boolean' if isinstance(value,bool) else 'integer' if isinstance(value,int) else 'number' if isinstance(value,float) else 'string'
        dictionary.append(dict(file=table+'.csv',column=col,data_type=typ,nullable=False,description=notes.get(col,col.replace('_',' ').capitalize()+('. Nominal INR.' if col.endswith('_inr') else '.'))))
for table,rows in [*tables.items(),('data_dictionary',dictionary)]:
    with (OUT/(table+'.csv')).open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
report=dict(status='passed',seed=SEED,row_counts={k:len(v) for k,v in tables.items()},checks=['foreign keys','unique user/month and debt/date keys','expense totals','cash/investment/debt rollforwards','net worth identity','nonnegative balances','monthly continuity','user-disjoint splits','12-month target joins'],negative_net_worth_months=sum(x['net_worth_inr']<0 for x in tables['monthly_financials']),cash_shortfall_months=sum(x['new_borrowing_inr']>0 for x in tables['monthly_financials']))
(OUT/'validation_report.json').write_text(json.dumps(report,indent=2))
(OUT/'preview.json').write_text(json.dumps(dict(counts=report['row_counts'],users=tables['users'],dictionary=dictionary)))
print(json.dumps(report,indent=2))
