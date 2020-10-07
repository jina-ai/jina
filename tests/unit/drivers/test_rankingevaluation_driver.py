from jina.drivers.evaluate import RankingEvaluationDriver
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


def create_documents_to_evaluate(num_docs):
    def add_matches(doc: jina_pb2.Document, num_matches):
        for idx in range(num_matches):
            match = doc.matches.add()
            match.tags['id'] = idx

    def add_groundtruth(doc: jina_pb2.Document, num_groundtruth):
        for idx in range(num_groundtruth):
            gt = doc.groundtruth.add()
            gt.tags['id'] = idx

    docs = []
    for idx in range(num_docs):
        doc = jina_pb2.Document()
        add_matches(doc, num_docs)
        add_groundtruth(doc, num_docs)
        docs.append(doc)
    return docs


def test_evaluate_driver():
    docs = create_documents_to_evaluate(10)
    driver = SimpleEvaluateDriver()
    executor = MockPrecisionEvaluator()
    driver.attach(executor=executor, pea=None)
    driver._apply_all(docs)
    for doc in docs:
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].id == 'SimpleEvaluateDriver-MockPrecision@2'
        assert doc.evaluations[0].value == 1.0
