import multiprocessing
import os
import time

import numpy as np
import pytest

from jina import Document, Flow


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_FLOW_DUMP_LOAD_INTERVAL_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['JINA_FLOW_DUMP_LOAD_INTERVAL_WORKSPACE']


@pytest.fixture(scope='function')
def index_flow():
    return Flow().add(uses='_index', shards=3)


@pytest.fixture(scope='function')
def search_flow():
    return Flow().add(uses='_index', shards=3, polling='all')


def test_rolling_reload(config, index_flow, search_flow):
    """Run index and search in parallel, we should observe number of documents while searching
    keep increasing.
    We expect while indexing and quering, we should get a new `num_matches` for each run.
    """
    num_matches = set()

    def input_fn():
        for idx in range(10):
            time.sleep(1)
            yield Document(embedding=np.array([1, 2, 3]), tags={'idx': idx})

    def print_req(req, j):
        print(f'{j}-time got {len(req.docs[0].matches)} results')
        num_matches.add(len(req.docs[0].matches))

    def index_flow_with_shards():
        with index_flow as f:
            f.index(input_fn, request_size=1)

    def search_flow_rolling_reload():
        with search_flow as f:
            for j in range(10):
                f.reload(targets=f'pod0/{j % 3}')
                f.search(
                    Document(embedding=np.array([1, 2, 3])),
                    request_size=1,
                    on_done=lambda x: print_req(x, j),
                    top_k=999,
                )
                time.sleep(1)

    # run dump interval flow
    t = multiprocessing.Process(target=index_flow_with_shards)
    t.start()
    time.sleep(1)
    # run load interval flow
    search_flow_rolling_reload()
    # verify num_matches has different values since we're querying while indexing
    assert len(num_matches) > 1
