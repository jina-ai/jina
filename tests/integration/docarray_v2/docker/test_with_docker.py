import os
import time

import pytest
import requests as general_requests

from jina import Flow

cur_dir = os.path.dirname(os.path.abspath(__file__))


@pytest.fixture
def executor_images_built():
    import docker

    client = docker.from_env()
    client.images.build(path=os.path.join(cur_dir, 'executor1'), tag='encoder-executor')
    client.images.build(path=os.path.join(cur_dir, 'executor2'), tag='indexer-executor')
    client.close()
    yield
    time.sleep(2)
    client = docker.from_env()
    client.containers.prune()


@pytest.mark.parametrize('protocol', ['http', 'grpc'])
def test_flow_with_docker(executor_images_built, protocol):
    from docarray import BaseDoc, DocList
    from typing import Optional, List
    from docarray.typing import NdArray

    class MyDoc(BaseDoc):
        text: str
        embedding: Optional[NdArray] = None

    class MyDocWithMatches(MyDoc):
        matches: DocList[MyDoc] = []
        scores: List[float] = []

    f = Flow(protocol=protocol).add(uses='docker://encoder-executor').add(uses='docker://indexer-executor')

    with f:
        if protocol == 'http':
            resp = general_requests.get(f'http://localhost:{f.port}/openapi.json')
            resp.json()

        sentences = ['This framework generates embeddings for each input sentence',
                     'Sentences are passed as a list of string.',
                     'The quick brown fox jumps over the lazy dog.']

        inputs = DocList[MyDoc]([MyDoc(text=sentence) for sentence in sentences])
        f.post(on='/index', inputs=inputs)
        queries = inputs[0:2]
        search_results = f.post(on='/search', inputs=queries, return_type=DocList[MyDocWithMatches])

        assert len(search_results) == len(queries)
        for result in search_results:
            assert result.text in sentences
            assert len(result.matches) == len(sentences)
            for m in result.matches:
                assert m.text in sentences
