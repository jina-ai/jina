import os

import numpy as np
import pytest
import requests

from jina import Client, Document, Flow
from tests import random_docs

# noinspection PyUnresolvedReferences
from tests.integration.crud import CrudIndexer

PARAMS = {'top_k': 10}


def rest_post(f, endpoint, documents):
    data = [d.to_dict() for d in documents]
    if endpoint == 'delete':
        method = 'delete'
    elif endpoint == 'update':
        method = 'put'
    else:
        method = 'post'
    response = getattr(requests, method)(
        f'http://localhost:{f.port}/{endpoint}',
        json={'data': data, 'parameters': PARAMS},
    )
    if response.status_code != 200:
        raise Exception(f'exception in status code {response.status_code}')

    return response.json()


@pytest.mark.parametrize('rest', [True, False])
def test_crud(tmpdir, rest):
    os.environ['RESTFUL'] = 'http' if rest else 'grpc'
    os.environ['WORKSPACE'] = str(tmpdir)

    with Flow.load_config('flow.yml') as f:
        c = Client(port=f.port)
        original_docs = list(random_docs(10, chunks_per_doc=0))
        if rest:
            rest_post(f, 'index', original_docs)
        else:
            c.post(on='/index', inputs=original_docs, return_responses=True)

    with Flow.load_config('flow.yml') as f:
        c = Client(port=f.port)
        inputs = list(random_docs(1))
        if rest:
            results = rest_post(f, 'search', inputs)
            matches = results['data'][0]['matches']
            for doc in results['data']:
                assert Document.from_dict(doc).text == 'hello world'
        else:
            results = c.post(
                on='/search', inputs=inputs, parameters=PARAMS, return_responses=True
            )
            matches = results[0].docs[0].matches
            for doc in results[0].docs:
                assert doc.text == 'hello world'

        assert len(matches) == 10

    with Flow.load_config('flow.yml') as f:
        c = Client(port=f.port)
        inputs = list(random_docs(5, chunks_per_doc=0))

        if rest:
            rest_post(f, 'delete', inputs)

        else:
            c.post(on='/delete', inputs=inputs, return_responses=True)

    with Flow.load_config('flow.yml') as f:
        c = Client(port=f.port)
        inputs = list(random_docs(1))

        if rest:
            results = rest_post(f, 'search', inputs)
            matches = results['data'][0]['matches']

        else:
            results = c.post(
                on='/search', inputs=inputs, parameters=PARAMS, return_responses=True
            )
            matches = results[0].docs[0].matches

        assert len(matches) == 5

    updated_docs = list(
        random_docs(5, chunks_per_doc=5, start_id=5, text='hello again')
    )

    with Flow.load_config('flow.yml') as f:
        c = Client(port=f.port)
        if rest:
            rest_post(f, 'update', updated_docs)
        else:
            c.post(on='/update', inputs=updated_docs)

    with Flow.load_config('flow.yml') as f:
        c = Client(port=f.port)
        inputs = list(random_docs(1))
        if rest:
            results = rest_post(f, 'search', inputs)
            matches = sorted(
                results['data'][0]['matches'], key=lambda match: match['id']
            )
        else:
            results = c.post(
                on='/search', inputs=inputs, parameters=PARAMS, return_responses=True
            )
            matches = sorted(results[0].docs[0].matches, key=lambda match: match.id)

        assert len(matches) == 5

        for match, updated_doc in zip(matches, updated_docs):
            if isinstance(match, dict):
                match = Document.from_dict(match)

            assert updated_doc.id == match.id
            assert updated_doc.text == match.text
            np.testing.assert_array_equal(updated_doc.embedding, match.embedding)
            assert len(match.chunks) == 5
            assert len(match.chunks) == len(updated_doc.chunks)
            for match_chunk, updated_doc_chunk in zip(match.chunks, updated_doc.chunks):
                assert match_chunk.text == updated_doc_chunk.text
                np.testing.assert_array_equal(
                    match_chunk.embedding, updated_doc_chunk.embedding
                )
