# Financial health and FIRE — v1.2

## Inputs and accounting
Personal details: age, employment type, dependants, marital status and target retirement age.
Income and expenses are recurring monthly values. Need/want is a household-editable classification.
Debt balances and scheduled payments are optional; add them when debt exists. EMIs are counted once
from the debt table, included in needs and subtracted once from income. Do not enter the same EMI as an expense.
Insurance cover is not an asset. Premiums belong in expenses. Only liquid cash explicitly designated
as emergency funds qualifies for the reserve. Existing undesignated cash is not silently reassigned.
Goal earmarks remain subsets of assets; asset purposes determine whether funds enter the FIRE corpus.

## Explainable 100-point rubric
This is an academic heuristic, not a validated credit score or an ML prediction.
Each component is rounded to the nearest integer. Ratios are bounded between zero and one.

| Component | Maximum | Formula / condition |
|---|---:|---|
| Cash flow | 25 | surplus/income divided by 30% |
| Emergency reserve | 25 | designated liquid emergency cash / chosen emergency target |
| Debt burden | 20 | 1 − monthly payments/income divided by 50% |
| Protection | 20 | 10 for active recorded health cover >0; 10 for active recorded life/term cover >0 if dependants or debt exist, otherwise 10 |
| Investment habit | 10 | affordable planned portfolio contribution/income divided by 15% |

Missing income earns zero on income-ratio components; no income and no debt earns 20 for debt burden.
Empty financial plans score zero. Plans missing income, expenses or insurance status are provisional.
Protection records policy presence, not coverage adequacy. Planned contributions are not verified payments.
Marital status does not affect points. Age and employment do not directly reduce points.

## FIRE calculations
Today's target = monthly retirement spending × 12 × lifestyle multiplier / (withdrawal rate / 100).
Default multipliers: Lean .75, Normal 1, Fat 1.5, editable. These are project assumptions, not universal definitions.
Default withdrawal assumption is 4%, editable from 1% to 10%; the allowed range is not a recommendation.
Default spending includes current living expenses plus EMIs. Set an explicit retirement spending budget
if loans will end or costs change; pensions, taxes, insurance premiums and healthcare must be reflected
in your own budget. A zero budget produces zero targets and unavailable progress, not readiness.

Eligible starting corpus: non-property assets with purpose portfolio. Excludes emergency, near-term
and personal assets. Goal tags must be reflected in purpose if those funds should be excluded.
Target at retirement inflates today's target at profile inflation for max(0, retirement age − current age).
Corpus grows at the assumed annual return with fixed month-end contributions. Contribution = minimum
of requested portfolio contribution and surplus remaining after reserve, goal and extra debt allocations,
clamped at zero. No future income increases or released EMIs are assumed in this FIRE contribution schedule.
All eligible classes use one aggregate return assumption. Progress compares today's corpus with today's target;
funding gap compares future corpus with the inflation-adjusted future target.

No drawdown, longevity, taxes, fees or sequence-of-returns simulation is implemented. Negative cash-flow
plans are highlighted in actions; their future corpus figures do not model funding their spending shortfalls.
FIRE figures cannot establish that retirement is affordable. The regular wealth simulator separately models
cash-flow drawdowns and debt amortization and is not the same as this fixed-contribution FIRE scenario.

Conceptual reference: [Charles Schwab — The 4% Rule](https://www.schwab.com/learn/story/beyond-4-rule-how-much-can-you-spend-retirement)
explains the rule's assumptions and limitations. Its US retirement context is not validation of a particular
withdrawal rate for this INR demonstration.

## SWOT and actions
Rules use saved cash flow, reserve gaps, protection and debt at/above the project's 18% APR threshold.
P1 = address first; P2 = build resilience; P3 = improve plan. Multiple actions draw on one shared budget,
not separate promises of available money. No transactions are executed.

## Validation
42 backend tests include 8 new wellness cases: empty plans, emergency eligibility, FIRE arithmetic and inflation,
protection/marital neutrality, EMI counting and budget caps, zero return/horizon, action ordering and invalid rates.
Browser verification is recorded in health-test-results.json; portable script: frontend/tests/health.mjs.

## v1.3 navigation update
Open FIRE planner to edit retirement assumptions and the monthly contribution budget.
Personal & protection now focuses on personal details and insurance. FIRE preview is
an authenticated, read-only POST to /api/fire-preview; it does not mutate saved data.
Save FIRE plan updates the shared profile and contribution settings. CSV exports use
/api/export?kind=fire and reflect the saved plan, not unsaved previews.
Allocation & mix, its API routes, report and advisor branch have been removed.
The legacy portfolio state key is retained to preserve existing budgets and asset tags.

## Version 2.0 additions
The separate FIRE planner includes a yearly Normal FIRE target/investment chart, a readable data table, required fixed monthly contribution, extra contribution needed, a surplus ledger and metric explanations. Required contributions are calculated mathematically under the displayed assumptions; they are not automatically budgeted. Zero time remaining with a funding gap is labelled unavailable. See FINAL_RELEASE.md for formulas and edge cases. Dashboard and health-score definitions remain unchanged.
