import os

import numpy as np

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.proto.ndarray.generic import GenericNdArray


def test_evaluation(tmpdir):
    os.environ['JINA_TEST_RANKING_EVALUATION'] = str(tmpdir)

    def index_documents():
        """Index Documents:
            doc: tag__id = 0
                 tag__dummy_score = 0
                 embedding = 0
            doc: tag__id = 1
                 tag__dummy_score = -1
                 embedding = 1
            doc: tag__id = 2
                 tag__dummy_score = -2
                 embedding = 2
        """
        doc0 = jina_pb2.Document()
        doc0.tags['id'] = '0'
        doc0.tags['dummy_score'] = 0
        GenericNdArray(doc0.embedding).value = np.array([0])
        doc1 = jina_pb2.Document()
        doc1.tags['id'] = '1'
        doc1.tags['dummy_score'] = -1
        GenericNdArray(doc1.embedding).value = np.array([1])
        doc2 = jina_pb2.Document()
        doc2.tags['id'] = '2'
        doc2.tags['dummy_score'] = -2
        GenericNdArray(doc2.embedding).value = np.array([2])
        return [doc0, doc1, doc2]

    with Flow().load_config('flow-index.yml') as index_flow:
        index_flow.index(input_fn=index_documents)

    def validate_evaluation_response(resp):
        assert len(resp.docs) == 2
        for doc in resp.docs:
            assert len(doc.evaluations) == 8  # 2 evaluation Pods with 4 evaluations each

        doc = resp.docs[0]
        assert len(doc.matches) == 2
        assert doc.evaluations[0].op_name == 'evaluate_match-Precision@1'
        assert doc.evaluations[0].value == 1.0
        assert doc.evaluations[1].op_name == 'evaluate_match-Precision@2'
        assert doc.evaluations[1].value == 0.5
        assert doc.evaluations[2].op_name == 'evaluate_match-Recall@1'
        assert doc.evaluations[2].value == 0.5
        assert doc.evaluations[3].op_name == 'evaluate_match-Recall@2'
        assert doc.evaluations[3].value == 0.5

        assert doc.evaluations[4].op_name == 'evaluate_rank-Precision@1'
        assert doc.evaluations[4].value == 1.0
        assert doc.evaluations[5].op_name == 'evaluate_rank-Precision@2'
        assert doc.evaluations[5].value == 0.5
        assert doc.evaluations[6].op_name == 'evaluate_rank-Recall@1'
        assert doc.evaluations[6].value == 0.5
        assert doc.evaluations[7].op_name == 'evaluate_rank-Recall@2'
        assert doc.evaluations[7].value == 0.5

        doc = resp.docs[1]
        assert doc.evaluations[0].op_name == 'evaluate_match-Precision@1'
        assert doc.evaluations[0].value == 1.0
        assert doc.evaluations[1].op_name == 'evaluate_match-Precision@2'
        assert doc.evaluations[1].value == 1.0
        assert doc.evaluations[2].op_name == 'evaluate_match-Recall@1'
        assert doc.evaluations[2].value == 0.5
        assert doc.evaluations[3].op_name == 'evaluate_match-Recall@2'
        assert doc.evaluations[3].value == 1.0

        assert doc.evaluations[4].op_name == 'evaluate_rank-Precision@1'
        assert doc.evaluations[4].value == 1.0
        assert doc.evaluations[5].op_name == 'evaluate_rank-Precision@2'
        assert doc.evaluations[5].value == 1.0
        assert doc.evaluations[6].op_name == 'evaluate_rank-Recall@1'
        assert doc.evaluations[6].value == 0.5
        assert doc.evaluations[7].op_name == 'evaluate_rank-Recall@2'
        assert doc.evaluations[7].value == 1.0

    def doc_groundtruth_evaluation_pairs():
        doc0 = jina_pb2.Document()
        GenericNdArray(doc0.embedding).value = np.array([0])  # it will match 0 and 1
        groundtruth0 = jina_pb2.Document()
        match0 = groundtruth0.matches.add()
        match0.tags['id'] = '0'
        match1 = groundtruth0.matches.add()
        match1.tags['id'] = '2'
        # top_k is set to 2 for VectorSearchDriver
        # expects as matches [0, 2] but given [0, 1]
        # Precision@1 = 100%
        # Precision@2 = 50%
        # Recall@1 = 100%
        # Recall@2 = 50%

        # expects as ranked [0, 2] but given [0, 1]
        # Precision@1 = 100%
        # Precision@2 = 50%
        # Recall@1 = 100%
        # Recall@2 = 50%

        doc1 = jina_pb2.Document()
        GenericNdArray(doc1.embedding).value = np.array([2])  # it will match 2 and 1
        groundtruth1 = jina_pb2.Document()
        match0 = groundtruth1.matches.add()
        match0.tags['id'] = '1'
        match1 = groundtruth1.matches.add()
        match1.tags['id'] = '2'
        # expects as matches [1, 2] but given [2, 1]
        # Precision@1 = 100%
        # Precision@2 = 100%
        # Recall@1 = 100%
        # Recall@2 = 100%

        # expects as ranked [1, 2] but given [2, 1]
        # Precision@1 = 100%
        # Precision@2 = 100%
        # Recall@1 = 100%
        # Recall@2 = 100%

        return [(doc0, groundtruth0), (doc1, groundtruth1)]

    with Flow().load_config('flow-evaluate.yml') as evaluate_flow:
        evaluate_flow.search(
            input_fn=doc_groundtruth_evaluation_pairs(),
            output_fn=validate_evaluation_response,
            callback_on_body=True,
            top_k=2
        )

    del os.environ['JINA_TEST_RANKING_EVALUATION']
