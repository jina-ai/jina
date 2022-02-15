import random

import pytest

from jina import Flow, Executor, requests, Document
from tests import random_docs, validate_callback


class DummySegment(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = random.random()

    @requests
    def segment(self, docs, *args, **kwargs):
        for d in docs:
            d.chunks = [
                Document(blob=f'aa{self._label}'.encode()),
                Document(blob=f'bb{self._label}'.encode()),
            ]


class Merger(Executor):
    @requests
    def merge(self, docs, **kwargs):
        return docs


def validate(da):
    chunk_ids = [c.id for d in da for c in d.chunks]
    assert len(chunk_ids) == 80


@pytest.mark.skip(
    'this should fail as explained in https://github.com/jina-ai/jina/pull/730'
)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_this_will_fail(protocol):
    f = (
        Flow(protocol=protocol)
        .add(name='a11', uses='DummySegment')
        .add(name='a12', uses='DummySegment', needs='gateway')
        .add(name='r1', needs=['a11', 'a12'])
        .add(name='a21', uses='DummySegment', needs='gateway')
        .add(name='a22', uses='DummySegment', needs='gateway')
        .add(name='r2', needs=['a21', 'a22'])
        .add(needs=['r1', 'r2'])
    )

    with f:
        da = f.index(inputs=random_docs(10, chunks_per_doc=0))

    validate(da)


@pytest.mark.timeout(180)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_this_should_work(protocol):
    f = (
        Flow(protocol=protocol)
        .add(name='a1')
        .add(name='a11', uses='DummySegment', needs='a1')
        .add(name='a12', uses='DummySegment', needs='a1')
        .add(name='r1', uses=Merger, needs=['a11', 'a12'])
        .add(name='a2', needs='gateway')
        .add(name='a21', uses='DummySegment', needs='a2')
        .add(name='a22', uses='DummySegment', needs='a2')
        .add(name='r2', uses=Merger, needs=['a21', 'a22'])
        .add(uses=Merger, needs=['r1', 'r2'])
    )

    with f:
        da = f.index(inputs=random_docs(10, chunks_per_doc=0))

    validate(da)
