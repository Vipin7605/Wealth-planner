# Verification

Verified on Linux with Python 3.12.14 and Node.js 24.19.0/22.22.2. Windows and macOS launchers are included but were not run on those operating systems.

## Automated tests

22 tests passed in the clean project virtual environment using:

```bash
.venv/bin/python -m pytest -q
```

Coverage includes account registration/login/logout, session cookies, account data isolation, conflict detection, account deletion, invalid data, rejected cross-origin mutations, exports, demo calculations, scenario comparisons, goal funding, debt amortization, zero-interest debt, negative amortization, borrowing shortfalls, inflation, non-finite inputs, CSV parsing and read-only previews, and trained-model inference. Dependency deprecation warnings were emitted by the test client; the tests passed.

## Browser workflows

13 browser workflows passed at desktop 1440×1050 and mobile 390×844:

1. Demo login and dashboard.
2. Income creation, editing, persistence after reload and deletion.
3. CSV preview and confirmed expense import.
4. Scenario controls.
5. Goal creation.
6. Debt comparison.
7. Calculation-based guide response.
8. Trained model inference.
9. Settings save.
10. Report rendering.
11. Mobile navigation and no horizontal page overflow.
12. Logout.
13. New-account registration and empty-plan dashboard.

No page JavaScript errors were recorded. Dashboard and mobile screenshots were visually reviewed. Charts render without entrance animations so they appear in screenshots and printed output. The browser harness also generated a temporary PDF to exercise the browser print path; it is not an independently typeset report artifact.

To repeat browser tests, stop any server using port 8000, then:

```bash
cd frontend
npm ci
npx playwright install chromium
node tests/smoke.mjs
```

Run `python3 run.py` once beforehand to create the Python environment, then stop it. The harness starts a separate backend with a temporary database. It does not modify your live financial accounts. It replaces preview screenshots and the browser-results JSON in `docs/`. Alternatively, set `WEALTH_PYTHON` to a Python interpreter with the project requirements installed.

## Clean startup

`python3 run.py --no-browser --port 8002` created a new virtual environment, installed the specified requirements, retrained the ML model and returned HTTP 200 from the health endpoint. The prebuilt frontend was served successfully in browser testing.

## Not runtime-verified

- PostgreSQL and Docker/Compose deployment.
- An actual Ollama model response; the default rule-based mode was tested.
- Windows/macOS execution and installed-browser differences.
- Public deployment security, load capacity and real-world financial prediction accuracy.

These are explicit limits of the local academic build, not claims of production certification.

## Portfolio extension verification

34 automated tests pass after adding 12 portfolio tests. They cover legacy defaults, target totals and horizons, reserve/near-term exclusions, exact paise allocation, surplus caps, zero portfolios, invalid classification, provider normalization, net-zero rebalance gaps, preview non-mutation and CSV export.

11 additional browser workflows passed: classified demo, diversification tags, budget cap, invalid weight blocking, save/reload, CSV export, asset-purpose edits, horizon presets, reports, guide integration and 390px mobile layout. See portfolio-test-results.json. Screenshots were reviewed and mobile grid overflow was corrected.

Repeat the portfolio browser checks with node tests/portfolio.mjs from frontend/ after installing Playwright browsers. Like the earlier harness, it starts its own temporary database and requires port 8000 to be free.


## v1.2 verification
42 backend tests passed. Six browser workflows passed for dashboard rendering, financial profile/FIRE save and JSON export, persistence, needs quick entry, reports and mobile overflow. Results: health-test-results.json. Production frontend build passed. Previous portfolio browser results are retained as historical v1.1 evidence.

## v1.3 verification
42 backend tests pass, including authenticated FIRE preview isolation, retired allocation route, FIRE export and invalid-rate rejection. Eight FIRE browser workflows and six health/report regression workflows pass. See fire-test-results.json and health-test-results.json.

## v1.3.1 UI verification
Production build passed. Ten Overview/FIRE browser checks and six health/report workflows passed, including restored Overview, separation of FIRE, score-detail navigation, previews, saving/reload, export, validation and responsive layout. Backend formulas are unchanged from v1.3.

## Final release 2.0 — current verification
- 46 backend tests passed.
- 15 Overview/FIRE/recovery browser checks passed, including chart data, metric help, unsaved navigation protection, backup preview/restore and invalid backup rejection.
- 6 health/report browser workflows passed.
- Vite production build passed with separate app, vendor and chart bundles.
- Screenshots were visually inspected. All browser tests used isolated temporary SQLite databases and fictional demo data.

## v3.0 verification
86 backend tests pass (was 46): 15 new Monte Carlo simulation tests (zero-volatility agreement with the deterministic engine to the paisa, an independent scalar reference implementation for the drawdown, seeded reproducibility, percentile ordering, volatility drag, safe-spending consistency, degenerate plans) and 25 new API/security/parser tests (timing-safe login and account lockout, password change and session revocation, Monte Carlo input validation and draft-vs-saved-plan isolation, ML interval containment, whole-word category matching, real-world CSV formats, duplicate-import detection).

Four browser suites pass: smoke, fire, health (all as before, with fire.mjs's chart-details locator disambiguated after the new Monte Carlo panel introduced a second matching heading) and a new montecarlo.mjs covering: the panel rendering against a live unsaved draft, changing volatility changing the simulated outcome, the draft never being saved by a preview run, invalid plan-until-age surfacing the backend's validation message, a stale error clearing once the input is corrected, the accessible percentile table, duplicate-row flagging and skip-by-default on CSV import, and the ML research page's interval and feature-importance sections. See montecarlo-test-results.json.

Both the Monte Carlo engine and the new browser assertions were mutation-tested during development: deliberately reintroducing a known bug (uninflated retirement-year withdrawals, missing volatility-drag correction, a duplicate-import regression, a stale-error UI regression) was confirmed to fail the corresponding test before the fix was restored, as a check that the tests exercise real behaviour rather than passing unconditionally.

Vite production build passed after splitting the single-file frontend into pages and components; `npx eslint src` passes with no errors or warnings on the new module layout.
