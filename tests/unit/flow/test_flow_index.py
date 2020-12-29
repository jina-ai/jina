import os
import time

import pytest

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.types.document.uid import UniqueId
from tests import random_docs, rm_files

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_queries(num_docs, chunks_per_doc=5):
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.id = UniqueId(j)
        for k in range(chunks_per_doc):
            dd = d.chunks.add()
            dd.id = UniqueId(num_docs + j * chunks_per_doc + k)
        yield d


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
def test_shards_insufficient_data(mocker):
    """THIS IS SUPER IMPORTANT FOR TESTING SHARDS

    IF THIS FAILED, DONT IGNORE IT, DEBUG IT
    """
    index_docs = 3
    parallel = 4

    mock = mocker.Mock()
    def validate(req):
        mock()
        assert len(req.docs) == 1
        assert len(req.docs[0].matches) == index_docs

        for d in req.docs[0].matches:
            assert hasattr(d, 'weight')
            assert d.weight
            assert d.meta_info == b'hello world'

    f = Flow().add(name='doc_pb',
                   uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'),
                   parallel=parallel,
                   separated_workspace=True)
    with f:
        f.index(input_fn=random_docs(index_docs))

    time.sleep(2)
    with f:
        pass
    time.sleep(2)
    f = Flow().add(name='doc_pb',
                   uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'),
                   parallel=parallel,
                   separated_workspace=True, polling='all', uses_after='_merge_chunks')
    with f:
        f.search(input_fn=random_queries(1, index_docs),
                 callback_on='body',
                 on_done=validate
                 )
    time.sleep(2)
    rm_files(['test-docshard-tmp'])
    mock.assert_called_once()
