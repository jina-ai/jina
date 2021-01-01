import pytest

from jina.drivers.evaluate import RankEvaluateDriver
from jina.executors.evaluators.rank.precision import PrecisionEvaluator
from jina.proto import jina_pb2
from jina.types.document.helper import DocGroundtruthPair


class SimpleRankEvaluateDriver(RankEvaluateDriver):

    def __init__(self, field: str, *args, **kwargs):
        super().__init__(field, *args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def expect_parts(self) -> int:
        return 1


class RunningAvgRankEvaluateDriver(RankEvaluateDriver):

    def __init__(self, field: str, *args, **kwargs):
        super().__init__(field, running_avg=True, *args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn

    @property
    def expect_parts(self) -> int:
        return 1


@pytest.fixture
def simple_rank_evaluate_driver(field):
    return SimpleRankEvaluateDriver(field)


@pytest.fixture
def ruuningavg_rank_evaluate_driver(field):
    return RunningAvgRankEvaluateDriver(field)


@pytest.fixture
def ground_truth_pairs():
    num_docs = 10

    def add_matches(doc: jina_pb2.DocumentProto, num_matches):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx
            match.score.value = idx

    pairs = []
    for idx in range(num_docs):
        doc = jina_pb2.DocumentProto()
        gt = jina_pb2.DocumentProto()
        add_matches(doc, num_docs)
        add_matches(gt, num_docs)
        pairs.append(DocGroundtruthPair(doc=doc, groundtruth=gt))
    return pairs


@pytest.mark.parametrize('field', ['tags__id', 'score__value'])
def test_ranking_evaluate_driver(simple_rank_evaluate_driver,
                                 ground_truth_pairs):
    simple_rank_evaluate_driver.attach(executor=PrecisionEvaluator(eval_at=2), runtime=None)
    simple_rank_evaluate_driver._apply_all(ground_truth_pairs)
    for pair in ground_truth_pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'Precision@N'
        assert doc.evaluations[0].value == 1.0


@pytest.mark.parametrize('field', ['tags__id', 'score__value'])
def test_ranking_evaluate_driver(ruuningavg_rank_evaluate_driver,
                                 ground_truth_pairs):
    ruuningavg_rank_evaluate_driver.attach(executor=PrecisionEvaluator(eval_at=2), runtime=None)
    ruuningavg_rank_evaluate_driver._apply_all(ground_truth_pairs)
    for pair in ground_truth_pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'Precision@N'
        assert doc.evaluations[0].value == 1.0


class SimpleChunkRankEvaluateDriver(RankEvaluateDriver):

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
def simple_chunk_rank_evaluate_driver():
    return SimpleChunkRankEvaluateDriver()


@pytest.fixture
def eval_request():
    num_docs = 10
    num_matches = 1

    def add_matches(doc: jina_pb2.DocumentProto):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx

    req = jina_pb2.RequestProto.IndexRequestProto()
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


def test_ranking_evaluate_driver_matches_in_chunks(simple_chunk_rank_evaluate_driver,
                                                   eval_request):
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    simple_chunk_rank_evaluate_driver.attach(executor=PrecisionEvaluator(eval_at=2), runtime=None)
    simple_chunk_rank_evaluate_driver.eval_request = eval_request
    simple_chunk_rank_evaluate_driver()

    assert len(eval_request.docs) == len(eval_request.groundtruths)
    assert len(eval_request.docs) == 10
    for doc in eval_request.docs:
        assert len(doc.evaluations) == 0  # evaluation done at chunk level
        assert len(doc.chunks) == 1
        chunk = doc.chunks[0]
        assert len(chunk.evaluations) == 1  # evaluation done at chunk level
        assert chunk.evaluations[0].op_name == 'Precision@N'
        assert chunk.evaluations[0].value == 1.0


@pytest.fixture
def eval_request_with_unmatching_struct():
    num_docs = 10
    num_matches = 1

    def add_matches(doc: jina_pb2.DocumentProto):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx

    req = jina_pb2.RequestProto.SearchRequestProto()
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


def test_evaluate_assert_doc_groundtruth_structure(simple_chunk_rank_evaluate_driver,
                                                   eval_request_with_unmatching_struct):
    simple_chunk_rank_evaluate_driver.attach(executor=PrecisionEvaluator(eval_at=2), runtime=None)
    simple_chunk_rank_evaluate_driver.eval_request = eval_request_with_unmatching_struct
    with pytest.raises(AssertionError):
        simple_chunk_rank_evaluate_driver()
