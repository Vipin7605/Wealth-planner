"""Train the synthetic 12-month net-worth model with a calibrated prediction interval.

Design
------
* Users are disjoint across train / validation / test (no leakage across splits).
* The model predicts the 12-month *change* in net worth and adds it back to today's
  net worth. This is easier to learn than the level and extrapolates better.
* Point model is chosen among Ridge, Random forest and Gradient boosting by
  validation MAE, and compared with two naive baselines.
* An 80% prediction interval comes from conformalized quantile regression (CQR):
  gradient-boosted 10%/90% quantile models, widened by a margin calibrated on the
  validation split. Coverage is then *measured* on the untouched test split.

All numbers describe a synthetic generator, not real households.
"""
from pathlib import Path
import argparse, hashlib, json, platform, sys
import numpy as np
import pandas as pd
import sklearn, joblib
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.mlfeatures import CATEGORICAL, FEATURES, NUMERIC, build_features  # noqa: E402

TARGET_LEVEL = 'simulated_net_worth_12m_inr'
TARGET_CHANGE = 'simulated_change_12m_inr'
INTERVAL_LEVEL = 0.80
SEED = 42


def metrics(y, p):
    return {'mae': round(float(mean_absolute_error(y, p)), 2),
            'rmse': round(float(np.sqrt(mean_squared_error(y, p))), 2)}


def make_pipeline(estimator, scale=True):
    prep = ColumnTransformer([
        ('numeric', StandardScaler() if scale else 'passthrough', NUMERIC),
        ('categorical', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL)])
    return Pipeline([('preprocess', prep), ('regressor', estimator)])


