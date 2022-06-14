from docarray import DocumentArray
from jina import Executor, Flow, requests


def test_parameters_per_executor():
    class ExecReadParameters(Executor):
        @requests
        def foo(self, docs, parameters, **kwargs):
            for doc in docs:
                name_in_tags = doc.tags.get('name_in_param', '')
                name_in_param = parameters.get('name', '')
                if name_in_param != '':
                    assert name_in_param in self.runtime_args.name
                doc.tags['name_in_param'] = name_in_tags + name_in_param

    class ExecReturnResultsInParams(Executor):
        @requests
        def foo(self, **kwargs):
            return {'a': 'b'}

    f = (
        Flow()
        .add(uses=ExecReadParameters, name='read0')
        .add(uses=ExecReturnResultsInParams, name='return1')
        .add(uses=ExecReadParameters, name='read21')
        .add(uses=ExecReadParameters, name='read22', needs=['return1'])
        .add(uses=ExecReturnResultsInParams, name='return23', needs=['return1'])
        .add(name='join', needs=['read21', 'read22', 'return23'])
    )

    parameters = {
        '__jina_parameters_per_executor__': True,
        'read0': {'name': 'read0'},
        'read21': {'name': 'read21'},
    }
    with f:
        response = f.index(
            inputs=DocumentArray.empty(2), parameters=parameters, return_responses=True
        )[0]

    docs = response.docs
    par = response.parameters
    print(f' par {par}')
    for doc in docs:
        assert doc.tags['name_in_param'] == 'read0'
