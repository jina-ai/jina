import os
import time

import pytest

from jina.flow import Flow
from jina.proto import jina_pb2
from tests import random_docs, rm_files

cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_queries(num_docs, chunks_per_doc=5):
    for j in range(num_docs):
        d = jina_pb2.DocumentProto()
        d.id = j
        for k in range(chunks_per_doc):
            dd = d.chunks.add()
            dd.id = num_docs + j * chunks_per_doc + k
        yield d


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
@pytest.mark.parametrize('restful', [False, True])
def test_shards_insufficient_data(mocker, restful):
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

    f = (Flow(restful=restful)
         .add(name='doc_pb',
              uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'),
              parallel=parallel))
    with f:
        f.index(input_fn=random_docs(index_docs))

    time.sleep(2)
    with f:
        pass
    time.sleep(2)
    f = (Flow(restful=restful)
         .add(name='doc_pb',
              uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'),
              parallel=parallel,
              polling='all',
              uses_after='_merge_chunks'))
    with f:
        f.search(input_fn=random_queries(1, index_docs),

                 on_done=validate)
    time.sleep(2)
    rm_files(['test-docshard-tmp'])
    mock.assert_called_once()
