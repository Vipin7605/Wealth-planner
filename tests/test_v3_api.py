"""API tests for v3 features: Monte Carlo, ML interval, security hardening, password change."""
import copy, os, pathlib, tempfile
os.environ.setdefault('DATABASE_URL', 'sqlite:///' + str(pathlib.Path(tempfile.mkdtemp()) / 'v3.db'))
import backend.main as main
from fastapi.testclient import TestClient
from backend.main import app

PW = 'a-long-password-42'


def signup(c, email):
    return c.post('/api/register', json={'email': email, 'password': PW})


def test_health_reports_version_and_database():
    with TestClient(app) as c:
        body = c.get('/api/health').json()
        assert body['status'] == 'ok' and body['version'] == '3.0.0'


def test_security_headers_and_cache_policy():
    with TestClient(app) as c:
        r = c.get('/api/health')
        csp = r.headers['content-security-policy']
        assert "script-src 'self'" in csp and "frame-ancestors 'none'" in csp and "object-src 'none'" in csp
        assert r.headers['cache-control'] == 'no-store' and r.headers['x-frame-options'] == 'DENY'
        assert 'unsafe-eval' not in csp and "script-src 'self' 'unsafe" not in csp
        assert c.get('/').headers['cache-control'] == 'no-cache'


def test_monte_carlo_requires_login_and_validates_input():
    with TestClient(app) as c:
        assert c.post('/api/monte-carlo', json={}).status_code == 401
        c.post('/api/demo', json={})
        assert c.post('/api/monte-carlo', json={'options': {'simulations': 10}}).status_code == 422
        assert c.post('/api/monte-carlo', json={'options': {'volatility': 90}}).status_code == 422
        assert c.post('/api/monte-carlo', json={'options': {'bogus': 1}}).status_code == 422
        too_early = c.post('/api/monte-carlo', json={'options': {'end_age': 55}})
        assert too_early.status_code == 422 and 'retirement age' in too_early.json()['detail']


def test_monte_carlo_uses_saved_plan_or_unsaved_draft_without_saving():
    with TestClient(app) as c:
        c.post('/api/demo', json={})
        saved = c.get('/api/state').json()
        base = c.post('/api/monte-carlo', json={'options': {'simulations': 500}})
        assert base.status_code == 200
        body = base.json()
        assert 0 <= body['survival_probability'] <= 1 and body['timeline'][0]['age'] == saved['state']['profile']['age']
        draft = copy.deepcopy(saved['state'])  # deep copy: `saved` must stay untouched for the comparison below
        draft['fire']['monthly_spending'] = 5000
        preview = c.post('/api/monte-carlo', json={'state': draft, 'options': {'simulations': 500}}).json()
        assert preview['survival_probability'] > body['survival_probability']
        assert c.get('/api/state').json() == saved  # preview must not save


def test_ml_model_is_available_and_returns_a_containing_interval():
    with TestClient(app) as c:
        c.post('/api/demo', json={})
        r = c.get('/api/ml').json()
        assert r['available'] is True
        interval = r['interval']
        assert interval['low'] <= r['prediction'] <= interval['high']
        assert interval['level'] == 0.8 and 0.7 <= interval['test_coverage'] <= 0.95
        assert r['metrics']['selected_model'] and 'Cash-flow extrapolation' in r['metrics']['validation']
        assert c.get('/api/ml').json()['prediction'] == r['prediction']  # cached artifact, stable output


def test_unknown_email_and_wrong_password_look_identical_and_lockout_applies():
    with TestClient(app) as c:
        signup(c, 'victim@example.com')
        c.post('/api/logout', json={})
        main.attempts.clear()
        a = c.post('/api/login', json={'email': 'victim@example.com', 'password': 'wrong-password-1'})
        b = c.post('/api/login', json={'email': 'nobody@example.com', 'password': 'wrong-password-1'})
        assert a.status_code == b.status_code == 401 and a.json() == b.json()
        for _ in range(12):
            main.attempts.clear()
            last = c.post('/api/login', json={'email': 'victim@example.com', 'password': 'wrong-password-1'})
        assert last.status_code == 429
        main.attempts.clear()
        # The lock also protects against a correct guess arriving mid-attack.
        assert c.post('/api/login', json={'email': 'victim@example.com', 'password': PW}).status_code == 429
        main.failures.clear()
        main.attempts.clear()
        assert c.post('/api/login', json={'email': 'victim@example.com', 'password': PW}).status_code == 200


def test_password_change_flow_and_session_revocation():
    with TestClient(app) as a, TestClient(app) as b:
        main.attempts.clear()
        signup(a, 'change@example.com')
        assert b.post('/api/login', json={'email': 'change@example.com', 'password': PW}).status_code == 200
        assert a.post('/api/password', json={'current_password': 'not-it', 'new_password': 'brand-new-password-9'}).status_code == 403
        assert a.post('/api/password', json={'current_password': PW, 'new_password': PW}).status_code == 422
        assert a.post('/api/password', json={'current_password': PW, 'new_password': 'short'}).status_code == 422
        assert a.post('/api/password', json={'current_password': PW, 'new_password': 'brand-new-password-9'}).status_code == 200
        assert a.get('/api/me').status_code == 200          # this session continues
        assert b.get('/api/me').status_code == 401          # the other device is signed out
        a.post('/api/logout', json={})
        main.attempts.clear()
        assert a.post('/api/login', json={'email': 'change@example.com', 'password': PW}).status_code == 401
        main.attempts.clear()
        assert a.post('/api/login', json={'email': 'change@example.com', 'password': 'brand-new-password-9'}).status_code == 200


def test_demo_workspace_cannot_change_password():
    with TestClient(app) as c:
        c.post('/api/demo', json={})
        assert c.post('/api/password', json={'current_password': 'x', 'new_password': 'brand-new-password-9'}).status_code == 403


def test_import_flags_duplicates_of_saved_expenses():
    with TestClient(app) as c:
        c.post('/api/demo', json={})
        existing = c.get('/api/state').json()['state']['expenses'][0]
        text = f"Name,Amount\n{existing['name']},{existing['amount']}\nBrand new item,\"₹1,20,000\""
        r = c.post('/api/parse-expenses', json={'text': text}).json()
        assert [i['name'] for i in r['items']] == [existing['name'], 'Brand new item']
        assert r['items'][1]['amount'] == 120000
        assert r['duplicate_ids'] == [r['items'][0]['id']]


def test_fire_advisor_mentions_simulated_probability():
    with TestClient(app) as c:
        c.post('/api/demo', json={})
        answer = c.post('/api/advisor', json={'question': 'Can I retire early with FIRE?'}).json()['answer']
        assert 'chance your investments last' in answer and '%' in answer
