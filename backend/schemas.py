from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator
import math

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid', allow_inf_nan=False)

class Profile(Strict):
    name: str=Field(default='My plan',min_length=1,max_length=80)
    age: int=Field(default=28,ge=18,le=90)
    dependants: int=Field(default=0,ge=0,le=20)
    risk: Literal['low','medium','high']='medium'
    employment: Literal['salaried','self_employed','freelance']='salaried'
    marital_status: Literal['not_specified','single','married','divorced','widowed']='not_specified'
    retirement_age: int=Field(default=60,ge=18,le=100)
    income_growth: float=Field(default=6,ge=-10,le=30)
    expense_growth: float=Field(default=5,ge=0,le=20)
    investment_return: float=Field(default=8,ge=-20,le=25)
    inflation: float=Field(default=5,ge=0,le=20)
    invest_surplus_pct: float=Field(default=65,ge=0,le=100)
    emergency_months: int=Field(default=6,ge=1,le=24)

class Item(Strict):
    id: str=Field(min_length=1,max_length=80)
    name: str=Field(min_length=1,max_length=100)
    amount: float=Field(ge=0,le=1e10)
class Expense(Item):
    category: Literal['Food','Shopping','Travel','Education','Utilities','Healthcare','Entertainment','Insurance','Housing','Other']='Other'
    essential: bool=True
class Asset(Item):
    kind: Literal['cash','investment','property']='cash'
    asset_class: Literal['unclassified','domestic_equity','international_equity','bonds','gold','real_estate','cash','alternatives']='unclassified'
    purpose: Literal['portfolio','emergency','near_term','personal']='portfolio'
    issuer: str=Field(default='Unknown',min_length=1,max_length=100)
    sector: str=Field(default='Unknown',min_length=1,max_length=100)
    geography: Literal['Unknown','India','International','Global']='Unknown'
    vehicle: Literal['unknown','single_security','diversified_fund','deposit','physical']='unknown'
    liquidity: Literal['liquid','restricted','illiquid']='liquid'
    @model_validator(mode='after')
    def consistent_class(self):
        if self.kind=='cash' and self.asset_class not in ['unclassified','cash']:raise ValueError('Cash assets must use the cash class')
        if self.kind=='property' and self.asset_class not in ['unclassified','real_estate']:raise ValueError('Property must use the real estate class')
        if self.kind=='investment' and self.asset_class=='cash':raise ValueError('Use cash type for the cash class')
        return self
class Targets(Strict):
    domestic_equity: float=Field(default=40,ge=0,le=100)
    international_equity: float=Field(default=10,ge=0,le=100)
    bonds: float=Field(default=30,ge=0,le=100)
    gold: float=Field(default=10,ge=0,le=100)
    real_estate: float=Field(default=0,ge=0,le=100)
    cash: float=Field(default=10,ge=0,le=100)
    alternatives: float=Field(default=0,ge=0,le=100)
    @model_validator(mode='after')
    def sums_to_100(self):
        if abs(sum(self.model_dump().values())-100)>.001:raise ValueError('Allocation targets must total 100%')
        return self
class PortfolioPlan(Strict):
    mode: Literal['preset','custom']='preset'
    horizon_years: int=Field(default=10,ge=1,le=40)
    targets: Targets=Field(default_factory=Targets)
    monthly_contribution: float=Field(default=10000,ge=0,le=1e9)
    reserve_contribution: float=Field(default=0,ge=0,le=1e9)
    goal_contribution: float=Field(default=0,ge=0,le=1e9)
    extra_debt_payment: float=Field(default=0,ge=0,le=1e9)
    drift_threshold: float=Field(default=5,ge=1,le=25)
    holding_limit: float=Field(default=20,ge=5,le=100)
class Debt(Item):
    apr: float=Field(default=12,ge=0,le=60)
    payment: float=Field(default=1000,ge=0,le=1e9)
class Goal(Item):
    saved: float=Field(default=0,ge=0,le=1e10)
    months: int=Field(default=36,ge=1,le=600)
class Protection(Strict):
    health_insurance: Literal['unknown','yes','no']='unknown'
    health_cover: float=Field(default=0,ge=0,le=1e10)
    term_insurance: Literal['unknown','yes','no']='unknown'
    term_cover: float=Field(default=0,ge=0,le=1e10)
class FirePlan(Strict):
    monthly_spending: float|None=Field(default=None,ge=0,le=1e9)
    withdrawal_rate: float=Field(default=4,ge=1,le=10)
    lean_multiplier: float=Field(default=.75,ge=.3,le=1)
    fat_multiplier: float=Field(default=1.5,ge=1,le=4)
class State(Strict):
    protection: Protection=Field(default_factory=Protection)
    fire: FirePlan=Field(default_factory=FirePlan)
    profile: Profile=Field(default_factory=Profile)
    income: list[Item]=Field(default_factory=list,max_length=100)
    expenses: list[Expense]=Field(default_factory=list,max_length=200)
    assets: list[Asset]=Field(default_factory=list,max_length=100)
    debts: list[Debt]=Field(default_factory=list,max_length=100)
    goals: list[Goal]=Field(default_factory=list,max_length=100)
    portfolio: PortfolioPlan=Field(default_factory=PortfolioPlan)
    @model_validator(mode='after')
    def unique_ids(self):
        for name in ['income','expenses','assets','debts','goals']:
            ids=[x.id for x in getattr(self,name)]
            if len(ids)!=len(set(ids)):raise ValueError('Duplicate record IDs')
        return self
class StateUpdate(Strict):
    state: State
    version: int=Field(ge=0)
class Credentials(Strict):
    email: str=Field(min_length=5,max_length=254,pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    password: str=Field(min_length=10,max_length=128)
class Scenario(Strict):
    years: int=Field(default=20,ge=1,le=30)
    expense_reduction: float=Field(default=0,ge=0,le=90)
    extra_income: float=Field(default=0,ge=0,le=1e7)
    income_growth: float|None=Field(default=None,ge=-10,le=30)
    investment_return: float|None=Field(default=None,ge=-20,le=25)
class Chat(Strict):
    question: str=Field(min_length=1,max_length=2000)
class ExpenseText(Strict):
    text: str=Field(min_length=1,max_length=200000)

class MonteCarloOptions(Strict):
    scenario: Literal['lean','normal','fat']='normal'
    volatility: float|None=Field(default=None,ge=0,le=40)
    end_age: int=Field(default=90,ge=50,le=110)
    simulations: int=Field(default=2000,ge=200,le=5000)
    seed: int=Field(default=42,ge=0,le=2**31-1)
class MonteCarloRequest(Strict):
    state: State|None=None
    options: MonteCarloOptions=Field(default_factory=MonteCarloOptions)
class PasswordChange(Strict):
    current_password: str=Field(min_length=1,max_length=128)
    new_password: str=Field(min_length=10,max_length=128)
