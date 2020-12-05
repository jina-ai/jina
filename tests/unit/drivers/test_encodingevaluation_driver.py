import numpy as np
import pytest

from jina import Document, Request
from jina.drivers.evaluate import NDArrayEvaluateDriver
from jina.executors.evaluators.embedding import BaseEmbeddingEvaluator
from jina.proto import jina_pb2
from jina.types.document.helper import DocGroundtruthPair


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
        doc = Document(embedding=np.array([1, 1]))
        gt = Document(embedding=np.array([2, 2]))
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
    def req(self) -> 'jina_pb2.RequestProto':
        """Get the current (typed) request, shortcut to ``self.pea.request``"""
        return self.eval_request

    @property
    def expect_parts(self) -> int:
        return 1


@pytest.fixture
def simple_chunk_evaluate_driver():
    return SimpleChunkEvaluateDriver()


@pytest.fixture
def eval_request():
    num_docs = 10
    req = jina_pb2.RequestProto()
    for idx in range(num_docs):
        doc = Document(req.index.docs.add())
        gt = Document(req.index.groundtruths.add())
        doc.update_id()
        gt.update_id()
        chunk_doc = doc.chunks.new()
        chunk_gt = gt.chunks.new()
        chunk_doc.embedding = np.array([1, 1])
        chunk_gt.embedding = np.array([2, 2])
    return Request(req)


def test_encoding_evaluate_driver_embedding_in_chunks(simple_chunk_evaluate_driver,
                                                      mock_diff_evaluator,
                                                      eval_request):
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    simple_chunk_evaluate_driver.attach(executor=mock_diff_evaluator, pea=None)
    simple_chunk_evaluate_driver.eval_request = eval_request
    simple_chunk_evaluate_driver()

    ed = list(eval_request.docs)
    eg = list(eval_request.groundtruths)
    assert len(ed) == len(eg)
    assert len(ed) == 10
    for doc in ed:
        assert len(doc.evaluations) == 0  # evaluation done at chunk level
        dc = list(doc.chunks)
        assert len(dc) == 1
        chunk = dc[0]
        assert len(chunk.evaluations) == 1  # evaluation done at chunk level
        assert chunk.evaluations[0].op_name == 'SimpleChunkEvaluateDriver-MockDiffEvaluator'
        assert chunk.evaluations[0].value == 1.0
