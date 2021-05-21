import os

import pytest

from jina import Document, requests, Executor, Flow
from tests import random_docs, validate_callback

cur_dir = os.path.dirname(os.path.abspath(__file__))


class DummySegment(Executor):
    """dummySegment represents a basic segment of two values"""

    @requests
    def segment(self, docs, *args, **kwargs):
        """create a dummy segment of two values."""
        for d in docs:
            d.chunks = [Document(buffer=b'aa'), Document(buffer=b'bb')]


def validate(req):
    """simple check for validating tests."""
    chunk_ids = [c.id for d in req.docs for c in d.chunks]
    assert len(chunk_ids) == len(set(chunk_ids))
    assert len(chunk_ids) == 20


@pytest.mark.parametrize('restful', [False, True])
@pytest.mark.parametrize(
    'uses',
    [
        'DummySegment',
        os.path.join(cur_dir, 'yaml/dummy-seg-not-random.yml'),
    ],
)
def test_seg(mocker, restful, uses):
    """tests segments provided the uses for a flow."""
    mock = mocker.Mock()
    f = Flow(restful=restful).add(uses=uses)
    with f:
        f.index(inputs=random_docs(10, chunks_per_doc=0), on_done=mock)
    mock.assert_called_once()
    validate_callback(mock, validate)
