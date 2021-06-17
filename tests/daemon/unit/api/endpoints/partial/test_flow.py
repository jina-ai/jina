from pathlib import Path

from daemon.models import DaemonID
from daemon.models.enums import UpdateOperation

cur_dir = Path(__file__).parent
api = '/flow'


def test_flow_api(monkeypatch, partial_flow_client):
    response = partial_flow_client.post(
        api,
        params={
            'filename': f'{cur_dir}/../good_flow.yml',
            'id': DaemonID('jflow'),
            'port_expose': 1234,
        },
    )
    assert response

    response = partial_flow_client.get(api)
    assert response
    assert response.json()['arguments']['port_expose'] == 1234

    # the pod used in this flow is not a compound pod and does not support ROLLING_UPDATE
    response = partial_flow_client.put(
        api,
        params={
            'kind': UpdateOperation.ROLLING_UPDATE,
            'dump_path': '',
            'pod_name': 'hello',
            'shards': 1,
        },
    )
    assert response.status_code == 400

    response = partial_flow_client.put(
        api,
        params={
            'kind': UpdateOperation.DUMP,
            'dump_path': '',
            'pod_name': 'hello',
            'shards': 1,
        },
    )
    assert response

    response = partial_flow_client.delete(api)
    assert response
