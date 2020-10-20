import pytest
import numpy as np

from typing import Optional
from jina.drivers.evaluate import LoadGroundTruthDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2


class MockGroundTruthIndexer(BaseKVIndexer):

    def add(self, keys: 'np.ndarray', vectors: 'np.ndarray', *args, **kwargs):
        pass

    def query(self, key: int) -> Optional['jina_pb2.Document']:
        if key in self.db.keys():
            return self.db[key]
        else:
            return None

    def get_query_handler(self):
        pass

    def get_add_handler(self):
        pass

    def get_create_handler(self):
        pass

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        doc1 = jina_pb2.Document()
        doc1.tags['id'] = 1
        doc1.tags['groundtruth'] = True
        doc2 = jina_pb2.Document()
        doc2.tags['id'] = 2
        doc2.tags['groundtruth'] = True
        doc4 = jina_pb2.Document()
        doc4.tags['id'] = 4
        doc4.tags['groundtruth'] = True
        self.db = {
            1: doc1.SerializeToString(),
            2: doc2.SerializeToString(),
            4: doc4.SerializeToString()
        }


class SimpleLoadGroundTruthDriver(LoadGroundTruthDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eval_request = None

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def req(self) -> 'jina_pb2.Request':
        """Get the current (typed) request, shortcut to ``self.pea.request``"""
        return self.eval_request


@pytest.fixture(scope='function')
def simple_load_groundtruth_driver():
    return SimpleLoadGroundTruthDriver()


@pytest.fixture(scope='function')
def mock_groundtruth_indexer():
    return MockGroundTruthIndexer()


@pytest.fixture(scope='function')
def eval_request():
    req = jina_pb2.Request.SearchRequest()
    # doc: 1
    # doc: 2
    # doc: 3
    # doc: 4
    # doc: 5 - will be missing from KV indexer
    for idx in range(5):
        doc = req.docs.add()
        doc.tags['id'] = idx + 1
    return req


def test_load_groundtruth_driver(mock_groundtruth_indexer, simple_load_groundtruth_driver, eval_request):
    simple_load_groundtruth_driver.attach(executor=mock_groundtruth_indexer, pea=None)
    simple_load_groundtruth_driver.eval_request = eval_request
    simple_load_groundtruth_driver()

    assert len(eval_request.docs) == 3
    assert len(eval_request.groundtruths) == 3

    for groundtruth in eval_request.groundtruths:
        assert groundtruth.tags['groundtruth']

    assert eval_request.groundtruths[0].tags['id'] == 1
    assert eval_request.groundtruths[1].tags['id'] == 2
    # index 3 and 5 have no groundtruth in the KVIndexer
    assert eval_request.groundtruths[2].tags['id'] == 4
