import os

import pytest

from ..helpers import create_flow, invoke_requests, get_results

cur_dir = os.path.dirname(os.path.abspath(__file__))
compose_yml = os.path.join(cur_dir, 'docker-compose.yml')
flow_yml = os.path.join(cur_dir, 'flow.yml')
pod_dir = os.path.join(cur_dir, 'pods')


@pytest.mark.parametrize('docker_compose', [compose_yml], indirect=['docker_compose'])
def test_flow(docker_compose):
    flow_id = create_flow(flow_yml, pod_dir)['flow_id']
    print(f'Flow created with id {flow_id}')

    for x in range(100):
        text = 'text:hey, dude ' + str(x)
        print(f'Indexing with text: {text}')
        r = invoke_requests(method='post',
                            url='http://0.0.0.0:45678/api/index',
                            payload={'top_k': 10, 'data': [text]})
        assert r is not None
        text_indexed = r['index']['docs'][0]['text']
        print(f'Got response text_indexed: {text_indexed}')
        assert text_indexed == text

    r = invoke_requests(method='get',
                        url=f'http://localhost:8000/flow/{flow_id}')
    assert r is not None
    assert r['status_code'] == 200

    r = invoke_requests(method='delete',
                        url=f'http://localhost:8000/flow?flow_id={flow_id}')
    assert r is not None
    assert r['status_code'] == 200

    r = create_flow(flow_yml, pod_dir)
    assert r is not None
    flow_id = r['flow_id']
    print(f'Flow created with id {flow_id}')

    texts_matched = get_results(query='text:anything will match the same')
    assert len(texts_matched['search']['docs'][0]['matches']) == 10

    r = invoke_requests(method='get',
                        url=f'http://localhost:8000/flow/{flow_id}')
    assert r is not None
    assert r['status_code'] == 200

    r = invoke_requests(method='delete',
                        url=f'http://localhost:8000/flow?flow_id={flow_id}')
    assert r is not None
    assert r['status_code'] == 200
