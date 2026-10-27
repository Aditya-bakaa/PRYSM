import json
import time
import httpx
import pytest
from fastapi.testclient import TestClient
from app import agents, main
from app.reference_data import DEFAULT_PROBLEM
from app.schemas import Problem

client = TestClient(main.app)


def test_health_reference():
    assert client.get('/api/health').json()['status'] == 'ok'
    ref = client.get('/api/reference').json()
    assert ref['scoring']['carbon_horizon_years'] == 30
    assert ref['weights'] == {'cost': .3, 'carbon': .3, 'resilience': .4}


def test_demo_api_e2e():
    response = client.post('/api/arena/run', json={'mode': 'demo'})
    assert response.status_code == 200, response.text
    data = response.json()
    assert len(data['evaluations']) == 3
    assert data['mode'] == 'demo'
    assert all(a['source'] == 'fixture' for a in data['timings']['agents'])
    assert data['synthesis']['hybrid_evaluation']['baseline_metrics']['total_cost'] > 0
    assert data['timings']['total_ms'] >= data['timings']['evaluation_ms']


def test_bad_request_returns_422():
    assert client.post('/api/arena/run', json={'mode': 'invalid'}).status_code == 422
    assert client.post('/api/arena/run', json={'problem': {**DEFAULT_PROBLEM, 'floor_area_m2': -2}}).status_code == 422


def test_integrity_demo_is_separate():
    r = client.get('/api/integrity-demo')
    assert r.status_code == 200, r.text
    data = r.json()
    assert data['honest']['baseline_metrics'] == data['false']['baseline_metrics']
    assert data['honest']['integrity_penalty'] == 0
    assert data['false']['integrity_penalty'] == 8
    assert data['honest']['final_score'] > data['false']['final_score']


def test_evaluate_api():
    p = agents._fixture('GreenAdvocate').model_dump()
    r = client.post('/api/evaluate', json=p)
    assert r.status_code == 200
    assert r.json()['agent_name'] == 'GreenAdvocate'


def test_all_live_calls_fail_uses_fallback(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    monkeypatch.setattr(agents, '_generate', lambda name, problem: (_ for _ in ()).throw(httpx.ReadTimeout('blocked')))
    proposals, timings, notes = agents.run_agents(Problem(**DEFAULT_PROBLEM), mode='live')
    assert len(proposals) == 3
    assert len(notes) == 3
    assert all(x.source == 'fallback' for x in timings)


def test_partial_failure_preserves_success(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    def fake(name, _):
        if name == 'CostOptimizer': raise httpx.ReadTimeout('broken')
        return agents._fixture(name)
    monkeypatch.setattr(agents, '_generate', fake)
    _, timings, notes = agents.run_agents(Problem(**DEFAULT_PROBLEM), mode='live')
    assert [x.source for x in timings] == ['fallback', 'live', 'live']
    assert len(notes) == 1


def test_agents_run_parallel(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    def slow(name, _):
        time.sleep(.11)
        return agents._fixture(name)
    monkeypatch.setattr(agents, '_generate', slow)
    started = time.perf_counter()
    _, timings, _ = agents.run_agents(Problem(**DEFAULT_PROBLEM), mode='live')
    elapsed = time.perf_counter() - started
    assert elapsed < .28  # sequential would exceed .33s
    assert all(x.latency_ms >= 100 for x in timings)


def test_cache_and_refresh(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    main._CACHE.clear()
    calls = []
    def fake(name, problem):
        calls.append(name)
        return agents._fixture(name)
    monkeypatch.setattr(agents, '_generate', fake)
    for i, refresh in enumerate((False, False, True)):
        response = client.post('/api/arena/run', json={'mode': 'live', 'refresh': refresh})
        assert response.status_code == 200, response.text
        assert response.json()['cached'] == (i == 1)
    assert len(calls) == 6


def test_missing_key_fallback(monkeypatch):
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    _, timings, notes = agents.run_agents(Problem(**DEFAULT_PROBLEM), mode='live')
    assert len(notes) == 3
    assert all(a.source == 'fallback' for a in timings)


def test_json_schema_invalid_response_falls_back(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    class FakeResponse:
        status_code = 200
        headers = {}
        def raise_for_status(self): pass
        def json(self):
            return {'choices': [{'message': {'content': json.dumps({
                'material': 'nonexistent', 'features': [], 'summary': 'wrong material',
                'accepted_tradeoff': 'Some long tradeoff', 'refused_tradeoff': 'Another tradeoff',
            })}}]}
    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs): return FakeResponse()
    monkeypatch.setattr(agents.httpx, 'Client', FakeClient)
    _, timings, _ = agents.run_agents(Problem(**DEFAULT_PROBLEM), mode='live')
    assert {x.source for x in timings} == {'fallback'}


def test_rate_limit_fallback_after_bounded_retry(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    monkeypatch.setattr(agents, 'sleep', lambda _: None)
    calls = []
    class RateLimited:
        status_code = 429
        headers = {}
        def raise_for_status(self): raise httpx.HTTPStatusError('rate limited', request=httpx.Request('POST','https://groq.test'), response=httpx.Response(429))
    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs):
            calls.append(1)
            return RateLimited()
    monkeypatch.setattr(agents.httpx, 'Client', FakeClient)
    _, timings, _ = agents.run_agents(Problem(**DEFAULT_PROBLEM), mode='live')
    assert {x.source for x in timings} == {'fallback'}
    assert len(calls) == 6  # two attempts for each of three agents


def test_valid_provider_payload(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    response_text = json.dumps({
        'material': 'fly_ash_brick', 'features': ['raised_plinth', 'rainwater_harvesting'],
        'summary': 'Affordable building using a raised floor and water harvesting.',
        'accepted_tradeoff': 'Accepts less resilience than reinforced concrete.',
        'refused_tradeoff': 'Refuses an unaffordable steel frame option.',
        'claims': [],
    })
    class FakeResponse:
        status_code = 200
        headers = {}
        def raise_for_status(self): pass
        def json(self): return {'choices': [{'message': {'content': response_text}}]}
    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs): return FakeResponse()
    monkeypatch.setattr(agents.httpx, 'Client', FakeClient)
    proposals, timings, notes = agents.run_agents(Problem(**DEFAULT_PROBLEM), 'live')
    assert all(x.source == 'live' for x in timings)
    assert all(p.material == 'fly_ash_brick' for p in proposals)
    assert not notes


def test_provider_timeout_retry_then_fallback(monkeypatch):
    monkeypatch.setenv('GROQ_API_KEY', 'fake-key')
    monkeypatch.setattr(agents, 'sleep', lambda _: None)
    calls = []
    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, *args, **kwargs):
            calls.append(1)
            raise httpx.ReadTimeout('timed out')
    monkeypatch.setattr(agents.httpx, 'Client', FakeClient)
    _, timings, notes = agents.run_agents(Problem(**DEFAULT_PROBLEM), 'live')
    assert all(x.source == 'fallback' for x in timings)
    assert len(calls) == 6
    assert len(notes) == 3
