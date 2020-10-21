import pytest
import os

from jina.flow import Flow
from jina.proto import jina_pb2


@pytest.fixture(scope='function')
def index_groundtruth():
    """Index Groundtruth:
        doc: tag__id = 0
             tag__groundtruth = True
             text = aa
        doc: tag__id = 1
             tag__groundtruth = True
             text = aa
        doc: tag__id = 3
             tag__groundtruth = True
             text = aa
    """
    doc0 = jina_pb2.Document()
    doc0.tags['id'] = 0
    doc0.tags['groundtruth'] = True
    doc0.text = 'aa'
    doc1 = jina_pb2.Document()
    doc1.tags['id'] = 1
    doc1.tags['groundtruth'] = True
    doc1.text = 'aa'
    doc3 = jina_pb2.Document()
    doc3.tags['id'] = 3
    doc3.tags['groundtruth'] = True
    doc3.text = 'aa'
    return [doc0, doc1, doc3]


@pytest.fixture(scope='function')
def evaluate_docs():
    """Evaluate Documents:
        doc: tag__id = 0
             tag__groundtruth = False
             text = aa
        doc: tag__id = 1
             tag__groundtruth = False
             text = aa
        doc: tag__id = 2
             tag__groundtruth = False
             text = aa
    """
    doc0 = jina_pb2.Document()
    doc0.tags['id'] = 0
    doc0.tags['groundtruth'] = False
    doc0.text = 'aaa'
    doc1 = jina_pb2.Document()
    doc1.tags['id'] = 1
    doc1.tags['groundtruth'] = False
    doc1.text = 'aaa'
    # doc2 does not have a groundtruth indexed
    doc2 = jina_pb2.Document()
    doc2.tags['id'] = 2
    doc2.tags['groundtruth'] = False
    doc2.text = 'aaa'
    doc3 = jina_pb2.Document()
    doc3.tags['id'] = 3
    doc3.tags['groundtruth'] = False
    doc3.text = 'aaa'
    return [doc0, doc1, doc2, doc3]


@pytest.fixture(scope='function')
def random_workspace(tmpdir):
    os.environ['JINA_TEST_EVALUATION_FROM_FILE'] = str(tmpdir)
    yield
    del os.environ['JINA_TEST_EVALUATION_FROM_FILE']


def test_evaluation_from_file(random_workspace, index_groundtruth, evaluate_docs):
    with Flow().load_config('flow-index-gt.yml') as index_gt_flow:
        index_gt_flow.index(input_fn=index_groundtruth)

    def validate_evaluation_response(resp):
        assert len(resp.docs) == 3
        assert len(resp.groundtruths) == 3
        for doc in resp.docs:
            assert len(doc.evaluations) == 1
            assert doc.evaluations[0].value == 1.0
            assert doc.evaluations[0].op_name == 'evaluate_from_file-Length'
            assert not doc.tags['groundtruth']
        for gt in resp.groundtruths:
            assert gt.tags['groundtruth']

    with Flow().load_config('flow-evaluate-from-file.yml') as evaluate_flow:
        evaluate_flow.search(
            input_fn=evaluate_docs,
            output_fn=validate_evaluation_response,
            callback_on_body=True
        )
