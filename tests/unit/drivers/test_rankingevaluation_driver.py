import pytest

from jina.drivers.evaluate import RankEvaluateDriver
from jina.drivers.helper import DocGroundtruthPair
from jina.executors.evaluators.rank import BaseRankingEvaluator
from jina.proto import jina_pb2


class MockPrecisionEvaluator(BaseRankingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(eval_at=2, *args, **kwargs)

    @property
    def metric(self):
        return f'MockPrecision@{self.eval_at}'

    def evaluate(self, matches_ids, desired_ids, *args, **kwargs) -> float:
        ret = 0.0
        for doc_id in matches_ids[:self.eval_at]:
            if doc_id in desired_ids:
                ret += 1.0

        divisor = min(self.eval_at, len(desired_ids))
        if divisor == 0.0:
            return 0.0
        else:
            return ret / divisor


@pytest.fixture
def mock_precision_evaluator():
    return MockPrecisionEvaluator()


class SimpleEvaluateDriver(RankEvaluateDriver):
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
            match.tags['score'] = idx

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


class SimpleChunkEvaluateDriver(RankEvaluateDriver):

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


def _compute_dcg(gains):
    from math import log
    """Compute discounted cumulative gain."""
    ret = 0.0
    for score, position in zip(gains[1:], range(2, len(gains) + 1)):
        ret += score / log(position, 2)
    return gains[0] + ret


def _compute_idcg(gains):
    """Compute ideal discounted cumulative gain."""
    sorted_gains = sorted(gains, reverse=True)
    return _compute_dcg(sorted_gains)


class MockNDCGEvaluator(BaseRankingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(eval_at=2, *args, **kwargs)

    @property
    def metric(self):
        return f'MockNDCG@{self.eval_at}'

    def evaluate(self, actual, desired, *args, **kwargs) -> float:
        """"
        :param actual: the scores predicted by the search system.
        :param desired: the expected score given by user as groundtruth.
        :return the evaluation metric value for the request document.
        """
        actual_at_k = actual[:self.eval_at]
        desired_at_k = desired[:self.eval_at]
        if len(actual) < 2:
            raise ValueError(f'Expecting gains with minimal length of 2, {len(actual)} received.')
        dcg = _compute_dcg(gains=actual_at_k)
        idcg = _compute_idcg(gains=desired_at_k)
        if idcg == 0.0:
            return 0.0
        else:
            return dcg / idcg


@pytest.fixture
def mock_ndcg_evaluator():
    return MockNDCGEvaluator()


@pytest.fixture
def simple_evaluate_driver_ndcg():
    return SimpleEvaluateDriver(id_tag='score')


def test_ranking_ndcg_evaluate_driver(mock_ndcg_evaluator,
                                      simple_evaluate_driver_ndcg,
                                      ground_truth_pairs):
    simple_evaluate_driver_ndcg.attach(executor=mock_ndcg_evaluator, pea=None)
    simple_evaluate_driver_ndcg._apply_all(ground_truth_pairs)
    for pair in ground_truth_pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'SimpleEvaluateDriver-MockNDCG@2'
        assert doc.evaluations[0].value == 1.0
