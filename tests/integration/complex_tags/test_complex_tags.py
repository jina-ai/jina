import pytest

from docarray import Document, Executor, Flow, requests
from tests import validate_callback

INPUT_TAGS = {
    'hey': {'nested': True, 'list': ['elem3', 'elem2', {'inlist': 'here'}]},
    'hoy': [0, 1],
}

EXPECTED_TAGS = {
    'hey': {'nested': True, 'list': ['elem3', 'CHANGED', {'inlist': 'CHANGED'}]},
    'hoy': [0, 'CHANGED'],
}


@pytest.fixture
def docs():
    d = Document()
    d.tags = INPUT_TAGS
    return [d]


@pytest.fixture()
def executor_class():
    class ComplexTagExecutor(Executor):
        @requests
        def process(self, docs, **kwargs):
            doc = docs[0]
            assert doc.tags == INPUT_TAGS
            doc.tags['hey']['list'][1] = 'CHANGED'
            doc.tags['hey']['list'][2]['inlist'] = 'CHANGED'
            doc.tags['hoy'][1] = 'CHANGED'
            assert doc.tags == EXPECTED_TAGS

    return ComplexTagExecutor


def test_send_complex_document(docs, executor_class, mocker):
    def validate(resp):
        doc = resp.docs[0]
        assert doc.tags == EXPECTED_TAGS

    mock = mocker.Mock()
    f = Flow().add(uses=executor_class)
    with f:
        f.index(inputs=docs, on_done=mock)

    validate_callback(mock, validate)


def test_copy_tags(docs):
    for d in docs:
        _d = Document(tags=d.tags)
        assert _d.tags == d.tags
