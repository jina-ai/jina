from pathlib import Path

from daemon.models import DaemonID
from daemon.models.enums import UpdateOperation
from jina import Client, Document

cur_dir = Path(__file__).parent
api = '/flow'


def test_flow_api(monkeypatch, partial_flow_client):
    response = partial_flow_client.post(
        api,
        params={
            'filename': f'{cur_dir}/good_flow_dummy.yml',
            'id': DaemonID('jflow'),
            'port_expose': 1234,
        },
    )
    assert response

    response = partial_flow_client.get(api)
    assert response
    assert response.json()['arguments']['port_expose'] == 1234

    def response_checker(response):
        assert response.docs[0].content == 'https://jina.ai'

    Client(port_expose=1234).post(
        on='/any_endpoint', inputs=Document(), on_done=response_checker
    )

    # the pod used in this flow is not a compound pod and does not support ROLLING_UPDATE
    response = partial_flow_client.put(
        api,
        params={
            'kind': UpdateOperation.ROLLING_UPDATE,
            'dump_path': '',
            'pod_name': 'dummy_executor',
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
