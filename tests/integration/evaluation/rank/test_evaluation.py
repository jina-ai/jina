import os
import numpy as np

from jina.flow import Flow
from jina.proto import jina_pb2, uid
from jina.drivers.helper import array2pb


def test_evaluation(tmpdir):
    os.environ['JINA_TEST_RANKING_EVALUATION'] = str(tmpdir)

    num_index_documents = 10
    num_evaluate_documents = 5

    def index_documents():
        docs = []
        for index in range(num_index_documents):
            doc = jina_pb2.Document()
            doc.tags['id'] = index
            doc.tags['dummy_score'] = -index
            doc.embedding.CopyFrom(array2pb(np.array([index])))
            doc.id = uid.new_doc_id(doc)
            docs.append(doc)
        return docs

    with Flow().load_config('flow-index.yml') as index_flow:
        index_flow.index(input_fn=index_documents)

    def validate_evaluation_response(resp):
        assert len(resp.docs) == num_evaluate_documents
        for doc in resp.docs:
            assert len(doc.evaluations) == 8  # 2 evaluation Pods with 4 evaluations each

    def evaluate_documents():
        docs = []
        for index in range(num_evaluate_documents):
            doc = jina_pb2.Document()
            doc.embedding.CopyFrom(array2pb(np.array([index])))
            groundtruth1 = doc.groundtruth.add()
            groundtruth1.tags['id'] = index
            groundtruth2 = doc.groundtruth.add()
            groundtruth2.tags['id'] = index + 1
            groundtruth3 = doc.groundtruth.add()
            groundtruth3.tags['id'] = 15965
            docs.append(doc)
        return docs

    with Flow().load_config('flow-evaluate.yml') as evaluate_flow:
        evaluate_flow.eval(
            input_fn=evaluate_documents(),
            output_fn=validate_evaluation_response,
            callback_on_body=True
        )

    del os.environ['JINA_TEST_RANKING_EVALUATION']
