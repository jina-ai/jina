import pytest
import numpy as np
from typing import Any
from jina.drivers.evaluate import CraftEvaluationDriver
from jina.drivers.helper import DocGroundtruthPair, array2pb
from jina.executors.evaluators.craft import BaseCraftingEvaluator
from jina.proto import jina_pb2


class MockDiffEvaluator(BaseCraftingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return 'MockDiffEvaluator'

    def evaluate(self, doc_content: Any, groundtruth_content: Any, *args, **kwargs) -> float:
        return abs(len(doc_content) - len(groundtruth_content))


@pytest.fixture
def mock_diff_evaluator():
    return MockDiffEvaluator()


class SimpleEvaluateDriver(CraftEvaluationDriver):
    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture
def simple_evaluate_driver():
    def get_evaluate_driver(field_type):
        return SimpleEvaluateDriver(field=field_type)

    return get_evaluate_driver


@pytest.fixture
def ground_truth_pairs():
    def get_pairs(field_type):
        num_docs = 10
        pairs = []
        for idx in range(num_docs):
            doc = jina_pb2.Document()
            gt = jina_pb2.Document()
            if field_type == 'text':
                doc.text = 'aaa'
                gt.text = 'aaaa'
            elif field_type == 'buffer':
                doc.buffer = b'\x01\x02\x03'
                gt.buffer = b'\x01\x02\x03\x04'
            elif field_type == 'blob':
                doc.blob.CopyFrom(array2pb(np.array([1, 1, 1])))
                gt.blob.CopyFrom(array2pb(np.array([1, 1, 1, 1])))

            pairs.append(DocGroundtruthPair(doc=doc, groundtruth=gt))
        return pairs

    return get_pairs


@pytest.mark.parametrize(
    'field_type',
    ['text', 'buffer', 'blob']
)
def test_crafter_evaluate_driver(field_type, mock_diff_evaluator, simple_evaluate_driver, ground_truth_pairs):
    pairs = ground_truth_pairs(field_type)
    driver = simple_evaluate_driver(field_type)
    driver.attach(executor=mock_diff_evaluator, pea=None)
    driver._apply_all(pairs)
    for pair in pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'SimpleEvaluateDriver-MockDiffEvaluator'
        assert doc.evaluations[0].value == 1.0


class SimpleChunkEvaluateDriver(CraftEvaluationDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.eval_request = None
        self._traversal_paths = ('c',)

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def req(self) -> 'jina_pb2.Request':
        """Get the current (typed) request, shortcut to ``self.pea.request``"""
        return self.eval_request


@pytest.fixture
def simple_chunk_evaluate_driver():
    def get_evaluate_driver(field_type):
        return SimpleChunkEvaluateDriver(field=field_type)

    return get_evaluate_driver


@pytest.fixture
def eval_request():
    def request(field_type):
        num_docs = 10
        req = jina_pb2.Request.IndexRequest()
        for idx in range(num_docs):
            doc = req.docs.add()
            gt = req.groundtruths.add()
            chunk_doc = doc.chunks.add()
            chunk_gt = gt.chunks.add()
            chunk_doc.granularity = 1
            chunk_gt.granularity = 1
            if field_type == 'text':
                chunk_doc.text = 'aaa'
                chunk_gt.text = 'aaaa'
            elif field_type == 'buffer':
                chunk_doc.buffer = b'\x01\x02\x03'
                chunk_gt.buffer = b'\x01\x02\x03\x04'
            elif field_type == 'blob':
                chunk_doc.blob.CopyFrom(array2pb(np.array([1, 1, 1])))
                chunk_gt.blob.CopyFrom(array2pb(np.array([1, 1, 1, 1])))
        return req

    return request


@pytest.mark.parametrize(
    'field_type',
    ['text', 'buffer', 'blob']
)
def test_crafter_evaluate_driver_in_chunks(field_type,
                                           simple_chunk_evaluate_driver,
                                           mock_diff_evaluator,
                                           eval_request):
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    req = eval_request(field_type)
    driver = simple_chunk_evaluate_driver(field_type)
    driver.attach(executor=mock_diff_evaluator, pea=None)
    driver.eval_request = req
    driver()

    assert len(req.docs) == len(req.groundtruths)
    assert len(req.docs) == 10
    for doc in req.docs:
        assert len(doc.evaluations) == 0  # evaluation done at chunk level
        assert len(doc.chunks) == 1
        chunk = doc.chunks[0]
        assert len(chunk.evaluations) == 1  # evaluation done at chunk level
        assert chunk.evaluations[0].op_name == 'SimpleChunkEvaluateDriver-MockDiffEvaluator'
        assert chunk.evaluations[0].value == 1.0
