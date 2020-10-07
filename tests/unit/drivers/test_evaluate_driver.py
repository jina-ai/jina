from jina.drivers.evaluate import EvaluateDriver
from jina.executors.evaluators import BaseEvaluator
from jina.proto import jina_pb2


class MockPrecisionEvaluator(BaseEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(id_tag='id', *args, **kwargs)
        self.eval_at = 2

    @property
    def name(self):
        return f'MockPrecision@{self.eval_at}'

    def evaluate(self, matches, groundtruth, *args, **kwargs) -> float:
        ret = 0.0
        matches_ids = list(map(lambda x: x.tags[self.id_tag], matches[:self.eval_at]))
        groundtruth_ids = list(map(lambda x: x.tags[self.id_tag], groundtruth))
        for doc_id in matches_ids:
            if doc_id in groundtruth_ids:
                ret += 1.0

        divisor = min(self.eval_at, len(groundtruth))
        if divisor == 0.0:
            """TODO: Agree on a behavior"""
            return 0.0
        else:
            return ret / divisor


class SimpleEvaluateDriver(EvaluateDriver):

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
