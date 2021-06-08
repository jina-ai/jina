import pytest
import numpy as np

from jina import Client, Executor, Document, DocumentArray, requests, Flow


class TestExecutor(Executor):
    @requests
    def encode(self, docs: DocumentArray, **kwargs):
        for doc in docs:
            doc.embedding = np.full((3, 5), doc.id)


@pytest.fixture(scope='function')
def flow():
    return Flow(port_expose=56789).add(uses=TestExecutor)


@pytest.fixture(scope='function')
def docs_to_index():
    return DocumentArray(
        [
            Document(id=1),
            Document(id=2),
        ]
    )


def test_grpc_client(flow, docs_to_index):
    with flow as f:
        f.index(inputs=docs_to_index)
    with flow as f:
        f.block()
    client = Client(host='localhost', port=56789)
    client.post(on='/search', inputs=Document(id=3), on_done=print)


def test_rest_client():
    with Flow(port_expose=56789).add(uses=TestExecutor) as f:
        f.index(
            inputs=DocumentArray(
                [
                    Document(id=1),
                    Document(id=2),
                ]
            )
        )
    with Flow(port_expose=56789).add(uses=TestExecutor) as f:
        f.use_rest_gateway()
        f.block()

    client = Client(host='localhost', port=56789, is_restful=True)
    client.post(on='/search', inputs=Document(id=3), on_done=print)
