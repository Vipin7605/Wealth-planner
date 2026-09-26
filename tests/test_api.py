import os,tempfile,pathlib
os.environ['DATABASE_URL']='sqlite:///'+str(pathlib.Path(tempfile.mkdtemp())/'test.db')
from fastapi.testclient import TestClient
from backend.main import app

def signup(client,email):return client.post('/api/register',json={'email':email,'password':'a-long-password-42'})
def test_auth_isolation_validation_conflict_export_and_delete():
    with TestClient(app) as a,TestClient(app) as b:
        assert a.get('/api/state').status_code==401
        assert signup(a,'alice@example.com').status_code==201
        assert signup(b,'bob@example.com').status_code==201
        assert 'httponly' in a.cookies.jar._cookies['testserver.local']['/']['wealth_session']._rest.keys().__str__().lower()
        start=a.get('/api/state').json();start['state']['profile']['name']='Alice plan'
        assert a.put('/api/state',json=start).status_code==200
        assert a.put('/api/state',json=start).status_code==409
        assert b.get('/api/state').json()['state']['profile']['name']=='My plan'
        assert a.get('/api/state').json()['state']['profile']['name']=='Alice plan'
        invalid=a.get('/api/state').json();invalid['state']['income']=[{'id':'x','name':'bad','amount':-1}]
        assert a.put('/api/state',json=invalid).status_code==422
        assert a.post('/api/logout',headers={'Origin':'https://evil.example'},json={}).status_code==403
        assert a.post('/api/logout',data='bad').status_code==415
        assert a.get('/api/export').json()['schema_version']==1
        assert 'net_worth' in a.get('/api/export?kind=csv').text
        assert a.request('DELETE','/api/account',json={}).status_code==200
        assert a.get('/api/state').status_code==401
        assert b.get('/api/state').status_code==200

def test_demo_and_calculation_endpoints():
    with TestClient(app) as c:
        assert c.post('/api/demo',json={}).status_code==200
        assert c.get('/api/me').json()['demo'] is True
        assert c.get('/api/dashboard').json()['summary']['net_worth']==743000
        sim=c.post('/api/scenario',json={'years':5,'extra_income':1000}).json()
        assert sim['scenario']['points'][-1]['net_worth']>sim['baseline']['points'][-1]['net_worth']
        assert c.post('/api/scenario',json={'years':31}).status_code==422
        plans=c.get('/api/debt-plan?extra=5000').json()
        assert plans['avalanche']['months']>0
        assert c.get('/api/debt-plan?extra=-1').status_code==422
        chat=c.post('/api/advisor',json={'question':'Is my emergency fund enough?'}).json()
        assert chat['mode']=='rule_based' and '145,000' in chat['answer']
        assert c.post('/api/logout',json={}).status_code==200
        assert c.get('/api/state').status_code==401

def test_login_and_duplicate_registration():
    with TestClient(app) as c:
        assert signup(c,'login@example.com').status_code==201
        assert signup(c,'login@example.com').status_code==409
        c.post('/api/logout',json={})
        assert c.post('/api/login',json={'email':'login@example.com','password':'wrong-password'}).status_code==401
        assert c.post('/api/login',json={'email':'login@example.com','password':'a-long-password-42'}).status_code==200

def test_ml_inference_and_csv_preview_do_not_mutate_state():
    with TestClient(app) as c:
        c.post('/api/demo',json={})
        original=c.get('/api/state').json()
        preview=c.post('/api/parse-expenses',json={'text':'name,amount\nGroceries,1200'}).json()
        assert preview['items'][0]['category']=='Food'
        assert c.get('/api/state').json()==original
        ml=c.get('/api/ml')
        assert ml.status_code==200
        result=ml.json()
        if result['available']:
            assert isinstance(result['prediction'],(int,float))
            assert result['metrics']['users']=={'train':700,'validation':200,'test':100}

def test_restore_preview_normalizes_without_mutating():
    with TestClient(app) as c:
        assert c.post('/api/restore-preview',json={}).status_code==401
        c.post('/api/demo',json={});original=c.get('/api/state').json()
        preview=c.post('/api/restore-preview',json={'profile':{'name':'Restored plan'}})
        assert preview.status_code==200 and preview.json()['state']['profile']['name']=='Restored plan'
        assert 'fire' in preview.json()['state']
        assert c.get('/api/state').json()==original
        assert c.post('/api/restore-preview',json={'income':[{'id':'x','name':'bad','amount':-1}]}).status_code==422
        assert c.put('/api/state',json={'state':preview.json()['state'],'version':original['version']}).status_code==200
        assert c.get('/api/state').json()['state']['profile']['name']=='Restored plan'
