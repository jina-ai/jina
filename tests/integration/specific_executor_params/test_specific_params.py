import copy

from docarray import DocumentArray

from jina import Executor, Flow, requests


def test_specific_params():
    class MyExec(Executor):
        @requests
        def process(self, docs, parameters, **kwargs):
            return {'received_parameters': parameters}

    flow = Flow().add(uses=MyExec, name='exec1').add(uses=MyExec, name='exec2')

    with flow:
        response = flow.index(
            DocumentArray.empty(size=5),
            parameters={'key_1': True, 'exec2__key_2': False},
            return_responses=True,
        )

    assert response[0].parameters['__results__']['exec1/rep-0'][
        'received_parameters'
    ] == {'key_1': True}

    exec2_recevied_param = response[0].parameters['__results__']['exec2/rep-0'][
        'received_parameters'
    ]
    exec2_recevied_param.pop('__results__')

    assert exec2_recevied_param == {
        'key_1': True,
        'key_2': False,
    }
