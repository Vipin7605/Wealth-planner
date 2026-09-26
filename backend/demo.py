from .schemas import State
def demo_state():
    return State.model_validate({
      'profile':{'name':'Alex’s wealth plan','age':28,'dependants':1},
      'income':[{'id':'i1','name':'Monthly take-home salary','amount':85000},{'id':'i2','name':'Freelance income','amount':12000}],
      'expenses':[{'id':f'e{i}','name':n,'amount':a,'category':c,'essential':e} for i,(n,a,c,e) in enumerate([
        ('Rent & maintenance',18000,'Housing',True),('Groceries & meals',9000,'Food',True),('Commute',3500,'Travel',True),('Electricity & internet',3000,'Utilities',True),('Insurance premiums',2500,'Insurance',True),('Healthcare',1500,'Healthcare',True),('Courses',2000,'Education',True),('Shopping',4000,'Shopping',False),('Entertainment',3000,'Entertainment',False)])],
      'assets':[
        {'id':'a1','name':'Emergency savings','amount':145000,'kind':'cash','asset_class':'cash','purpose':'emergency','issuer':'Demo Bank','geography':'India','vehicle':'deposit'},
        {'id':'a2','name':'Indian broad-market fund','amount':350000,'kind':'investment','asset_class':'domestic_equity','sector':'Broad market','issuer':'Demo Fund House A','geography':'India','vehicle':'diversified_fund'},
        {'id':'a3','name':'Fixed deposits','amount':200000,'kind':'investment','asset_class':'bonds','issuer':'Demo Bank','sector':'Deposits','geography':'India','vehicle':'deposit','liquidity':'restricted'},
        {'id':'a4','name':'International equity fund','amount':120000,'kind':'investment','asset_class':'international_equity','sector':'Broad market','issuer':'Demo Fund House B','geography':'International','vehicle':'diversified_fund'},
        {'id':'a5','name':'Gold holding','amount':80000,'kind':'investment','asset_class':'gold','sector':'Precious metals','issuer':'Demo Gold Provider','geography':'Global','vehicle':'physical'},
        {'id':'a6','name':'Technology share','amount':70000,'kind':'investment','asset_class':'domestic_equity','sector':'Technology','issuer':'Demo Technology Co','geography':'India','vehicle':'single_security'}
      ],
      'portfolio':{'monthly_contribution':15000,'reserve_contribution':5000,'goal_contribution':10000,'extra_debt_payment':3000},
      'debts':[{'id':'d1','name':'Education loan','amount':180000,'apr':9,'payment':6500},{'id':'d2','name':'Credit card balance','amount':42000,'apr':30,'payment':4500}],
      'goals':[{'id':'g1','name':'Home down payment','amount':1800000,'saved':300000,'months':60},{'id':'g2','name':'Travel fund','amount':150000,'saved':35000,'months':18},{'id':'g3','name':'Higher education','amount':500000,'saved':100000,'months':36}]
    })
