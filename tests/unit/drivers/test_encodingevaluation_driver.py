import numpy as np
import pytest

from jina.drivers.evaluate import NDArrayEvaluateDriver
from jina.drivers.helper import DocGroundtruthPair
from jina.executors.evaluators.embedding import BaseEmbeddingEvaluator
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


class MockDiffEvaluator(BaseEmbeddingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def metric(self):
        return 'MockDiffEvaluator'

    def evaluate(self, actual: 'np.array', desired: 'np.array', *args, **kwargs) -> float:
        """"
        :param actual: the embedding of the document (resulting from an Encoder)
        :param desired: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        return abs(sum(actual - desired) / len(actual))


@pytest.fixture
def mock_diff_evaluator():
    return MockDiffEvaluator()


class SimpleEvaluateDriver(NDArrayEvaluateDriver):
    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture
def simple_evaluate_driver():
    return SimpleEvaluateDriver()


@pytest.fixture
def ground_truth_pairs():
    num_docs = 10
    pairs = []
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        gt = jina_pb2.Document()
        GenericNdArray(doc.embedding).value = np.array([1, 1])
        GenericNdArray(gt.embedding).value = np.array([2, 2])
        pairs.append(DocGroundtruthPair(doc=doc, groundtruth=gt))
    return pairs


def test_encoding_evaluate_driver(mock_diff_evaluator,
                                  simple_evaluate_driver,
                                  ground_truth_pairs):
    simple_evaluate_driver.attach(executor=mock_diff_evaluator, pea=None)
    simple_evaluate_driver._apply_all(ground_truth_pairs)
    for pair in ground_truth_pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'SimpleEvaluateDriver-MockDiffEvaluator'
        assert doc.evaluations[0].value == 1.0


class SimpleChunkEvaluateDriver(NDArrayEvaluateDriver):

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
    return SimpleChunkEvaluateDriver()


@pytest.fixture
def eval_request():
    num_docs = 10
    req = jina_pb2.Request.IndexRequest()
    for idx in range(num_docs):
        doc = req.docs.add()
        gt = req.groundtruths.add()
        chunk_doc = doc.chunks.add()
        chunk_gt = gt.chunks.add()
        chunk_doc.granularity = 1
        chunk_gt.granularity = 1
        GenericNdArray(chunk_doc.embedding).value = np.array([1, 1])
        GenericNdArray(chunk_gt.embedding).value = np.array([2, 2])
    return req


def test_encoding_evaluate_driver_embedding_in_chunks(simple_chunk_evaluate_driver,
                                                      mock_diff_evaluator,
                                                      eval_request):
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    simple_chunk_evaluate_driver.attach(executor=mock_diff_evaluator, pea=None)
    simple_chunk_evaluate_driver.eval_request = eval_request
    simple_chunk_evaluate_driver()

    assert len(eval_request.docs) == len(eval_request.groundtruths)
    assert len(eval_request.docs) == 10
    for doc in eval_request.docs:
        assert len(doc.evaluations) == 0  # evaluation done at chunk level
        assert len(doc.chunks) == 1
        chunk = doc.chunks[0]
        assert len(chunk.evaluations) == 1  # evaluation done at chunk level
        assert chunk.evaluations[0].op_name == 'SimpleChunkEvaluateDriver-MockDiffEvaluator'
        assert chunk.evaluations[0].value == 1.0
