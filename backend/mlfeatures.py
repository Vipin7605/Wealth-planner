"""Feature construction shared by ml/train.py and the /api/ml endpoint.

Keeping this in one place guarantees the model sees identical features at
training and inference time (no train/serve skew).
"""
import pandas as pd

BASE_NUMERIC = ['age', 'take_home_income_inr', 'living_expenses_inr', 'essential_expenses_inr',
                'debt_payment_inr', 'cash_inr', 'investments_inr', 'total_liabilities_inr', 'net_worth_inr']
CATEGORICAL = ['risk_tolerance', 'employment_type']
ENGINEERED = ['monthly_surplus_inr', 'savings_rate', 'liquidity_months', 'investment_share',
              'risk_level', 'investments_x_risk']
NUMERIC = BASE_NUMERIC + ENGINEERED
FEATURES = NUMERIC + CATEGORICAL
RISK_LEVEL = {'low': 0, 'medium': 1, 'high': 2}


def build_features(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the model input frame. Uses only same-month information."""
    out = frame[BASE_NUMERIC + CATEGORICAL].copy()
    income = out['take_home_income_inr']
    out['monthly_surplus_inr'] = income - out['living_expenses_inr'] - out['debt_payment_inr']
    out['savings_rate'] = (out['monthly_surplus_inr'] / income.where(income > 0)).fillna(0).clip(-2, 1)
    commitments = out['essential_expenses_inr'] + out['debt_payment_inr']
    out['liquidity_months'] = (out['cash_inr'] / commitments.where(commitments > 0)).fillna(0).clip(0, 120)
    financial = out['cash_inr'] + out['investments_inr']
    out['investment_share'] = (out['investments_inr'] / financial.where(financial > 0)).fillna(0)
    out['risk_level'] = out['risk_tolerance'].map(RISK_LEVEL).astype(float)
    out['investments_x_risk'] = out['investments_inr'] * out['risk_level']
    return out[FEATURES]
