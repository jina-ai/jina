import os
import json
import time

import pytest
from urllib import request

from jina.flow import Flow
from jina.proto import jina_pb2
from jina import Document
from jina import helper
from jina.executors.encoders import BaseEncoder
from tests import validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))

_document_fields = sorted(set(list(jina_pb2.DocumentProto().DESCRIPTOR.fields_by_name)))

# check if this can be bypassed
IGNORED_FIELDS = ['embedding', 'score']


@pytest.fixture
def docs():
    return [Document(id=f'{idx}', text=f'doc{idx}') for idx in range(10)]


def test_no_matches_grpc(mocker, docs):
    def validate_response(resp):
        for doc in resp.search.docs:
            assert len(doc.matches) == 0

    mock_on_done = mocker.Mock()
    with Flow().add(uses='_pass') as f:
        f.search(inputs=docs, on_done=mock_on_done)
    validate_callback(mock_on_done, validate_response)


@pytest.fixture
def query_dict():
    return {'top_k': 3, 'mode': 'search', 'data': [f'text:query']}


class MockExecutor(BaseEncoder):
    def get_docs(self, req_type):
        if req_type == 'ControlRequest':
            return []
        driver = self._drivers[req_type][0]
        return driver.docs

    def __call__(self, req_type, *args, **kwargs):
        if req_type == 'ControlRequest':
            for d in self._drivers[req_type]:
                d()
        else:
            for doc in self.get_docs(req_type):
                doc.tags['tag'] = 'test'


def test_no_matches_rest(query_dict):
    port = helper.random_port()
    with Flow(rest_api=True, port_expose=port).add(uses='!MockExecutor'):
        # temporarily adding sleep
        time.sleep(0.5)
        query = json.dumps(query_dict).encode('utf-8')
        req = request.Request(
            f'http://0.0.0.0:{port}/search',
            data=query,
            headers={'content-type': 'application/json'},
        )
        resp = request.urlopen(req).read().decode('utf8')
        doc = json.loads(resp)['search']['docs'][0]
        present_keys = sorted(doc.keys())
        for field in _document_fields:
            if field not in IGNORED_FIELDS + ['buffer', 'content', 'blob']:
                assert field in present_keys
