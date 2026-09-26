# Architecture and academic scope

## Components

React views call same-origin FastAPI endpoints. Authentication resolves an opaque cookie to a hashed session record and user, with constant-time password comparison and a per-account lockout independent of the request's source address. Pydantic validates financial state; SQLAlchemy persists each user’s document with a version number. A deterministic financial engine owns all arithmetic. A separate Monte Carlo module runs the same FIRE assumptions through simulated market returns to estimate a survival probability, given either the saved plan or an unsaved draft. The ML module separately estimates 12-month synthetic net worth with a calibrated prediction interval. The advisor explains calculated values via explicit rules or an optional local LLM, and now cites the Monte Carlo survival probability when discussing FIRE.

## Data model

- `users`: id, unique email, salted password hash, financial state JSON text, version, demo flag.
- `sessions`: token hash, user ID, expiry timestamp.
- Financial JSON: profile plus income, expenses, assets, debts and goals collections. IDs are unique within collections.
- Synthetic CSVs and fitted models are research assets, separate from live account storage.

This document-storage design keeps the local prototype simple and permits atomic plan updates. It is not the normalized PostgreSQL entity schema described as a possible future architecture in the initial project concept. A future multi-user production system could normalize financial records and introduce migrations.

## API map

| Route | Function |
|---|---|
| POST /api/register, /api/login, /api/demo, /api/logout | Account and session lifecycle |
| GET /api/me | Session identity |
| GET /api/state | Current user’s financial state and version |
| PUT /api/state | Validated, version-checked replacement of current user’s state |
| DELETE /api/account | Current user and all its sessions removed |
| GET /api/dashboard | Summary and 20-year baseline |
| POST /api/scenario | Baseline and adjusted scenario |
| GET /api/debt-plan?extra= | Both repayment strategies |
| POST /api/categorize | Explicit keyword-rule category suggestion |
| POST /api/parse-expenses | Parse and validate CSV; no mutation until confirmed |
| POST /api/advisor | Grounded explanation; optional local AI |
| GET /api/ml | Synthetic 12-month ML estimate, calibrated interval and measured evaluation |
| POST /api/monte-carlo | Simulated-market FIRE survival probability for the saved plan or a supplied draft; never mutates state |
| POST /api/password | Authenticated password change; revokes other devices' sessions |
| GET /api/export?kind=csv | Financial summary CSV (default JSON exports full plan) |

## Research design

The project separates a deterministic financial simulator from learned prediction. Long-term outcome charts are scenario calculations, not empirical 30-year predictions. The 12-month learned model uses a labelled synthetic panel with user-disjoint holdouts. Report the generator’s assumptions, selected model, comparison to persistence, and limitations in the academic evaluation. This prototype demonstrates an end-to-end system; publication-quality empirical claims require real-world data and further validation.

## Extension points

- Normalize records and add recurring transaction history, with migration tooling.
- Train an expense classifier on consented labelled merchant narrations; current category suggestions are rules.
- Model taxes, fees, retirement income transitions and correlated (rather than independent month-to-month) market scenarios; the current Monte Carlo module already adds return volatility but keeps every other deterministic-engine assumption.
- Add goal-specific return assumptions and explicit allocations of assets to goals.
- Evaluate an LLM on numerical faithfulness with human-reviewed questions and responses.
- Add bank integration only with an authenticated, consented provider and review of its requirements.
