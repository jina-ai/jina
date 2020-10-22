import pytest
import json
from urllib import request

from jina.flow import Flow


TOP_K = 2


@pytest.fixture
def query_dict():
    return {'top_k': TOP_K, 'mode': 'search', 'data': [f'text:query']}


def test_top_k_with_rest_api(query_dict):
    with Flow(rest_api=True, port_expose=45678).add(uses='_pass'):
        query = json.dumps(query_dict).encode('utf-8')
        req = request.Request('http://0.0.0.0:45678/api/search', data=query, headers={'content-type': 'application/json'})
        resp = request.urlopen(req).read().decode('utf8')
        assert json.loads(resp)['queryset'][0]['name'] == 'VectorSearchDriver'
        assert json.loads(resp)['queryset'][0]['parameters']['top_k'] == TOP_K
