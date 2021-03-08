import os

import pytest

from jina.flow import Flow
from jina import Document

from tests import validate_callback


@pytest.fixture
def index_groundtruth():
    """Index Groundtruth:
    doc: id = 00
         tag__groundtruth = True
         text = aa
    doc: id = 01
         tag__groundtruth = True
         text = aa
    doc: id = 02
         tag__groundtruth = True
         text = aa
    ... we will not have groundtruth for id 5, 10, 50
    """
    docs = []
    for idx in range(0, 100):
        doc = Document()
        doc.id = f'{idx:0>16}'
        doc.tags['groundtruth'] = True
        doc.text = 'aa'
        if idx not in (5, 10, 50):
            docs.append(doc)
    return docs


@pytest.fixture
def evaluate_docs():
    """Evaluate Documents:
    doc: id = 00
         tag__groundtruth = False
         text = aaa
    doc: id = 01
         tag__groundtruth = False
         text = aaa
    doc: id = 02
         tag__groundtruth = False
         text = aaa
    ...
    """
    docs = []
    for idx in range(0, 100):
        doc = Document()
        doc.id = f'{idx:0>16}'
        doc.tags['groundtruth'] = False
        doc.text = 'aaa'
        docs.append(doc)
    return docs


@pytest.fixture
def random_workspace(tmpdir):
    os.environ['JINA_TEST_EVALUATION_FROM_FILE'] = str(tmpdir)
    yield
    del os.environ['JINA_TEST_EVALUATION_FROM_FILE']


@pytest.mark.parametrize(
    'index_yaml, search_yaml',
    [
        ('flow-index-gt.yml', 'flow-evaluate-from-file.yml'),
        ('flow-index-gt-parallel.yml', 'flow-evaluate-from-file-parallel.yml'),
        ('flow-index-gt-parallel.yml', 'flow-parallel-evaluate-from-file-parallel.yml'),
    ],
)
@pytest.mark.parametrize('restful', [False, True])
def test_evaluation_from_file(
    random_workspace,
    index_groundtruth,
    evaluate_docs,
    index_yaml,
    search_yaml,
    restful,
    mocker,
    monkeypatch,
):
    monkeypatch.setenv("RESTFUL", restful)

    with Flow.load_config(index_yaml) as index_gt_flow:
        index_gt_flow.index(inputs=index_groundtruth, request_size=10)

    def validate_evaluation_response(resp):
        assert len(resp.docs) == 97
        assert len(resp.groundtruths) == 97
        for doc in resp.docs:
            assert len(doc.evaluations) == 1
            assert doc.evaluations[0].value == 1.0
            assert not doc.tags['groundtruth']
        for gt in resp.groundtruths:
            assert gt.tags['groundtruth']

    mock = mocker.Mock()
    with Flow.load_config(search_yaml) as evaluate_flow:
        evaluate_flow.search(inputs=evaluate_docs, on_done=mock)

    mock.assert_called_once()
    validate_callback(mock, validate_evaluation_response)
