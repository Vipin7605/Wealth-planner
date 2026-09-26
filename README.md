# Wealthwise — AI Wealth Growth Planner

**Version 3.0.0 · Local academic application · INR**

Start with [START_HERE.md](START_HERE.md). The project includes all source code, a built frontend, synthetic data and a trained demonstration model.

## Start
```bash
python run.py
```
Use `python3 run.py` on macOS/Linux. Python 3.11–3.13 is supported by the launcher. Internet is needed for first installation. Open http://127.0.0.1:8000 after startup. Windows and Mac launchers are also included.

## Workspace
| Page | Purpose |
|---|---|
| Overview | Original dark dashboard: net worth, income, surplus, savings rate, wealth chart, score, spending and emergency reserve |
| My finances | Monthly income, needs/wants, asset balances and optional debt; CSV expense import and quick-entry labels |
| Financial health | Explained 100-point rubric, strengths, weaknesses, opportunities, threats and priority actions |
| Personal & protection | Household profile, dependants, insurance and emergency target |
| FIRE planner | Separate Lean/Normal/Fat scenarios, editable assumptions, budget cap, required monthly saving, projection chart, metric explanations and a Monte Carlo market-volatility stress test |
| Wealth simulator | Assumption-based long-term what-if comparisons |
| Goals | Targets, savings earmarks, deadlines and required monthly funding |
| Debt planner | Avalanche and snowball comparisons within available surplus |
| Financial guide | Calculations explained in plain language; rule-based by default |
| ML research | Synthetic regression experiment, validation comparison, test metrics, a calibrated prediction interval and feature-importance ranking |
| Reports | Printable financial summary and exports |
| Settings | Shared assumptions, JSON backup/restore, password change and account management |

Allocation & mix is retired. Asset metadata and the legacy portfolio budget key remain internally for compatibility with saved plans.

## Improvements in 3.0
- Monte Carlo retirement stress test: thousands of simulated return paths estimate the probability your FIRE plan survives to a chosen age, a safe spending level, and a percentile fan chart, alongside the existing deterministic projection.
- The ML estimate now reports a calibrated prediction interval (conformalized quantile regression, coverage measured on unseen test users) and permutation feature importance, not just a point number.
- Category suggestions match whole words only ("rent" no longer matches "parents" or "current"); CSV import accepts ₹, commas and semicolon-delimited exports, and flags rows that look like duplicates of expenses you already saved before importing them.
- Timing-safe login (unknown-email and wrong-password responses are indistinguishable), per-account lockout after repeated failures, a password-change endpoint that signs out other devices, and a Content-Security-Policy header.
- Frontend split from one 2,200-line file into pages/components, with ESLint passing cleanly.

## Improvements in 2.0
- Preserves the requested Overview and separate FIRE page, with consistent dark styling.
- Expandable setup checklist, built-in metric explanations and accessible chart data table.
- FIRE trajectory, required monthly contribution and additional contribution needed for Normal FIRE.
- Explicit surplus ledger showing unallocated funds and overcommitted budgets.
- Unsaved-edit prompts for FIRE, profile and settings; unexpected UI-error recovery screen.
- Authenticated backup preview; restore requires a reviewed user action and keeps account credentials.
- Saves return the normalized state and dashboard together; optimistic version checks prevent silent multi-tab overwrites.
- Separate application, chart and vendor bundles; keyboard focus indicators and reduced-motion support.

## Architecture and development
React + Vite + Recharts frontend; FastAPI + SQLAlchemy backend; SQLite default.

```bash
# Backend, after launcher setup
.venv/bin/python -m uvicorn backend.main:app --reload
# React development, separate terminal
cd frontend
npm ci
npm run dev
# Build after changing the React source
npm run build
```
On Windows use `.venv\Scripts\python.exe`. Vite proxies API calls to port 8000. Docker/compose are optional templates; local startup is the verified path.

Financial inputs are validated server-side. Passwords use salted scrypt compared in constant time, with a per-account lockout after repeated failed attempts and login responses that do not reveal whether an email is registered. Sessions use HttpOnly, SameSite=Strict cookies. JSON mutations, origin checks and a Content-Security-Policy header limit cross-origin and injected-script risk. Demo workspaces are separate from registered accounts. The launcher binds to loopback; deployment beyond a local device requires separate operational review.

Optional environment variables: `DATABASE_URL`, `ALLOWED_ORIGINS`, `COOKIE_SECURE`, `OLLAMA_MODEL`, `OLLAMA_URL`. The launcher reads a local `.env` if provided. Only loopback Ollama URLs are allowed; install and run Ollama separately if using it. Without this configuration the guide needs no AI API key.

## Data science and calculations
`data/ml_training_12m.csv` contains 24,000 synthetic training/validation/test rows. Users are separated across splits (700/200/100). See `data/DATASET_README.md`, `data/data_dictionary.csv`, `ml/train.py` and `ml/metrics.json`. Run `python ml/train.py` in the installed environment to retrain.

The selected regression model predicts a synthetic 12-month net-worth outcome, with an interval from conformalized quantile regression whose coverage is measured on unseen test users. Its reported error does not validate real household forecasting. FIRE's headline projection is deterministic mathematics; the FIRE planner also offers an explicit Monte Carlo stress test that adds market volatility and retirement withdrawals, clearly separated from the deterministic figures above it. Financial-health scoring is rule-based, not ML classification.

See [docs/FINANCIAL_HEALTH.md](docs/FINANCIAL_HEALTH.md) for accounting and formulas and [docs/FINAL_RELEASE.md](docs/FINAL_RELEASE.md) for release checks and known limits.

## Verification
```bash
.venv/bin/python -m pytest -q
node frontend/tests/smoke.mjs
node frontend/tests/fire.mjs
node frontend/tests/health.mjs
node frontend/tests/montecarlo.mjs
```
Browser tests require Playwright's Chromium or `WEALTH_CHROMIUM` pointing to a compatible binary. They start an isolated temporary database. Do not run browser scripts concurrently on the same port. Python and browser dependencies are separate from the distributable ZIP.

## Backups
Settings → Download JSON backup creates a schema-version 1 export. Choose backup validates the financial state without changing it. Restore reviewed plan replaces the account's current financial inputs using the current state version; it does not import passwords. Invalid files and stale saves are rejected.

## Password change
Settings → Change password requires the current password, rejects a new password identical to the old one, and signs out every other signed-in device while keeping the current session active. Demo workspaces have no password and cannot use this.
