import random

import pytest

from jina.executors.segmenters import BaseSegmenter
from jina.flow import Flow
from tests import random_docs, validate_callback


class DummySegment(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = random.random()

    def segment(self):
        return [
            dict(buffer=f'aa{self._label}'.encode()),
            dict(buffer=f'bb{self._label}'.encode()),
        ]


def validate(req):
    chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert len(chunk_ids) == 80


# TODO(Deepankar): Gets stuck when `restful: True` - issues with `needs='gateway'`
@pytest.mark.skip(
    'this should fail as explained in https://github.com/jina-ai/jina/pull/730'
)
@pytest.mark.parametrize('restful', [False])
def test_this_will_fail(mocker, restful):
    f = (
        Flow(restful=restful)
        .add(name='a11', uses='DummySegment')
        .add(name='a12', uses='DummySegment', needs='gateway')
        .add(name='r1', uses='_merge_chunks', needs=['a11', 'a12'])
        .add(name='a21', uses='DummySegment', needs='gateway')
        .add(name='a22', uses='DummySegment', needs='gateway')
        .add(name='r2', uses='_merge_chunks', needs=['a21', 'a22'])
        .add(uses='_merge_chunks', needs=['r1', 'r2'])
    )

    response_mock = mocker.Mock()

    with f:
        f.index(inputs=random_docs(10, chunks_per_doc=0), on_done=response_mock)

    validate_callback(response_mock, validate)


# TODO(Deepankar): Gets stuck when `restful: True` - issues with `needs='gateway'`
@pytest.mark.timeout(180)
@pytest.mark.parametrize('restful', [False])
def test_this_should_work(mocker, restful):
    f = (
        Flow(restful=restful)
        .add(name='a1')
        .add(name='a11', uses='DummySegment', needs='a1')
        .add(name='a12', uses='DummySegment', needs='a1')
        .add(name='r1', uses='_merge_chunks', needs=['a11', 'a12'])
        .add(name='a2', needs='gateway')
        .add(name='a21', uses='DummySegment', needs='a2')
        .add(name='a22', uses='DummySegment', needs='a2')
        .add(name='r2', uses='_merge_chunks', needs=['a21', 'a22'])
        .add(uses='_merge_chunks', needs=['r1', 'r2'])
    )

    response_mock = mocker.Mock()

    with f:
        f.index(inputs=random_docs(10, chunks_per_doc=0), on_done=response_mock)

    validate_callback(response_mock, validate)
