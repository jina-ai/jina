import os
import pytest

from jina.executors.crafters import BaseSegmenter
from jina.flow import Flow
from tests import random_docs

cur_dir = os.path.dirname(os.path.abspath(__file__))


class DummySegment(BaseSegmenter):
    def craft(self):
        return [dict(buffer=b'aa'), dict(buffer=b'bb')]


def validate(req):
    chunk_ids = [c.id for d in req.index.docs for c in d.chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert len(chunk_ids) == 20


@pytest.mark.parametrize('rest_api', [True, False])
def test_dummy_seg(mocker, rest_api):
    response_mock = mocker.Mock(wraps=validate)
    f = Flow(rest_api=rest_api).add(uses='DummySegment')
    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('rest_api', [True, False])
def test_dummy_seg_random(mocker, rest_api):
    response_mock = mocker.Mock(wraps=validate)
    f = Flow(rest_api=rest_api).add(uses=os.path.join(cur_dir, '../../unit/yaml/dummy-seg-random.yml'))
    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=response_mock)
    response_mock.assert_called()


@pytest.mark.parametrize('rest_api', [True, False])
def test_dummy_seg_not_random(mocker, rest_api):
    response_mock = mocker.Mock(wraps=validate)
    f = Flow(rest_api=rest_api).add(uses=os.path.join(cur_dir, '../../unit/yaml/dummy-seg-not-random.yml'))
    with f:
        f.index(input_fn=random_docs(10, chunks_per_doc=0), on_done=response_mock)
    response_mock.assert_called()
