import os
import random
import string
from itertools import chain
from pathlib import Path

import numpy as np
import pytest
import requests

from jina.executors.indexers import BaseIndexer

from jina import Document
from jina.flow import Flow

random.seed(0)
np.random.seed(0)


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_REST_DIR'] = str(tmpdir)
    yield
    del os.environ['JINA_REST_DIR']


def send_rest_request(flow_file, endpoint, method, data):
    json = {'data': data}
    with Flow.load_config(flow_file) as flow:
        url = f'http://0.0.0.0:{flow.port_expose}/{endpoint}'
        r = getattr(requests, method)(url, json=json)

        if r.status_code != 200:
            # TODO status_code should be 201 for index
            raise Exception(
                f'api request failed, url: {url}, status: {r.status_code}, content: {r.content} data: {data}'
            )
    return r


def send_rest_index_request(flow_file, documents):
    data = [document.dict() for document in documents]
    return send_rest_request(flow_file, 'index', 'post', data)


def send_rest_update_request(flow_file, documents):
    data = [document.dict() for document in documents]
    return send_rest_request(flow_file, 'update', 'put', data)


def send_rest_delete_request(flow_file, ids):
    return send_rest_request(flow_file, 'delete', 'delete', ids)


def send_rest_search_request(flow_file, documents):
    data = [document.dict() for document in documents]
    return send_rest_request(flow_file, 'search', 'post', data)


def random_docs(start, end):
    documents = []
    for j in range(start, end):
        d = Document()
        d.id = j
        d.tags['id'] = j
        d.text = ''.join(
            random.choice(string.ascii_lowercase) for _ in range(10)
        ).encode('utf8')
        d.embedding = np.random.random([10 + np.random.randint(0, 1)])
        documents.append(d)
    return documents


def get_ids_to_delete(start, end):
    return [str(idx) for idx in range(start, end)]


def validate_index_size(num_indexed_docs):
    from jina.executors.compound import CompoundExecutor

    path_compound = Path(
        CompoundExecutor.get_component_workspace_from_compound_workspace(
            os.environ['JINA_REST_DIR'], 'chunk_indexer', 0
        )
    )
    path = Path(os.environ['JINA_REST_DIR'])
    bin_files = list(path_compound.glob('*.bin')) + list(path.glob('*.bin'))
    assert len(bin_files) > 0
    for index_file in bin_files:
        index = BaseIndexer.load(str(index_file))
        assert index.size == num_indexed_docs


@pytest.mark.parametrize('flow_file', ['flow.yml', 'flow_vector.yml'])
def test_delete_vector(config, flow_file):
    NUMBER_OF_SEARCHES = 5

    def validate_results(resp, num_matches):
        documents = resp.json()['search']['docs']
        assert len(documents) == NUMBER_OF_SEARCHES
        for doc in documents:
            # TODO if there are no matches, the rest api should return an empty list instead of not having the attribute
            assert len(Document(doc).matches) == num_matches

    send_rest_index_request(flow_file, random_docs(0, 10))
    validate_index_size(10)

    search_result = send_rest_search_request(
        flow_file, random_docs(0, NUMBER_OF_SEARCHES)
    )
    validate_results(search_result, 10)

    delete_ids = []
    for d in random_docs(0, 10):
        delete_ids.append(d.id)
        for c in d.chunks:
            delete_ids.append(c.id)

    send_rest_delete_request(flow_file, delete_ids)

    validate_index_size(0)

    search_result = send_rest_search_request(
        flow_file, random_docs(0, NUMBER_OF_SEARCHES)
    )
    validate_results(search_result, 0)


def test_delete_kv(config):
    flow_file = 'flow_kv.yml'

    def validate_results(resp, num_matches):
        assert len(resp.json()['search']['docs']) == num_matches

    send_rest_index_request(flow_file, random_docs(0, 10))
    validate_index_size(10)

    search_result = send_rest_search_request(
        flow_file, chain(random_docs(2, 5), random_docs(100, 120))
    )
    validate_results(search_result, 3)

    send_rest_delete_request(flow_file, get_ids_to_delete(0, 3))
    validate_index_size(7)

    search_result = send_rest_search_request(flow_file, random_docs(2, 4))
    validate_results(search_result, 1)


@pytest.mark.parametrize('flow_file', ['flow.yml', 'flow_vector.yml'])
def test_update_vector(config, flow_file):
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_results(resp, has_changed):
        docs = resp.json()['search']['docs']
        assert len(docs) == NUMBER_OF_SEARCHES
        hash_set_before = [hash(d.embedding.tobytes()) for d in docs_before]
        hash_set_updated = [hash(d.embedding.tobytes()) for d in docs_updated]
        for doc_dictionary in docs:
            doc = Document(doc_dictionary)
            assert len(doc.matches) == 10
            for match in doc.matches:
                h = hash(match.embedding.tobytes())
                if has_changed:
                    assert h not in hash_set_before
                    assert h in hash_set_updated
                else:
                    assert h in hash_set_before
                    assert h not in hash_set_updated

    send_rest_index_request(flow_file, docs_before)
    validate_index_size(10)

    search_result = send_rest_search_request(
        flow_file, random_docs(0, NUMBER_OF_SEARCHES)
    )
    validate_results(search_result, has_changed=False)

    send_rest_update_request(flow_file, docs_updated)
    validate_index_size(10)

    search_result = send_rest_search_request(
        flow_file, random_docs(0, NUMBER_OF_SEARCHES)
    )
    validate_results(search_result, has_changed=True)


def test_update_kv(config):
    flow_file = 'flow_kv.yml'
    NUMBER_OF_SEARCHES = 1
    docs_before = list(random_docs(0, 10))
    docs_updated = list(random_docs(0, 10))

    def validate_results(resp):
        assert len(resp.json()['search']['docs']) == NUMBER_OF_SEARCHES

    send_rest_index_request(flow_file, docs_before)
    validate_index_size(10)

    search_result = send_rest_search_request(
        flow_file, random_docs(0, NUMBER_OF_SEARCHES)
    )
    validate_results(search_result)

    send_rest_update_request(flow_file, docs_updated)
    validate_index_size(10)

    search_result = send_rest_search_request(
        flow_file, random_docs(0, NUMBER_OF_SEARCHES)
    )
    validate_results(search_result)
