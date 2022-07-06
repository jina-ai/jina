import copy

from docarray import DocumentArray

from jina import Executor, Flow, requests


def test_specific_params():
    class MyExec(Executor):
        def __init__(self, params_awaited, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.params_awaited = params_awaited

        @requests
        def process(self, docs, parameters, **kwargs):
            docs[0].tags['assert'] = parameters == self.params_awaited

    flow = (
        Flow()
        .add(uses=MyExec, name='exec1', uses_with={'params_awaited': {'key_1': True}})
        .add(
            uses=MyExec,
            name='exec2',
            uses_with={'params_awaited': {'key_1': True, 'key_2': False}},
        )
    )

    with flow:
        docs = flow.index(
            DocumentArray.empty(size=1),
            parameters={'key_1': True, 'exec2__key_2': False},
        )

        assert docs[0].tags['assert']
