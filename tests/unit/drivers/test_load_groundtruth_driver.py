from typing import Optional, Iterable

import numpy as np
import pytest

from jina import Request
from jina.drivers.evaluate import LoadGroundTruthDriver
from jina.executors.indexers import BaseKVIndexer
from jina.proto import jina_pb2
from jina.types.document import Document


class MockGroundTruthIndexer(BaseKVIndexer):
    def add(
        self, keys: Iterable[str], values: Iterable[bytes], *args, **kwargs
    ) -> None:
        pass

    def query(self, key: str) -> Optional[bytes]:
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
        doc1 = Document()
        doc1.id = '01' * 8
        doc1.tags['groundtruth'] = True
        doc2 = Document()
        doc2.id = '02' * 8
        doc2.tags['groundtruth'] = True
        doc4 = Document()
        doc4.id = '04' * 8
        doc4.tags['groundtruth'] = True
        self.db = {
            doc1.id: doc1.SerializeToString(),
            doc2.id: doc2.SerializeToString(),
            doc4.id: doc4.SerializeToString(),
        }


class SimpleLoadGroundTruthDriver(LoadGroundTruthDriver):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eval_request = None

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def req(self) -> 'jina_pb2.RequestProto':
        """Get the current (typed) request, shortcut to ``self.pea.request``"""
        return self.eval_request

    @property
    def expect_parts(self) -> int:
        return 1


@pytest.fixture(scope='function')
def simple_load_groundtruth_driver():
    return SimpleLoadGroundTruthDriver()


@pytest.fixture(scope='function')
def mock_groundtruth_indexer():
    return MockGroundTruthIndexer()


@pytest.fixture(scope='function')
def eval_request():
    req = Request()
    req.request_type = 'search'
    # doc: 1
    # doc: 2
    # doc: 3
    # doc: 4
    # doc: 5 - will be missing from KV indexer
    for idx in range(5):
        dp = Document()
        dp.id = f'0{str(idx + 1)}' * 8
        req.docs.append(dp)
    return req


def test_load_groundtruth_driver(
    mock_groundtruth_indexer, simple_load_groundtruth_driver, eval_request
):
    simple_load_groundtruth_driver.attach(
        executor=mock_groundtruth_indexer, runtime=None
    )
    simple_load_groundtruth_driver.eval_request = eval_request
    simple_load_groundtruth_driver()

    assert len(eval_request.docs) == 3
    assert len(eval_request.groundtruths) == 3

    for groundtruth in eval_request.groundtruths:
        assert groundtruth.tags['groundtruth']

    assert eval_request.groundtruths[0].id == '01' * 8
    assert eval_request.groundtruths[1].id == '02' * 8
    # index 3 and 5 have no groundtruth in the KVIndexer
    assert eval_request.groundtruths[2].id == '04' * 8
