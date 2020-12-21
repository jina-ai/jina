import os

import numpy as np

from jina import Document
from jina.flow import Flow


def test_evaluation(tmpdir, mocker):
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
        with Document() as doc0:
            doc0.tags['id'] = '0'
            doc0.tags['dummy_score'] = 0
            doc0.embedding = np.array([0])

        with Document() as doc1:
            doc1.tags['id'] = '1'
            doc1.tags['dummy_score'] = -1
            doc1.embedding = np.array([1])

        with Document() as doc2:
            doc2.tags['id'] = '2'
            doc2.tags['dummy_score'] = -2
            doc2.embedding = np.array([2])

        return [doc0, doc1, doc2]

    with Flow.load_config('flow-index.yml') as index_flow:
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
        with Document() as doc0:
            doc0.embedding = np.array([0])

        with Document() as groundtruth0:
            m1 = Document(id='1' * 16)
            m1.score.value = -1
            match0 = groundtruth0.matches.append(m1)
            match0.tags['id'] = '0'
            m2 = Document(id='2' * 16)
            m2.score.value = -1
            match1 = groundtruth0.matches.append(m2)
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

        with Document() as doc1:
            doc1.embedding = np.array([2])

        with Document() as groundtruth1:
            m1 = Document(id='1' * 16)
            m1.score.value = -1
            match0 = groundtruth1.matches.append(m1)
            match0.tags['id'] = '1'
            m2 = Document(id='2' * 16)
            m2.score.value = -1
            match1 = groundtruth1.matches.append(m2)
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
    response_mock = mocker.Mock(wrap=validate_evaluation_response)
    with Flow.load_config('flow-evaluate.yml') as evaluate_flow:
        evaluate_flow.search(
            input_fn=doc_groundtruth_evaluation_pairs,
            on_done=response_mock,
            callback_on='body',
            top_k=2
        )

    del os.environ['JINA_TEST_RANKING_EVALUATION']
    response_mock.assert_called()
