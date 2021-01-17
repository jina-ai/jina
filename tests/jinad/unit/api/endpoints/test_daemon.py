from fastapi.testclient import TestClient

from daemon import _get_app

client = TestClient(_get_app())


def test_main():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == {}


def test_status():
    response = client.get('/status')
    assert response.status_code == 200
    for k in ('jina', 'peas', 'pods', 'flows', 'memory'):
        assert k in response.json()
