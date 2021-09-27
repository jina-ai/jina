from pathlib import Path

from daemon.models import PeaModel

cur_dir = Path(__file__).parent
api = '/pea'


def test_pea_api(partial_pea_client):
    pea_model = PeaModel()

    response = partial_pea_client.post(api, json=pea_model.dict(exclude={'log_config'}))
    assert response

    response = partial_pea_client.get(api)
    assert response
    assert response.json()['arguments']['port_jinad'] == pea_model.port_jinad

    response = partial_pea_client.delete(api)
    assert response
