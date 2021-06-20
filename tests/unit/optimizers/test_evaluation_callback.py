import pytest

from jina.optimizers import EvaluationCallback
from jina.types.request import Request
from jina import Document

EVAL_NAME = 'evaluation'
NUM_REQUESTS = 3
NUM_DOCS_PER_REQUEST = 4


@pytest.fixture()
def operator(request):
    return request.param


@pytest.fixture()
def callback(operator):
    return EvaluationCallback(EVAL_NAME, operator)


@pytest.fixture()
def responses():
    def create_documents(multiplier):
        d1 = Document()
        d1.evaluations['evaluation'] = multiplier * 1.0
        d1.evaluations['evaluation'].op_name = 'evaluation'
        d2 = Document()
        d2.evaluations['evaluation'] = multiplier * 1.0
        d2.evaluations['evaluation'].op_name = 'evaluation'
        d3 = Document()
        d3.evaluations['evaluation'] = multiplier * 2.0
        d3.evaluations['evaluation'].op_name = 'evaluation'
        d4 = Document()
        d4.evaluations['evaluation'] = multiplier * 2.0
        d4.evaluations['evaluation'].op_name = 'evaluation'
        return [d1, d2, d3, d4]

    def create_request(multiplier):
        req = Request().as_typed_request('data')
        for doc in create_documents(multiplier):
            req.docs.append(doc)
        return req

    return [create_request(multiplier=i + 1) for i in range(NUM_REQUESTS)]


@pytest.mark.parametrize(
    'operator, expected',
    [
        ('mean', 3.0),
        ('max', 6.0),
        ('min', 1.0),
        ('sum', 36.0),
        ('prod', 82944.0),
        ('median', 2.5),
    ],
    indirect=['operator'],
)
def test_evaluation_callback(callback, responses, operator, expected):
    for resp in responses:
        callback(resp)

    assert callback.get_final_evaluation() == expected
