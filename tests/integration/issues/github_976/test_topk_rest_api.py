import json
from urllib import request

import pytest

from jina.flow import Flow
from jina.helper import random_port

TOP_K = 2
PORT = random_port()


@pytest.fixture
def query_dict():
    return {'top_k': TOP_K, 'mode': 'search', 'data': [f'text:query']}


def test_top_k_with_rest_api(query_dict):
    with Flow(rest_api=True, port_expose=PORT).add():
        query = json.dumps(query_dict).encode('utf-8')
        req = request.Request(f'http://0.0.0.0:{PORT}/api/search', data=query,
                              headers={'content-type': 'application/json'})
        resp = request.urlopen(req).read().decode('utf8')
        assert json.loads(resp)['queryset'][0]['name'] == 'VectorSearchDriver'
        assert json.loads(resp)['queryset'][0]['parameters']['top_k'] == TOP_K
        assert json.loads(resp)['queryset'][0]['priority'] == 1
