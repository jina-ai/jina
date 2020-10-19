import pytest

from jina.drivers.evaluate import RankingEvaluationDriver
from jina.drivers.helper import DocGroundtruthPair
from jina.executors.evaluators.rank import BaseRankingEvaluator
from jina.proto import jina_pb2


class MockPrecisionEvaluator(BaseRankingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(eval_at=2, *args, **kwargs)

    @property
    def name(self):
        return f'MockPrecision@{self.eval_at}'

    def evaluate(self, matches_ids, groundtruth_ids, *args, **kwargs) -> float:
        ret = 0.0
        for doc_id in matches_ids[:self.eval_at]:
            if doc_id in groundtruth_ids:
                ret += 1.0

        divisor = min(self.eval_at, len(groundtruth_ids))
        if divisor == 0.0:
            return 0.0
        else:
            return ret / divisor


@pytest.fixture
def mock_precision_evaluator():
    return MockPrecisionEvaluator()


class SimpleEvaluateDriver(RankingEvaluationDriver):
    @property
    def exec_fn(self):
        return self._exec_fn


@pytest.fixture
def simple_evaluate_driver():
    return SimpleEvaluateDriver()


@pytest.fixture
def ground_truth_pairs():
    num_docs = 10

    def add_matches(doc: jina_pb2.Document, num_matches):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx

    pairs = []
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        gt = jina_pb2.Document()
        add_matches(doc, num_docs)
        add_matches(gt, num_docs)
        pairs.append(DocGroundtruthPair(doc=doc, groundtruth=gt))
    return pairs


def test_ranking_evaluate_driver(mock_precision_evaluator,
                                 simple_evaluate_driver,
                                 ground_truth_pairs):
    simple_evaluate_driver.attach(executor=mock_precision_evaluator, pea=None)
    simple_evaluate_driver._apply_all(ground_truth_pairs)
    for pair in ground_truth_pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'SimpleEvaluateDriver-MockPrecision@2'
        assert doc.evaluations[0].value == 1.0


class SimpleChunkEvaluateDriver(RankingEvaluationDriver):

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
    num_matches = 1

    def add_matches(doc: jina_pb2.Document):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx

    req = jina_pb2.Request.IndexRequest()
    for idx in range(num_docs):
        doc = req.docs.add()
        gt = req.groundtruths.add()
        chunk_doc = doc.chunks.add()
        chunk_gt = gt.chunks.add()
        chunk_doc.granularity = 1
        chunk_gt.granularity = 1
        add_matches(chunk_doc)
        add_matches(chunk_gt)
    return req


def test_ranking_evaluate_driver_matches_in_chunks(simple_chunk_evaluate_driver,
                                                   mock_precision_evaluator,
                                                   eval_request):
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    simple_chunk_evaluate_driver.attach(executor=mock_precision_evaluator, pea=None)
    simple_chunk_evaluate_driver.eval_request = eval_request
    simple_chunk_evaluate_driver()

    assert len(eval_request.docs) == len(eval_request.groundtruths)
    assert len(eval_request.docs) == 10
    for doc in eval_request.docs:
        assert len(doc.evaluations) == 0  # evaluation done at chunk level
        assert len(doc.chunks) == 1
        chunk = doc.chunks[0]
        assert len(chunk.evaluations) == 1  # evaluation done at chunk level
        assert chunk.evaluations[0].op_name == 'SimpleChunkEvaluateDriver-MockPrecision@2'
        assert chunk.evaluations[0].value == 1.0


@pytest.fixture
def eval_request_with_unmatching_struct():
    num_docs = 10
    num_matches = 1

    def add_matches(doc: jina_pb2.Document):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx

    req = jina_pb2.Request.SearchRequest()
    for idx in range(num_docs):
        doc = req.docs.add()
        gt = req.groundtruths.add()
        chunk_doc = doc.chunks.add()
        chunk_gt = gt.chunks.add()
        chunk_doc.granularity = 1
        chunk_gt.granularity = 1
        add_matches(chunk_doc)
        add_matches(chunk_gt)
        chunk_gt_wrong = gt.chunks.add()
    return req


def test_evaluate_assert_doc_groundtruth_structure(simple_chunk_evaluate_driver,
                                                   mock_precision_evaluator,
                                                   eval_request_with_unmatching_struct):
    simple_chunk_evaluate_driver.attach(executor=mock_precision_evaluator, pea=None)
    simple_chunk_evaluate_driver.eval_request = eval_request_with_unmatching_struct
    with pytest.raises(AssertionError):
        simple_chunk_evaluate_driver()
