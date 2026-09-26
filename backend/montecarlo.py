"""Monte Carlo retirement simulation.

The deterministic FIRE calculator answers "what if returns are exactly X% every
year?". This module answers the more honest question: "given that returns vary,
how likely is the plan to work?".

Model
-----
* Monthly returns are log-normal, calibrated so that the *expected* annual gross
  return equals ``1 + investment_return`` (the same input the deterministic
  engine uses). Volatility is the standard deviation of annual log-returns.
* Accumulation phase: fixed nominal monthly contribution added at month end,
  exactly like the deterministic FIRE fund. With volatility 0 the two engines
  agree to the paisa (this is unit-tested).
* Retirement phase: monthly spending (today's rupees) is inflated to each month
  and withdrawn at the *start* of the month (the conservative convention), then
  the remainder is exposed to that month's return. A path that hits zero stays
  at zero ("depleted").
* Fixed seed by default, so numbers do not jitter when unrelated inputs change.

Not modelled: taxes, fees, fat-tailed or serially correlated returns, changing
asset allocation in retirement, pensions or other income, variable spending.
"""
from __future__ import annotations

import numpy as np

from .finance import summary
from .schemas import MonteCarloOptions, State
from .wellness import wellness

# Annual volatility (%) assumed for a diversified portfolio by risk preference.
# These are illustrative planning defaults, not forecasts.
DEFAULT_VOLATILITY = {"low": 8.0, "medium": 12.0, "high": 16.0}
SCENARIO_INDEX = {"lean": 0, "normal": 1, "fat": 2}
PERCENTILES = (10, 25, 50, 75, 90)
SAFE_SPENDING_CONFIDENCE = 0.90


def _growth_params(annual_return_pct: float, volatility_pct: float) -> tuple[float, float]:
    """Monthly log-mean and log-sd so that E[annual gross return] = 1 + R."""
    annual_return = 1 + annual_return_pct / 100
    sigma = volatility_pct / 100
    monthly_mean = (np.log(annual_return) - sigma**2 / 2) / 12
    monthly_sd = sigma / np.sqrt(12)
    return float(monthly_mean), float(monthly_sd)


