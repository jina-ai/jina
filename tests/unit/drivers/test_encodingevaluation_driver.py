import numpy as np
from jina.drivers.evaluate import EncodeEvaluationDriver
from jina.drivers.helper import DocGroundtruthPair, array2pb
from jina.executors.evaluators.encode import BaseEncodingEvaluator
from jina.proto import jina_pb2


class MockDiffEvaluator(BaseEncodingEvaluator):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return 'MockDiffEvaluator'

    def evaluate(self, doc_embedding: 'np.array', groundtruth_embedding: 'np.array', *args, **kwargs) -> float:
        """"
        :param doc_embedding: the embedding of the document (resulting from an Encoder)
        :param groundtruth_embedding: the expected embedding of the document
        :return the evaluation metric value for the request document
        """
        return abs(sum(doc_embedding - groundtruth_embedding) / len(doc_embedding))


class SimpleEvaluateDriver(EncodeEvaluationDriver):
    @property
    def exec_fn(self):
        return self._exec_fn


def test_encoding_evaluate_driver():
    def create_document_ground_truth_pairs(num_docs):
        pairs = []
        for idx in range(num_docs):
            doc = jina_pb2.Document()
            gt = jina_pb2.Document()
            doc.embedding.CopyFrom(array2pb(np.array([1, 1])))
            gt.embedding.CopyFrom(array2pb(np.array([2, 2])))
            pairs.append(DocGroundtruthPair(doc=doc, groundtruth=gt))
        return pairs

    pairs = create_document_ground_truth_pairs(10)
    driver = SimpleEvaluateDriver()
    executor = MockDiffEvaluator()
    driver.attach(executor=executor, pea=None)
    driver._apply_all(pairs)
    for pair in pairs:
        doc = pair.doc
        assert len(doc.evaluations) == 1
        assert doc.evaluations[0].op_name == 'SimpleEvaluateDriver-MockDiffEvaluator'
        assert doc.evaluations[0].value == 1.0


class SimpleChunkEvaluateDriver(EncodeEvaluationDriver):

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


def test_encoding_evaluate_driver_embedding_in_chunks():
    # this test proves that we can evaluate matches at chunk level,
    # proving that the driver can traverse in a parallel way docs and groundtruth
    def create_eval_request(num_docs):
        req = jina_pb2.Request.IndexRequest()
        for idx in range(num_docs):
            doc = req.docs.add()
            gt = req.groundtruths.add()
            chunk_doc = doc.chunks.add()
            chunk_gt = gt.chunks.add()
            chunk_doc.granularity = 1
            chunk_gt.granularity = 1
            chunk_doc.embedding.CopyFrom(array2pb(np.array([1, 1])))
            chunk_gt.embedding.CopyFrom(array2pb(np.array([2, 2])))
        return req

    req = create_eval_request(10)
    driver = SimpleChunkEvaluateDriver()
    executor = MockDiffEvaluator()
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
        assert chunk.evaluations[0].op_name == 'SimpleChunkEvaluateDriver-MockDiffEvaluator'
        assert chunk.evaluations[0].value == 1.0

