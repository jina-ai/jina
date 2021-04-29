from jina import Flow, Document, Executor, requests, DocumentSet


def test_func_simple_routing():
    class MyExecutor(Executor):

        @requests(on='/search')
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'queryset', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post([Document()] * 3,
               on='/search',
               parameters={'hello': 'world',
                           'topk': 10},
               on_done=print)


def test_func_default_routing():
    class MyExecutor(Executor):

        @requests
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'queryset', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post([Document()] * 3,
               on='/search',
               parameters={'hello': 'world',
                           'topk': 10})


def test_func_return_():
    class MyExecutor(Executor):

        @requests
        def foo(self, **kwargs):
            return DocumentSet([Document(), Document()])

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post([Document()] * 3,
               on='/search',
               parameters={'hello': 'world',
                           'topk': 10},
               on_done=print)
