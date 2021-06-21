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
    f = Flow(return_results=True).add(
        uses={'jtype': 'DummyOverrideParams', 'metas': {'name': 'exec_name'}},
    )

    error_mock = mocker.Mock()

    with f:
        resp = f.index(
            inputs=DocumentArray([Document()]),
            parameters={'param1': 50, 'param2': 60, 'exec_name': {'param1': 'changed'}},
            on_error=error_mock,
        )
    error_mock.assert_not_called()

    assert len(resp) == 1
    assert len(resp[0].docs) == 1
    for doc in resp[0].docs:
        assert doc.tags['param1'] == 'changed'
        assert doc.tags['param2'] == 60
        assert doc.tags['exec_name']['param1'] == 'changed'
