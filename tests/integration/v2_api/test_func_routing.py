from jina import Client, Document, DocumentArray, Executor, Flow, requests
from jina.helper import random_port


def test_func_simple_routing():
    class MyExecutor(Executor):
        @requests(on='/search')
        def foo(self, **kwargs):
            for j in ('docs', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3
            assert kwargs['parameters']['hello'] == 'world'
            assert kwargs['parameters']['topk'] == 10
            kwargs['docs'][0].tags['hello'] = 'world'

    port = random_port()

    f = Flow(port=port).add(uses=MyExecutor)

    with f:
        results = Client(port=f.port).post(
            on='/search',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_responses=True,
        )
        assert results[0].header.status.code == 0
        assert results[0].data.docs[0].tags['hello'] == 'world'

    with f:
        results = Client(port=f.port).post(
            on='/random',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_responses=True,
        )
        assert results[0].header.status.code == 0


def test_func_failure():
    class MyExecutor(Executor):
        @requests(on='/search')
        def foo(self, **kwargs):
            raise Exception()

    port = random_port()

    f = Flow(port=port).add(uses=MyExecutor)

    with f:
        results = Client(port=f.port).post(
            on='/search',
            inputs=[(Document(), Document()) for _ in range(3)],
            return_responses=True,
            continue_on_error=True,
        )

    assert results[0].header.status.code == 1


def test_func_default_routing():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            for j in ('docs', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    port = random_port()
    f = Flow(port=port).add(uses=MyExecutor)

    with f:
        Client(port=f.port).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_responses=True,
        )


def test_func_return_():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            return DocumentArray([Document(), Document()])

    port = random_port()
    f = Flow(port=port).add(uses=MyExecutor)

    with f:
        Client(port=f.port).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            on_done=print,
            return_responses=True,
        )


def test_func_joiner():
    port = random_port()

    class Joiner(Executor):
        @requests
        def foo(self, docs_matrix, **kwargs):
            for d1, d2 in zip(docs_matrix[0], docs_matrix[1]):
                d1.text = d1.text + d2.text + '!!!'
            return docs_matrix[0]

    class M1(Executor):
        @requests
        def foo(self, docs, **kwargs):
            for idx, d in enumerate(docs):
                d.text = f'hello {idx}'

    class M2(Executor):
        @requests
        def foo(self, docs, **kwargs):
            for idx, d in enumerate(docs):
                d.text = f'world {idx}'

    f = (
        Flow(port=port)
        .add(name='executor0', uses=M1)
        .add(name='executor1', uses=M2, needs='gateway')
        .add(uses=Joiner, needs=['executor0', 'executor1'], disable_reduce=True)
    )

    with f:
        resp = Client(port=f.port).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_responses=True,
        )

    texts = {d.text for r in resp for d in r.docs}
    assert len(texts) == 3


def test_dealer_routing(mocker):
    port = random_port()
    f = Flow(port=port).add(shards=3)
    mock = mocker.Mock()
    with f:
        Client(port=f.port).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(100)],
            request_size=2,
            on_done=mock,
            return_responses=True,
        )

    mock.assert_called()


def test_target_executor(mocker):
    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, **kwargs):
            pass

    class Bar(Executor):
        @requests(on='/bye')
        def bar(self, **kwargs):
            pass

    port = random_port()

    f = Flow(port=port).add(name='p0', uses=Foo).add(name='p1', uses=Bar)

    with f:
        success_mock = mocker.Mock()
        fail_mock = mocker.Mock()
        Client(port=f.port).post(
            '/hello',
            target_executor='p0',
            inputs=Document(),
            on_done=success_mock,
            on_error=fail_mock,
            return_responses=True,
        )
        success_mock.assert_called()
        fail_mock.assert_not_called()

        success_mock = mocker.Mock()
        fail_mock = mocker.Mock()
        f.post('/hello', inputs=Document(), on_done=success_mock, on_error=fail_mock)
        success_mock.assert_called()
        fail_mock.assert_not_called()


def test_target_executor_with_overlaped_name(mocker):
    class FailExecutor(Executor):
        @requests
        def fail(self, **kwargs):
            raise RuntimeError

    class PassExecutor(Executor):
        @requests
        def success(self, **kwargs):
            pass

    port = random_port()
    f = (
        Flow(port=port)
        .add(uses=FailExecutor, name='foo_with_what_ever_suffix')
        .add(uses=PassExecutor, name='foo')
    )

    with f:
        mock = mocker.Mock()
        Client(port=f.port).post(
            on='/foo',
            target_executor='^foo$',
            inputs=Document(),
            on_done=mock,
            return_responses=True,
        )
        mock.assert_called()


def test_target_executor_with_one_pathways():
    port = random_port()
    f = Flow(port=port).add().add(name='my_target')
    with f:
        results = Client(port=f.port).post(
            on='/search',
            inputs=Document(),
            target_executor='my_target',
            return_responses=True,
        )
        assert len(results[0].data.docs) == 1


def test_target_executor_with_two_pathways():
    port = random_port()
    f = Flow(port=port).add().add(needs=['gateway', 'executor0'], name='my_target')
    with f:
        results = Client(port=f.port).post(
            on='/search',
            inputs=Document(),
            target_executor='my_target',
            return_responses=True,
        )
        assert len(results[0].data.docs) == 1


def test_target_executor_with_two_pathways_one_skip():
    port = random_port()
    f = Flow(port=port).add().add(needs=['gateway', 'executor0']).add(name='my_target')
    with f:
        results = Client(port=f.port).post(
            on='/search',
            inputs=Document(),
            target_executor='my_target',
            return_responses=True,
        )
        assert len(results[0].data.docs) == 1


def test_target_executor_with_shards():
    port = random_port()
    f = Flow(port=port).add(shards=2).add(name='my_target')
    with f:
        results = Client(port=f.port).post(
            on='/search',
            inputs=Document(),
            target_executor='my_target',
            return_responses=True,
        )
        assert len(results[0].data.docs) == 1
