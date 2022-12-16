from docarray import DocumentArray, Executor, Flow, requests


def test_needs_docs_map():
    class TestMergeDictDocMatrixExecutor(Executor):
        @requests()
        def foo(self, docs_map, **kwargs):
            assert {'exec0', 'exec1'} == set(docs_map.keys())

    f = (
        Flow()
        .add(name='exec0')
        .add(name='exec1', replicas=2, shards=2, needs=['gateway'])
        .add(
            name='exec2',
            needs=['exec0', 'exec1'],
            uses=TestMergeDictDocMatrixExecutor,
            disable_reduce=True,
        )
    )

    with f:
        f.post(on='/', inputs=DocumentArray.empty(2))
