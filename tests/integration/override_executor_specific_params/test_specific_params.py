from typing import Dict

from jina import Flow, DocumentArray, Document, Executor, requests
from tests import validate_callback


class DummyOverrideParams(Executor):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    @requests()
    def bar(self, docs: 'DocumentArray', parameters: Dict, *args, **kwargs):
        for doc in docs:
            doc.tags = parameters


def test_override_params(mocker):
    def validate(response):
        assert len(response.docs) == 1
        for doc in response.docs:
            assert doc.tags['param1'] == 'changed'
            assert doc.tags['param2'] == 60

    f = Flow().add(
        uses={'jtype': 'DummyOverrideParams', 'metas': {'name': 'exec_name'}},
    )

    mock = mocker.Mock()
    error_mock = mocker.Mock()

    with f:
        f.index(
            inputs=DocumentArray([Document()]),
            parameters={'param1': 50, 'param2': 60, 'exec_name': {'param1': 'changed'}},
            on_done=mock,
            on_error=error_mock,
        )
    mock.assert_called_once()
    validate_callback(mock, validate)
    error_mock.assert_not_called()
