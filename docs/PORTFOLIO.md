# Allocation and diversification

Open **Allocation & mix** in the sidebar. This is an educational planner, not a market optimizer or trading system.

## Holdings and scope

In My finances → Assets, edit class, purpose, issuer/provider, sector, geography, vehicle and liquidity. Separate positions into separately valued rows. Only portfolio-purpose assets enter allocation calculations. Emergency, near-term and personal assets stay in net worth but are excluded from this portfolio. To divide a holding between purposes, split its value across rows without duplication. Goal savings remain earmarks of existing assets.

Old investment rows remain unclassified; suggestions are blocked until classified. Cash/property types imply cash/real-estate classes when unspecified. Unknown issuer, sector or geography remains visible rather than being inferred from a name.

## Target policy

Weights use risk preference from Settings and this portfolio's horizon. Custom weights must total 100%. Presets are authored project examples, not regulator recommendations or empirically optimized allocations.

Order: Indian equity / international equity / bonds and deposits / gold / real estate / cash / alternatives.

| Horizon | Low risk | Medium risk | High risk |
|---|---|---|---|
| 1–3 years | 0/0/35/0/0/65/0 | 0/0/35/0/0/65/0 | 0/0/35/0/0/65/0 |
| 4–7 years | 10/5/55/10/0/20/0 | 25/10/45/10/0/10/0 | 35/10/35/10/0/10/0 |
| 8+ years | 15/5/55/10/0/15/0 | 40/10/30/10/0/10/0 | 55/15/15/10/0/5/0 |

Bonds and deposits are grouped broadly. Credit quality, duration, insurance protection and instrument suitability are not evaluated. A category label is not a guarantee of capital preservation.

Target value = portfolio value × target %. Drift = current % minus target %, in percentage points. Default review threshold: 5 pp, adjustable. Rebalancing gaps ignore prices changing, tax, fees, lot sizes and restrictions; they are not executable orders. Illiquid holdings trigger review notes.

## Diversification

Class coverage, top holding/top-three weights and tagged issuer, sector, geography and liquidity groups describe entered data only. The adjustable 20% holding threshold is a review prompt, not a universal safe limit. A diversified fund is not a single-security position. A fund manager/provider is not necessarily an underlying issuer or common counterparty.

Without constituents, price history or correlations, this app does not calculate underlying fund overlap, currency exposure, efficient frontiers, expected volatility, Sharpe ratios or value-at-risk. More holdings do not automatically mean less risk.

## Contributions and safeguards

Available contribution = max(0, surplus − reserve contribution − goal contribution − extra debt payments). Scheduled payments are already deducted from surplus. Requested investing is capped to this remainder.

For each class, find its positive target-value gap after adding the new money to the portfolio total. Allocate the budget proportionally across positive gaps. Largest-remainder rounding in paise preserves the exact budget. This buy-only heuristic may not reach target weights in a single month. Unclassified holdings leave the budget unallocated.

Notes flag emergency shortfalls, debt at or above the illustrative 18% APR threshold, competing goal funding, short-horizon risky custom targets and restricted assets. Only explicitly designated emergency cash counts toward this module's reserve; the original dashboard counts all cash. That distinction is labeled.

These reservations do not move money or change the separate wealth simulator's investment ratio. Target weights do not change its single assumed return. Save the plan to persist edits; preview calls do not mutate accounts. Export uses the saved plan.

## Upgrade compatibility

New fields have defaults, so old JSON plans load without deleting records. Asset classes should be reviewed before relying on new outputs. Keep runtime/wealth.db when updating the project. Full JSON export now includes portfolio results, and Reports and the financial guide use the new targets.

## Educational references

General concepts such as horizon/risk-based allocation, within-class diversification, fund overlap and rebalancing with new contributions are described by [Investor.gov](https://www.investor.gov/introduction-investing/getting-started/asset-allocation) and [FINRA](https://www.finra.org/investors/investing/investing-basics/asset-allocation-diversification). The app's numerical weights and thresholds are project assumptions, not recommendations from these sources.
