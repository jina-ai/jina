from typing import Dict

from jina import Flow, DocumentArray, Document, Executor, requests

ORIGINAL_PARAMS = {'param1': 50, 'param2': 60, 'exec_name': {'param1': 'changed'}}
OVERRIDEN_POD1_PARAMS = {
    'param1': 'changed',
    'param2': 60,
    'exec_name': {'param1': 'changed'},
}
OVERRIDEN_POD2_PARAMS = {
    'param1': 50,
    'param2': 'change_in_pod',
    'exec_name': {'param1': 'changed'},
}


class DummyOverrideParams(Executor):
    @requests()
    def bar(self, docs: 'DocumentArray', parameters: Dict, *args, **kwargs):
        for doc in docs:
            doc.tags = parameters


class DummyAssertNotOverrideBetweenPodsParams(Executor):
    @requests()
    def bar(self, parameters: Dict, *args, **kwargs):
        assert parameters == ORIGINAL_PARAMS
        parameters['param2'] = 'change_in_pod'


class DummyAssertIfParamsCanBeChangedInsidePods(Executor):
    @requests()
    def bar(self, parameters: Dict, *args, **kwargs):
        # this test is not sure it is intended, but good way of documenting
        assert parameters == ORIGINAL_PARAMS


def test_override_params(mocker):
    f = (
        Flow()
        .add(
            uses={'jtype': 'DummyOverrideParams', 'metas': {'name': 'exec_name'}},
        )
        .add(uses=DummyAssertNotOverrideBetweenPodsParams)
        .add(uses=DummyAssertIfParamsCanBeChangedInsidePods)
    )

    error_mock = mocker.Mock()

    with f:
        resp = f.index(
            inputs=DocumentArray([Document()]),
            parameters={'param1': 50, 'param2': 60, 'exec_name': {'param1': 'changed'}},
            on_error=error_mock,
            return_results=True,
        )
    error_mock.assert_not_called()

    assert len(resp) == 1
    assert len(resp[0].docs) == 1
    for doc in resp[0].docs:
        assert doc.tags == OVERRIDEN_POD1_PARAMS
        assert doc.tags['param1'] == 'changed'
        assert doc.tags['param2'] == 60
        assert doc.tags['exec_name']['param1'] == 'changed'
