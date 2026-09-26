# AI Wealth Growth Planner — synthetic dataset v1

All records are fictional, generated for academic prototyping. No personal data, real transactions, or external datasets were used. Currency is nominal INR. Rates are decimals (0.15 means 15%). The panel covers January 2023–December 2025 for 1,000 users. Seed: 20260919.

## Start here

- `wealth_planner_dataset.csv`: one latest snapshot per user, as of 2025-12-31. Use for the dashboard and financial forms.
- `ml_training_12m.csv`: 24,000 feature/target pairs. Feature dates span January 2023–December 2024. Targets are simulated balances exactly 12 months later.
- `monthly_financials.csv`: 36,000 monthly records, including opening balances, flows, and closing balances.
- `expense_records.csv`: 360,000 monthly category totals with simple synthetic descriptions and labels. These are NOT individual bank transactions.
- `users.csv`: fictional profiles and fixed user-disjoint splits.
- `assets.csv`: starting and ending cash/investment snapshots. Filter by date before aggregating.
- `debts.csv`: loan origination/starting snapshots and ending snapshots. Key is (debt_id, as_of_date). Filter the date before aggregating.
- `debt_schedule.csv`: opening balance, interest, payment, and closing balance by loan/month. New shortfall loans begin repayments the next month.
- `goals.csv`: three illustrative goals per user. Earmarked amounts are part of existing assets, not new assets.
- `assumptions.csv`: simulation parameters, not model targets or financial advice.
- `data_dictionary.csv`: every column's type and definition.
- `validation_report.json`: checks and counts.

## How the simulation works

Starting monthly income is clipped lognormal (₹15,000–₹250,000); age is sampled from 22–60. These arbitrary distributions are not calibrated to India's population. Profiles omit gender, caste, credit scores, names, contacts, and account credentials.

Income grows 2–12% annually with monthly noise; December includes a bonus. Starting living expenses are 40–90% of base income, growing 3–8% annually with noise and occasional additional expense shocks. Income is take-home, so taxes are not deducted again. No retirement transition is modeled within this three-year panel.

Essential expenses exclude Shopping, Entertainment, and Other. Housing is included as an additional category because omitting rent would distort planning. Emergency target is six times essential expenses. All cash is considered eligible for the gap calculation; earmarked goals are not deducted.

Debt uses fixed monthly payments with interest = opening balance × annual rate / 12. Credit-card debt is simplified as an amortizing balance without new card purchases or variable minimum payments. APRs are illustrative, not sourced market rates.

Investments receive a monthly random return with annual arithmetic means of 4%, 7%, or 10% and monthly standard deviations of 0.8%, 2.5%, or 4.5%, according to fictional risk preference. Monthly returns are clipped below at -50%. Returns apply to opening investments; contributions occur at month-end. There are no fees, taxes, correlated market shocks, or inflation-adjusted values. Cash earns no interest.

Positive cash-flow surplus is partially invested. A shortfall uses cash, then sells investments, then creates a 24% nominal annual shortfall loan with a fixed payment equal to 6% of its original principal. This is an accounting simulation, not a recommended borrowing policy. No defaults or borrowing limits are modeled. Negative net worth is allowed; asset balances remain nonnegative.

Cash close = cash open + income − expenses − debt payments − contributions + investment withdrawals + new borrowing.
Investment close = investment open + return gain + contributions − withdrawals.
Debt close = debt open + interest − payments + new borrowing.
Net worth = cash + investments − debt.

## Train a model without target leakage

Use `simulated_net_worth_12m_inr` as the target. `simulated_change_12m_inr` is an ALTERNATIVE target and must never be an input to the first target. Exclude both target columns, user_id, split, and target_date from X. Use only fields available at the feature date. Do not join latest snapshots or final asset/debt balances onto earlier feature rows. Fit preprocessing only on training data.

The supplied split uses disjoint users (700 train, 200 validation, 100 test). It evaluates generalization to unseen synthetic users, not future calendar periods. Do not randomly split repeated monthly rows. For a strict forward-time evaluation, ensure every training target date precedes the first validation feature date; a 12-month gap is necessary. This short panel limits such testing, so extend the history if both temporal and user holdouts are required.

Compare Linear Regression / Random Forest with a persistence baseline (future net worth = current net worth). Report MAE/RMSE and the synthetic provenance. Good scores indicate learning this generator, not real-world forecast accuracy.

Expense descriptions come from only 30 simple templates and explicitly reveal category vocabulary. They are suitable for pipeline/UI demos, not meaningful evidence of NLP generalization. Real anonymized, consented, labelled narrations with separate merchant/template holdouts are needed for credible classification research.

There are no observed 5-, 10-, 20-, or 30-year labels. Use a separate financial simulator for those horizons and label its output as scenario projections. The package provides no validated optimal investment, health-score, or advisor-answer labels. Implement those as transparent rules or separately evaluated systems.

## Reproduce

Python 3 standard library is sufficient:

```bash
python generate_dataset.py
```

This writes CSVs, a machine-readable validation report, and a preview intermediate into a `data/` subdirectory beside the script. Existing generated files in that subdirectory are overwritten. The Excel overview is a convenience reference and is not regenerated by this script.

Load a CSV:

```python
import pandas as pd
df = pd.read_csv('ml_training_12m.csv')
train = df[df['split'] == 'train'].copy()
exclude = ['user_id', 'month_end', 'split', 'target_date',
           'simulated_net_worth_12m_inr', 'simulated_change_12m_inr']
X = train.drop(columns=exclude)
y = train['simulated_net_worth_12m_inr']
# Encode categorical columns within a training-only fitted pipeline.
```

You may use and modify these generated records for this project. Cite them in your report as a purpose-built synthetic simulation, with this generator version and seed. Do not describe them as bank records, survey data, or Kaggle data.
