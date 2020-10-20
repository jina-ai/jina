import pytest
import os

from jina.flow import Flow
from jina.proto import jina_pb2
from jina.executors.metas import get_default_metas


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
    doc0.tags['id'] = '0'
    doc0.tags['groundtruth'] = True
    doc0.text = 'aa'
    doc1 = jina_pb2.Document()
    doc1.tags['id'] = '1'
    doc1.tags['groundtruth'] = True
    doc1.text = 'aa'
    doc3 = jina_pb2.Document()
    doc3.tags['id'] = '3'
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
    doc0.tags['id'] = '0'
    doc0.tags['groundtruth'] = False
    doc0.text = 'aa'
    doc1 = jina_pb2.Document()
    doc1.tags['id'] = '1'
    doc1.tags['groundtruth'] = False
    doc1.text = 'aa'
    # doc2 does not have a groundtruth indexed
    doc2 = jina_pb2.Document()
    doc2.tags['id'] = '1'
    doc2.tags['groundtruth'] = False
    doc2.text = 'aa'
    doc3 = jina_pb2.Document()
    doc3.tags['id'] = '3'
    doc3.tags['groundtruth'] = False
    doc3.text = 'aa'
    return [doc0, doc1, doc2, doc3]


@pytest.fixture(scope='function')
def test_metas(tmpdir, random_workspace_name):
    os.environ[random_workspace_name] = str(tmpdir)
    metas = get_default_metas()
    metas['workspace'] = os.environ[random_workspace_name]
    yield metas
    del os.environ[random_workspace_name]


@pytest.mark.parametrize('random_workspace_name', ['JINA_TEST_EVALUATION_FROM_FILE'])
def test_evaluation_from_file(random_workspace, index_groundtruth, evaluate_docs):
    with Flow().load_config('flow-index-gt.yml') as index_gt_flow:
        index_gt_flow.index(input_fn=index_groundtruth)

    def validate_evaluation_response(resp):
        assert len(resp.docs) == 3
        for doc in resp.docs:
            assert len(doc.evaluations) == 1  # 2 evaluation Pods with 4 evaluations each

    with Flow().load_config('flow-evaluate-from-file.yml') as evaluate_flow:
        evaluate_flow.search(
            input_fn=evaluate_docs,
            output_fn=validate_evaluation_response,
            callback_on_body=True
        )
