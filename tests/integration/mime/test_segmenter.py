import os

import pytest

from jina.executors.segmenters import BaseSegmenter
from jina.flow import Flow
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


class DummySegment(BaseSegmenter):
    def segment(self):
        return [dict(buffer=b'aa'), dict(buffer=b'bb')]


def validate(req):
    chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert len(chunk_ids) == 20


@pytest.mark.parametrize('restful', [False, True])
def test_dummy_seg(mocker, restful):
    mock = mocker.Mock()
    f = Flow(restful=restful).add(uses='DummySegment')
    with f:
        f.index(inputs=random_docs(10, chunks_per_doc=0), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_dummy_seg_random(mocker, restful):
    mock = mocker.Mock()
    f = Flow(restful=restful).add(uses=os.path.join(cur_dir, 'dummy-seg-random.yml'))
    with f:
        f.index(inputs=random_docs(10, chunks_per_doc=0), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate)


@pytest.mark.parametrize('restful', [False, True])
def test_dummy_seg_not_random(mocker, restful):
    mock = mocker.Mock()
    f = Flow(restful=restful).add(
        uses=os.path.join(cur_dir, 'dummy-seg-not-random.yml')
    )
    with f:
        f.index(inputs=random_docs(10, chunks_per_doc=0), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate)