def conformal_margin(lo, hi, y, level):
    """CQR margin: finite-sample-corrected quantile of the conformity scores."""
    scores = np.maximum(lo - y, y - hi)
    n = len(scores)
    q = min(1.0, np.ceil((n + 1) * level) / n)
    return float(np.quantile(scores, q, method='higher'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data', type=Path, default=ROOT / 'data' / 'ml_training_12m.csv')
    args = parser.parse_args()
    frame = pd.read_csv(args.data)
    parts = {k: frame[frame.split == k].reset_index(drop=True) for k in ['train', 'validation', 'test']}
    ids = {k: set(v.user_id) for k, v in parts.items()}
    assert all(not ids[a] & ids[b] for a, b in [('train', 'validation'), ('train', 'test'), ('validation', 'test')])
    assert frame[[*NUMERIC[:9], *CATEGORICAL, TARGET_LEVEL, TARGET_CHANGE]].notna().all().all()
    assert (pd.to_datetime(frame.target_date) > pd.to_datetime(frame.month_end)).all()
    X = {k: build_features(v) for k, v in parts.items()}
    change = {k: v[TARGET_CHANGE].to_numpy() for k, v in parts.items()}
    level = {k: v[TARGET_LEVEL].to_numpy() for k, v in parts.items()}
    now = {k: v.net_worth_inr.to_numpy() for k, v in parts.items()}

    candidates = {
        'Ridge regression': make_pipeline(Ridge(alpha=10)),
        'Random forest': make_pipeline(RandomForestRegressor(n_estimators=150, max_depth=12, min_samples_leaf=10,
                                                            max_features=.8, n_jobs=2, random_state=SEED), scale=False),
        'Gradient boosting': make_pipeline(HistGradientBoostingRegressor(loss='absolute_error', learning_rate=.05,
                                                                        max_iter=300, max_leaf_nodes=15,
                                                                        min_samples_leaf=40, l2_regularization=1.0,
                                                                        random_state=SEED), scale=False)}
    fitted, scores = {}, {}
    for name, model in candidates.items():
        model.fit(X['train'], change['train'])
        fitted[name] = model
        scores[name] = metrics(level['validation'], now['validation'] + model.predict(X['validation']))

    def baselines(k):
        surplus = X[k]['monthly_surplus_inr'].to_numpy()
        return {'Persistence baseline': metrics(level[k], now[k]),
                'Cash-flow extrapolation': metrics(level[k], now[k] + 12 * surplus)}
    scores.update(baselines('validation'))
    selected = min(fitted, key=lambda k: scores[k]['mae'])
    point = fitted[selected]
    test_pred = now['test'] + point.predict(X['test'])
    test_scores = metrics(level['test'], test_pred)

    # --- Calibrated 80% interval (CQR) -------------------------------------
    alpha = (1 - INTERVAL_LEVEL) / 2
    quantile = {}
    for tag, q in [('lo', alpha), ('hi', 1 - alpha)]:
        quantile[tag] = make_pipeline(HistGradientBoostingRegressor(
            loss='quantile', quantile=q, learning_rate=.05, max_iter=250, max_leaf_nodes=15,
            min_samples_leaf=60, l2_regularization=1.0, random_state=SEED), scale=False).fit(X['train'], change['train'])
    def band(k):
        return quantile['lo'].predict(X[k]), quantile['hi'].predict(X[k])
    vlo, vhi = band('validation')
    margin = conformal_margin(vlo, vhi, change['validation'], INTERVAL_LEVEL)
    def coverage(k):
        lo, hi = band(k)
        lo, hi = lo - margin, hi + margin
        pred = point.predict(X[k])
        lo, hi = np.minimum(lo, pred), np.maximum(hi, pred)  # interval always contains the point estimate
        inside = (change[k] >= lo) & (change[k] <= hi)
        return round(float(inside.mean()), 4), round(float((hi - lo).mean()), 2)
    val_cov, val_width = coverage('validation')
    test_cov, test_width = coverage('test')

    importance = permutation_importance(point, X['validation'], change['validation'], n_repeats=3, random_state=SEED,
                                        scoring='neg_mean_absolute_error', n_jobs=1)
    ranked = sorted(zip(FEATURES, importance.importances_mean), key=lambda x: -x[1])[:8]

    result = {
        'schema_version': 2, 'dataset': 'Purpose-built synthetic panel v1', 'seed': SEED,
        'selected_model': selected, 'features': FEATURES, 'target': TARGET_LEVEL,
        'target_construction': 'Predicts 12-month change in net worth, added to current net worth.',
        'rows': {k: len(v) for k, v in parts.items()}, 'users': {k: len(v) for k, v in ids.items()},
        'validation': scores, 'test': test_scores, **{'test_persistence': baselines('test')['Persistence baseline']},
        'test_baselines': baselines('test'),
        'interval': {'level': INTERVAL_LEVEL, 'method': 'Conformalized quantile regression (gradient boosting)',
                     'conformal_margin_inr': round(margin, 2), 'validation_coverage': val_cov,
                     'test_coverage': test_cov, 'test_mean_width_inr': test_width},
        'importance': [{'feature': f, 'mae_increase_inr': round(float(v), 2)} for f, v in ranked],
        'limitations': ['Synthetic outcomes only; no real-world validation.',
                        'User-disjoint evaluation, not a future-calendar holdout.',
                        'Rows from one user are correlated, so interval coverage is approximate.',
                        'MAE is an average error; use the interval, not MAE, to judge uncertainty.'],
        'python_version': platform.python_version(), 'sklearn_version': sklearn.__version__,
        'data_sha256': hashlib.sha256(args.data.read_bytes()).hexdigest()}
    joblib.dump({'pipeline': point, 'quantiles': quantile, 'conformal_margin': margin, 'target_mode': 'change',
                 'bounds': {k: [float(parts['train'][k].min()), float(parts['train'][k].max())] for k in NUMERIC[:9]},
                 'sklearn_version': sklearn.__version__}, ROOT / 'ml' / 'model.joblib', compress=3)
    (ROOT / 'ml' / 'metrics.json').write_text(json.dumps(result, indent=2))
    print(json.dumps({k: result[k] for k in ['selected_model', 'validation', 'test', 'test_baselines', 'interval', 'importance']}, indent=2))


if __name__ == '__main__':
    main()