def _drawdown(balance0, growth, factors, spend, on_year=None):
    """Run the retirement drawdown for every path at once.

    ``growth`` has shape (months, paths). A path is depleted in the month it
    cannot fund that month's inflated withdrawal; it then stays at zero.
    Returns the depletion month per path (-1 = lasted the whole horizon).
    ``on_year(k, balance)`` is called with the balances after each full year.
    """
    balance = balance0.copy()
    depleted = np.full(balance.shape, -1, dtype=np.int64)
    for month in range(growth.shape[0]):
        need = spend * factors[month]
        alive = depleted < 0
        fail = alive & (balance < need - 1e-9)
        depleted[fail] = month
        balance = np.where(fail | ~alive, 0.0, balance - need) * growth[month]
        if on_year is not None and (month + 1) % 12 == 0:
            on_year((month + 1) // 12, balance)
    return depleted


def _survival_rate(balance0, growth, factors, spend) -> float:
    return float(np.mean(_drawdown(balance0, growth, factors, spend) < 0))


def _safe_spending(balance0, growth, factors, inflation_at_retirement) -> float:
    """Highest monthly spend (today's rupees) with >= 90% survival (bisection).

    Common random numbers make survival monotone in spend, so bisection is valid.
    """
    months = growth.shape[0]
    top = float(balance0.max())
    if top <= 0 or months == 0:
        return 0.0
    low = 0.0
    high = 3 * top / (months * inflation_at_retirement) + 1
    if _survival_rate(balance0, growth, factors, high) >= SAFE_SPENDING_CONFIDENCE:
        return round(float(high), 2)
    for _ in range(22):
        mid = (low + high) / 2
        if _survival_rate(balance0, growth, factors, mid) >= SAFE_SPENDING_CONFIDENCE:
            low = mid
        else:
            high = mid
    return round(float(low), 2)


def simulate(state: State, options: MonteCarloOptions | None = None) -> dict:
    options = options or MonteCarloOptions()
    sm = summary(state)
    fire = wellness(state, sm)["fire"]
    profile = state.profile

    scenario = fire["scenarios"][SCENARIO_INDEX[options.scenario]]
    retire_years = fire["years"]
    retire_age = profile.age + retire_years
    end_age = options.end_age
    if end_age <= retire_age:
        raise ValueError(f"Plan-until age must be after your retirement age ({retire_age}).")

    volatility = options.volatility if options.volatility is not None else DEFAULT_VOLATILITY[profile.risk]
    paths = options.simulations
    accumulate_months = retire_years * 12
    retire_months = (end_age - retire_age) * 12
    total_years = end_age - profile.age
    mean, sd = _growth_params(profile.investment_return, volatility)
    inflation = profile.inflation / 100
    monthly_inflation = (1 + inflation) ** (1 / 12)
    rng = np.random.default_rng(options.seed)

    corpus = float(fire["corpus"])
    contribution = float(fire["monthly_contribution"])

    # --- Accumulation ------------------------------------------------------
    balance = np.full(paths, corpus)
    by_year = np.zeros((paths, total_years + 1))
    by_year[:, 0] = balance
    for month in range(1, accumulate_months + 1):
        balance = balance * np.exp(mean + sd * rng.standard_normal(paths)) + contribution
        if month % 12 == 0:
            by_year[:, month // 12] = balance
    at_retirement = balance.copy()

    # --- Retirement --------------------------------------------------------
    growth = np.exp(mean + sd * rng.standard_normal((retire_months, paths)))
    # Nominal withdrawal multiplier for each retirement month (today's = 1).
    factors = monthly_inflation ** (accumulate_months + np.arange(retire_months))
    spend_today = float(scenario["monthly_spending"])

    def record(year_in_retirement, balance):
        by_year[:, retire_years + year_in_retirement] = balance

    depleted = _drawdown(at_retirement, growth, factors, spend_today, on_year=record)

    survived = depleted < 0
    failed = ~survived
    target = float(scenario["target_retirement"])
    reach_target = float(np.mean(at_retirement >= target - 1e-9)) if target > 0 else 1.0

    def bands(values):
        return {f"p{p}": float(v) for p, v in zip(PERCENTILES, np.percentile(values, PERCENTILES))}

    timeline = []
    for year in range(total_years + 1):
        real_factor = (1 + inflation) ** year
        nominal = bands(by_year[:, year])
        timeline.append(
            {
                "age": profile.age + year,
                "phase": "saving" if year <= retire_years else "retired",
                **{k: round(v, 2) for k, v in nominal.items()},
                "real_p50": round(nominal["p50"] / real_factor, 2),
            }
        )

    retire_bands = bands(at_retirement)
    real_at_retirement = (1 + inflation) ** retire_years
    failure_ages = retire_age + (depleted[failed] + 1) / 12 if failed.any() else np.array([])
    safe = _safe_spending(at_retirement, growth, factors, factors[0] if retire_months else 1.0)

    warnings = []
    if sm["surplus"] < 0:
        warnings.append("Your monthly budget has a shortfall; the simulation does not fund it.")
    if float(scenario["monthly_spending"]) <= 0:
        warnings.append("Enter a retirement spending budget; with zero spending every path trivially succeeds.")
    if corpus <= 0 and contribution <= 0:
        warnings.append("No starting investments or affordable contributions; the fund stays at zero.")
    if retire_years == 0:
        warnings.append("Retirement age has been reached; the simulation starts withdrawing immediately.")

    return {
        "scenario": scenario["name"],
        "simulations": paths,
        "seed": options.seed,
        "survival_probability": round(float(np.mean(survived)), 4),
        "reach_target_probability": round(reach_target, 4),
        "target_at_retirement": round(target, 2),
        "deterministic_at_retirement": round(float(fire["projected_corpus"]), 2),
        "at_retirement": {k: round(v, 2) for k, v in retire_bands.items()},
        "at_retirement_real": {k: round(v / real_at_retirement, 2) for k, v in retire_bands.items()},
        "median_depletion_age": round(float(np.median(failure_ages)), 1) if failed.any() else None,
        "safe_monthly_spending": safe,
        "safe_confidence": SAFE_SPENDING_CONFIDENCE,
        "planned_monthly_spending": round(spend_today, 2),
        "timeline": timeline,
        "warnings": warnings,
        "assumptions": {
            "retirement_age": retire_age,
            "end_age": end_age,
            "expected_return_pct": profile.investment_return,
            "volatility_pct": volatility,
            "inflation_pct": profile.inflation,
            "starting_corpus": round(corpus, 2),
            "monthly_contribution": round(contribution, 2),
            "withdrawal_timing": "start of month",
        },
        "note": (
            "Log-normal monthly returns, fixed contributions, inflation-linked withdrawals. "
            "No taxes, fees, fat tails, pensions or spending flexibility. Illustrative, not a forecast."
        ),
    }
