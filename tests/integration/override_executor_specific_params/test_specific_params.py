from typing import Dict

from jina import Client, Document, DocumentArray, Executor, Flow, requests

ORIGINAL_PARAMS = {'param1': 50, 'param2': 60, 'exec_name': {'param1': 'changed'}}
OVERRIDEN_EXECUTOR1_PARAMS = {
    'param1': 'changed',
    'param2': 60,
    'exec_name': {'param1': 'changed'},
}


class DummyOverrideParams(Executor):
    @requests()
    def bar(self, docs: DocumentArray, parameters: Dict, *args, **kwargs):
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


def test_override_params(mocker, port_generator):
    exposed_port = port_generator()
    f = (
        Flow(port=exposed_port)
        .add(
            uses={'jtype': 'DummyOverrideParams', 'metas': {'name': 'exec_name'}},
        )
        .add(uses=DummyAssertNotOverrideBetweenPodsParams)
        .add(uses=DummyAssertIfParamsCanBeChangedInsidePods)
    )

    error_mock = mocker.Mock()

    with f:
        resp = Client(port=exposed_port).index(
            inputs=DocumentArray([Document()]),
            parameters={'param1': 50, 'param2': 60, 'exec_name': {'param1': 'changed'}},
            on_error=error_mock,
            return_responses=True,
        )
    error_mock.assert_not_called()

    assert len(resp) == 1
    assert len(resp[0].docs) == 1
    for doc in resp[0].docs:
        assert doc.tags == OVERRIDEN_EXECUTOR1_PARAMS
        assert doc.tags['param1'] == 'changed'
        assert doc.tags['param2'] == 60
        assert doc.tags['exec_name']['param1'] == 'changed'
