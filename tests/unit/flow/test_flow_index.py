import os
import time
import pytest
import shutil
import numpy as np
from jina.flow import Flow
from jina.drivers.helper import array2pb
from jina.proto import jina_pb2


def random_docs(num_docs, chunks_per_doc=5, embed_dim=10):
    c_id = 0
    for j in range(num_docs):
        d = jina_pb2.Document()
        d.id = j
        d.text = b'hello world'
        d.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
        for k in range(chunks_per_doc):
            c = d.chunks.add()
            c.text = 'i\'m chunk %d from doc %d' % (c_id, j)
            c.embedding.CopyFrom(array2pb(np.random.random([embed_dim])))
            c.id = c_id
            c.parent_id = j
            c_id += 1
        yield d


def rm_files(file_paths):
    for file_path in file_paths:
        if os.path.exists(file_path):
            if os.path.isfile(file_path):
                os.remove(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path, ignore_errors=False, onerror=None)


cur_dir = os.path.dirname(os.path.abspath(__file__))


def random_queries(num_docs, chunks_per_doc=5):
    for j in range(num_docs):
        d = jina_pb2.Document()
        for k in range(chunks_per_doc):
            dd = d.chunks.add()
            dd.id = k + 1  # 1-indexed
        yield d


@pytest.mark.skipif('GITHUB_WORKFLOW' in os.environ, reason='skip the network test on github workflow')
def test_shards_insufficient_data():
    """THIS IS SUPER IMPORTANT FOR TESTING SHARDS

    IF THIS FAILED, DONT IGNORE IT, DEBUG IT
    """
    index_docs = 3
    parallel = 4

    def validate(req):
        assert len(req.docs) == 1
        assert len(req.docs[0].matches) == index_docs

        for d in req.docs[0].matches:
            assert hasattr(d, 'weight')
            assert d.weight
            assert d.meta_info == b'hello world'

    f = Flow().add(name='doc_pb', uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'), parallel=parallel,
                   separated_workspace=True)
    with f:
        f.index(input_fn=random_docs(index_docs), random_doc_id=False)

    time.sleep(2)
    with f:
        pass
    time.sleep(2)
    f = Flow().add(name='doc_pb', uses=os.path.join(cur_dir, '../yaml/test-docpb.yml'), parallel=parallel,
                   separated_workspace=True, polling='all', uses_after='_merge_all')
    with f:
        f.search(input_fn=random_queries(1, index_docs), random_doc_id=False, output_fn=validate,
                 callback_on_body=True)
    time.sleep(2)
    rm_files(['test-docshard-tmp'])
