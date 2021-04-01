import os
import time
import threading

import pytest
import numpy as np

from jina import Document, Flow


@pytest.fixture
def config(tmpdir):
    os.environ['JINA_FLOW_DUMP_LOAD_INTERVAL_WORKSPACE'] = str(tmpdir)
    yield
    del os.environ['JINA_FLOW_DUMP_LOAD_INTERVAL_WORKSPACE']


@pytest.fixture(scope='function')
def flow_with_dump_interval():
    return Flow().add(uses='_index', dump_interval=1)


@pytest.fixture(scope='function')
def flow_with_load_interval():
    return Flow().add(uses='_index', load_interval=1)


def test_dump_load_interval(config, flow_with_dump_interval, flow_with_load_interval):
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

    def index_flow_with_dump_interval():
        with flow_with_dump_interval as f:
            f.index(input_fn, request_size=1)

    def search_flow_with_load_interval():
        with flow_with_load_interval as f:
            for j in range(10):
                f.search(
                    Document(embedding=np.array([1, 2, 3])),
                    request_size=1,
                    on_done=lambda x: print_req(x, j),
                    top_k=999,
                )
                time.sleep(1)

    # run dump interval flow
    t = threading.Thread(target=index_flow_with_dump_interval, daemon=True)
    t.start()
    time.sleep(1)
    # run load interval flow
    search_flow_with_load_interval()
    # verify num_matches has different values since we're querying while indexing
    assert len(num_matches) > 1
