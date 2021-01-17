def test_main(fastapi_client):
    response = fastapi_client.get('/')
    assert response.status_code == 200
    assert response.json() == {}


def test_status(fastapi_client):
    response = fastapi_client.get('/status')
    assert response.status_code == 200
    for k in ('jina', 'peas', 'pods', 'flows', 'used_memory'):
        assert k in response.json()
