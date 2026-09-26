# Wealthwise — Final academic release 3.0

## Run the application
1. Extract the ZIP completely.
2. Install Python 3.11, 3.12 or 3.13 if it is not already installed.
3. Open the extracted `wealth-growth-planner` folder in VS Code.
4. Open its terminal and run `python run.py` on Windows, or `python3 run.py` on macOS/Linux.
5. The launcher installs dependencies into a project environment, trains the synthetic demonstration model and opens http://127.0.0.1:8000.

First setup needs internet. Keep the terminal open; Ctrl+C stops the app.
Windows also has Start-Windows.bat; macOS has Start-Mac.command.
If port 8000 is busy, run `python run.py --port 8001` (use python3 on macOS).
Node.js is unnecessary to run the included build; it is needed only when editing React.

## First walkthrough
- Choose Explore interactive demo to see fictional sample data.
- Overview preserves the requested dark dashboard and original card/chart layout.
- Create your own account for a separate empty plan. Registration does not send email or verify an address.
- Use the Overview checklist to add household details, monthly finances, asset balances and protection.
- Enter regular loan payments under Debts only. Do not duplicate them as expenses.
- Keep FIRE as a separate planning page. Try a retirement budget, review the projection and required monthly contribution, then scroll to the Monte Carlo stress test to see the probability your plan survives real market ups and downs before you Save FIRE plan.
- Financial health contains score details, SWOT and priority actions. It is a transparent project heuristic.
- Reports provides a printable summary. Settings lets you download and restore JSON backups.

## Updating an older copy
Download a JSON backup from the old app before upgrading. Keep the old folder until the upgrade works.
Run the new project, create/sign in to a local account, and choose Settings → Choose backup → Review before restoring → Restore reviewed plan.
The backup transfers financial inputs, not login passwords. This release accepts schema-version 1 backups and supplies defaults for missing newer fields.
Alternatively, when using SQLite, with BOTH applications stopped copy the old runtime/wealth.db into the new runtime folder, preserving all accounts. Never replace a database while either application is running.

## What is included
- Complete React and FastAPI source; prebuilt frontend.
- SQLite by default; optional PostgreSQL configuration.
- Synthetic ML dataset, generator, dictionary, training code, model and evaluation metrics.
- Automated backend and browser tests, screenshots and implementation notes.
- Local rule-based financial guide; optional Ollama integration described in README.

## Understand the boundaries
This is a locally runnable academic application. The regression experiment uses synthetic household data.
Long-term wealth and FIRE use explicit mathematical assumptions, not learned market predictions.
FIRE's headline projection assumes fixed contributions and a constant return, with no taxes or fees; its separate Monte Carlo stress test adds market volatility and retirement withdrawals but still ignores taxes, fees and pensions. An apparent target match, or a high simulated survival probability, is not retirement-readiness certification.
The financial-health score is not a credit rating. Insurance scoring records policy presence, not coverage adequacy.
No bank connections, payments, trades or live market feeds are provided.
