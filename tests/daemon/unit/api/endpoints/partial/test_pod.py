from pathlib import Path

from daemon.models import PodModel

cur_dir = Path(__file__).parent
api = '/pod'


def test_pod_api(partial_pod_client):
    pod_model = PodModel()

    response = partial_pod_client.post(api, json=pod_model.dict(exclude={'log_config'}))
    assert response

    response = partial_pod_client.get(api)
    assert response

    assert response.json()['arguments']['port_jinad'] == pod_model.port_jinad

    response = partial_pod_client.delete(api)
    assert response
