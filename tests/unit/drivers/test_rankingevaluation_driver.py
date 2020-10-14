import pytest
from jina.drivers.evaluate import RankingEvaluationDriver, DocGroundtruthPair
from jina.executors.evaluators.rank import BaseRankingEvaluator
from jina.proto import jina_pb2


class MockPrecisionEvaluator(BaseRankingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(id_tag='id', *args, **kwargs)
        self.eval_at = 2

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
            """TODO: Agree on a behavior"""
            return 0.0
        else:
            return ret / divisor


class SimpleEvaluateDriver(RankingEvaluationDriver):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def exec_fn(self):
        return self._exec_fn


def test_evaluate_driver():
    def create_document_ground_truth_pairs(num_docs):
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

    pairs = create_document_ground_truth_pairs(10)
    driver = SimpleEvaluateDriver()
    executor = MockPrecisionEvaluator()
    driver.attach(executor=executor, pea=None)
    driver._apply_all(pairs)
    for wrapper in pairs:
        doc = wrapper.doc
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


def test_evaluate_driver_matches_in_chunks():
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    def create_eval_request(num_docs, num_matches):
        def add_matches(doc: jina_pb2.Document):
            for idx in range(num_matches):
                match = doc.matches.add()
                match.tags['id'] = idx

        req = jina_pb2.Request.EvaluateRequest()
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

    req = create_eval_request(10, 1)
    driver = SimpleChunkEvaluateDriver()
    executor = MockPrecisionEvaluator()
    driver.attach(executor=executor, pea=None)
    driver.eval_request = req
    driver()

    assert len(req.docs) == len(req.groundtruths)
    assert len(req.docs) == 10
    for doc in req.docs:
        assert len(doc.evaluations) == 0  # evaluation done at chunk level
        assert len(doc.chunks) == 1
        chunk = doc.chunks[0]
        assert len(chunk.evaluations) == 1  # evaluation done at chunk level
        assert chunk.evaluations[0].op_name == 'SimpleChunkEvaluateDriver-MockPrecision@2'
        assert chunk.evaluations[0].value == 1.0


def test_evaluate_assert_doc_groundtruth_structure():
    def create_eval_request_with_unmatching_structure(num_docs, num_matches):
        def add_matches(doc: jina_pb2.Document):
            for idx in range(num_matches):
                match = doc.matches.add()
                match.tags['id'] = idx

        req = jina_pb2.Request.EvaluateRequest()
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

    req = create_eval_request_with_unmatching_structure(10, 1)
    driver = SimpleChunkEvaluateDriver()
    executor = MockPrecisionEvaluator()
    driver.attach(executor=executor, pea=None)
    driver.eval_request = req
    with pytest.raises(AssertionError):
        driver()
