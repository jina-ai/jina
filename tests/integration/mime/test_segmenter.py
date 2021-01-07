import os

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


class DummySegment(BaseSegmenter):
    def craft(self):
        return [dict(buffer=b'aa'), dict(buffer=b'bb')]


def validate_factory(mock):
    def validate(req):
        mock()
        chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
        assert len(chunk_ids) == len(set(chunk_ids))
        assert len(chunk_ids) == 20

    return validate


def test_dummy_seg(mocker):
    mock = mocker.Mock()
    f = Flow().add(uses='DummySegment')
    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=validate_factory(mock))
    mock.assert_called_once()


def test_dummy_seg_random(mocker):
    mock = mocker.Mock()
    f = Flow().add(uses=os.path.join(cur_dir, '../../unit/yaml/dummy-seg-random.yml'))
    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=validate_factory(mock))
    mock.assert_called_once()


def test_dummy_seg_not_random(mocker):
    mock = mocker.Mock()
    f = Flow().add(uses=os.path.join(cur_dir, '../../unit/yaml/dummy-seg-not-random.yml'))
    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=validate_factory(mock))
    mock.assert_called_once()
