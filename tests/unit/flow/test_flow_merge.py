import random

import pytest

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from tests import random_docs


class DummySegment(BaseSegmenter):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._label = random.random()

    def craft(self):
        return [dict(buffer=f'aa{self._label}'.encode()), dict(buffer=f'bb{self._label}'.encode())]


def validate(req):
    chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert len(chunk_ids) == 80


@pytest.mark.skip('this should fail as explained in https://github.com/jina-ai/jina/pull/730')
def test_this_will_fail(mocker):
    f = (Flow().add(name='a11', uses='DummySegment')
         .add(name='a12', uses='DummySegment', needs='gateway')
         .add(name='r1', uses='_merge_chunks', needs=['a11', 'a12'])
         .add(name='a21', uses='DummySegment', needs='gateway')
         .add(name='a22', uses='DummySegment', needs='gateway')
         .add(name='r2', uses='_merge_chunks', needs=['a21', 'a22'])
         .add(uses='_merge_chunks', needs=['r1', 'r2']))

    response_mock = mocker.Mock(wrap=validate)

    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=response_mock)

    response_mock.assert_called()


@pytest.mark.timeout(180)
def test_this_should_work(mocker):
    f = (Flow()
         .add(name='a1')
         .add(name='a11', uses='DummySegment', needs='a1')
         .add(name='a12', uses='DummySegment', needs='a1')
         .add(name='r1', uses='_merge_chunks', needs=['a11', 'a12'])
         .add(name='a2', needs='gateway')
         .add(name='a21', uses='DummySegment', needs='a2')
         .add(name='a22', uses='DummySegment', needs='a2')
         .add(name='r2', uses='_merge_chunks', needs=['a21', 'a22'])
         .add(uses='_merge_chunks', needs=['r1', 'r2']))

    response_mock = mocker.Mock(wrap=validate)

    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=response_mock)

    response_mock.assert_called()

