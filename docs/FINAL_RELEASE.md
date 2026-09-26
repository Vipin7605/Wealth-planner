# Final release 2.0

## Design decisions
The requested dark Overview remains the home page. FIRE is a separate module. Allocation & mix remains removed. Existing household, protection, health score, expense, goals and debt functionality is retained.
New work focuses on explaining results and preventing avoidable data loss, not adding unverified AI claims.

## FIRE mathematics
For annual nominal return R, monthly rate r = (1 + R/100)^(1/12) − 1.
For n months, starting fund P and monthly contribution M:
future fund = P(1+r)^n + M[((1+r)^n−1)/r]. At r=0, future fund=P+Mn.
Required fixed monthly contribution = max(0, (future target−P(1+r)^n) / annuity factor).
The annuity factor is n when r=0. With zero time remaining and insufficient funds, required monthly contribution is unavailable rather than an infinite/zero claim.
Required amounts are explanatory and do not automatically increase contributions. The app caps the actual contribution after other monthly reservations.
Yearly chart points compare investments and inflation-adjusted Normal FIRE targets in nominal future rupees at each age. The chart's data table provides the same values.

## Reliability
A save transaction retains the optimistic state version check and returns normalized inputs plus dashboard values in one response. Backup preview is authenticated and does not save. Restore is an explicit action after review. Existing schema-version 1 backups are accepted. Frontend validation is supplemented by Pydantic server validation.
Unsaved-change prompts cover FIRE, personal/protection and Settings drafts. Browser reload warns on dirty drafts. The UI error boundary offers recovery to the last saved plan.

## Verification evidence
Backend results: 46 tests, including required-contribution algebra, zero-return and zero-horizon cases, budget overcommitment, backup authentication/normalization/isolation and all previous finance/auth/ML tests.
Browser results are in fire-test-results.json and health-test-results.json. Production frontend build is included. Screenshots show fictional demo data.

## Limitations
The academic model is trained on synthetic data. No real financial forecasting performance is established.
FIRE assumes fixed contributions and constant nominal returns, with no tax, fees, volatility, pension offsets or retirement drawdown simulation. Cash-flow deficits produce warnings; the FIRE accumulation path does not fund them. The wealth simulator separately tracks spending shortfalls.
The retirement spending budget defaults to present expenses plus EMIs; users must adjust it when their future commitments differ. Restricted investments are included if marked portfolio; liquidity/access at retirement is not verified. Existing goal earmarks must be excluded through asset-purpose tags to avoid treating the same money as retirement funding.
The app has no password-reset email flow, bank connection, live prices or trade execution. Insurance scoring does not assess coverage adequacy. A local financial-planning demonstration is not a regulated advisory service.

# Version 3.0

## Design decisions
This release focuses on three things the 2.0 build named as limitations: FIRE's silence on market volatility, the ML page's unqualified point estimate, and two account-security gaps. It also fixes three real, demonstrable bugs found while reviewing the existing code, and splits the frontend's single 2,200-line file into pages and components for maintainability. No page, calculation or saved-data format from 2.0 was removed.

## Monte Carlo FIRE stress test
`backend/montecarlo.py` runs the same FIRE inputs (starting corpus, monthly contribution, retirement age, spending target) through simulated monthly returns instead of one constant rate. Monthly returns are log-normal, calibrated so their expected annual return matches the deterministic engine's assumed return exactly — at zero volatility the two engines agree to the paisa, which is unit-tested directly. Retirement-phase withdrawals inflate every month and are taken at the start of the month; a path that cannot fund a withdrawal is marked depleted and stays at zero rather than going negative. The endpoint reports: survival probability to a chosen age, probability of reaching the deterministic target by retirement, a monthly spending level with ~90% simulated survival (found by bisection, since survival is monotone in spending under common random numbers), and a 10th/25th/50th/75th/90th percentile fund size at every age for the fan chart. It accepts either the user's saved plan or an unsaved draft and never writes to the database, so the FIRE planner can preview it live while editing without a save.

What it still does not model: taxes, fees, fat-tailed or serially correlated returns, a changing asset mix in retirement, pensions or other income, and variable (rather than fixed, inflation-linked) spending. This is stated in the API response's own `note` field, not only in this document.

## ML prediction interval
`ml/train.py` now predicts the 12-month *change* in net worth (added back to the current value) rather than the level directly, which is an easier learning target and extrapolates more sensibly outside the training range. The point model is chosen among Ridge, random forest and gradient boosting by validation MAE, reported alongside two naive baselines (persistence, and a simple cash-flow extrapolation) so the improvement over "assume nothing changes" is visible rather than asserted. The interval comes from conformalized quantile regression: gradient-boosted 10th/90th quantile models, widened by a margin calibrated on the validation split so that the interval's *coverage* — not just its existence — is a measured, reported number on the untouched test split, together with permutation feature importance so it's clear which inputs the model actually leans on. `backend/mlfeatures.py` is now shared between training and serving so the two cannot silently drift apart, which was a latent risk in the 2.0 code (the API endpoint reconstructed its own feature list by hand).

## Security hardening
Login previously compared the submitted password only when an account with that email existed, so response time (and behavior) could reveal whether an email was registered; it now always runs the same scrypt comparison against a dummy hash when no account matches. A per-account failure counter (independent of the existing per-IP rate limit) locks an account for 15 minutes after 10 failed attempts, closing a gap where a distributed attacker could bypass the IP-based limit entirely. A new authenticated password-change endpoint requires the current password, rejects a "new" password identical to the old one, and revokes every other session for that account while leaving the caller's own session intact. Every response now carries a Content-Security-Policy header restricting scripts to same-origin and disallowing framing, and static assets are cache-controlled by type instead of uniformly.

## Bug fixes
- The expense categorizer matched keywords as substrings, so "Parents support" was filed under Housing (via "rent" inside "parents"), "Current account fee" under Housing ("rent" inside "current"), and "Business lunch" under Travel ("bus" inside "business"). It now matches whole words only.
- CSV import rejected any amount containing a rupee sign, thousands separators, or an "Rs." prefix — i.e., it rejected the output of a typical bank or expense-app export. It now strips recognized currency formatting before parsing, and also accepts semicolon-delimited files.
- CSV import had no way to notice that an imported row was already saved; a re-imported file silently doubled every expense. Import now flags rows matching an existing expense's name and amount, and defaults to skipping them (the person can still choose to import them anyway).

## Verification evidence
Backend: 86 tests pass (46 existing + 40 new), covering the items above plus an independent scalar reference implementation of the retirement drawdown used to check the simulator's zero-volatility case at several spending levels. Browser: four suites pass (smoke, fire, health, and new montecarlo.mjs), 45 checks total. The Monte Carlo engine and two of the new browser checks were mutation-tested — a known-wrong version of the code was confirmed to fail the relevant test — as evidence the tests are sensitive to the behavior they claim to check, not simply passing by default. See docs/TESTING.md for the full breakdown.

## Limitations carried into 3.0
Everything listed under 2.0's Limitations above still applies to the deterministic FIRE figures and the ML point estimate. The Monte Carlo addition narrows, but does not remove, the "no volatility" limitation — see "What it still does not model" above. The ML interval's measured coverage is itself only as trustworthy as the synthetic generator producing both the training and test data; it says nothing about coverage against real financial outcomes. Account lockout is in-memory and per-process, so it resets on server restart and does not persist or synchronize across multiple server instances; a production deployment would need a shared store.
