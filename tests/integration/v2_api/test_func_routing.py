from jina import Flow, Document, Executor, Client, requests, DocumentArray


def test_func_simple_routing():
    class MyExecutor(Executor):
        @requests(on='/search')
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3
            assert len(kwargs['groundtruths']) == 3
            assert kwargs['parameters']['hello'] == 'world'
            assert kwargs['parameters']['topk'] == 10
            kwargs['docs'][0].tags['hello'] = 'world'

    f = Flow(port_expose=1234).add(uses=MyExecutor)

    with f:
        results = Client(port=1234).post(
            on='/search',
            inputs=[(Document(), Document()) for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_results=True,
        )
        assert results[0].header.status.code == 0
        assert results[0].data.docs[0].tags['hello'] == 'world'

    with f:
        results = Client(port=1234).post(
            on='/random',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_results=True,
        )
        assert results[0].header.status.code == 0


def test_func_failure():
    class MyExecutor(Executor):
        @requests(on='/search')
        def foo(self, **kwargs):
            raise Exception()

    f = Flow(port_expose=1234).add(uses=MyExecutor)

    with f:
        results = Client(port=1234).post(
            on='/search',
            inputs=[(Document(), Document()) for _ in range(3)],
            return_results=True,
        )
        assert results[0].header.status.code == 3


def test_func_default_routing():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    f = Flow(port_expose=1234).add(uses=MyExecutor)

    with f:
        Client(port=1234).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
        )


def test_func_return_():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            return DocumentArray([Document(), Document()])

    f = Flow(port_expose=1234).add(uses=MyExecutor)

    with f:
        Client(port=1234).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            on_done=print,
        )


def test_func_joiner(mocker):
    class Joiner(Executor):
        @requests
        def foo(self, docs, **kwargs):
            for d in docs:
                d.text += '!!!'
            return docs

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
        Flow(port_expose=1234)
        .add(uses=M1)
        .add(uses=M2, needs='gateway')
        .add(uses=Joiner, needs=['executor0', 'executor1'])
    )

    mock = mocker.Mock()

    def validate(req):
        texts = {d.text for d in req.docs}
        assert len(texts) == 6
        mock()

    with f:
        Client(port=1234).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            on_done=validate,
        )

    mock.assert_called_once()


def test_dealer_routing(mocker):
    f = Flow(port_expose=1234).add(shards=3)
    mock = mocker.Mock()
    with f:
        Client(port=1234).post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(100)],
            request_size=2,
            on_done=mock,
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

    f = Flow(port_expose=1234).add(name='p0', uses=Foo).add(name='p1', uses=Bar)

    with f:
        success_mock = mocker.Mock()
        fail_mock = mocker.Mock()
        Client(port=1234).post(
            '/hello',
            target_executor='p0',
            inputs=Document(),
            on_done=success_mock,
            on_error=fail_mock,
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

    f = (
        Flow(port_expose=1234)
        .add(uses=FailExecutor, name='foo_with_what_ever_suffix')
        .add(uses=PassExecutor, name='foo')
    )

    with f:
        # both pods are called, create no error
        mock = mocker.Mock()
        Client(port=1234).post(
            on='/foo', target_executor='foo', inputs=Document(), on_done=mock
        )
        mock.assert_called()


def test_target_executor_with_one_pathways():
    f = Flow(port_expose=1234).add().add(name='my_target')
    with f:
        results = Client(port=1234).post(
            on='/search',
            inputs=Document(),
            return_results=True,
            target_executor='my_target',
        )
        assert len(results[0].data.docs) == 1


def test_target_executor_with_two_pathways():
    f = (
        Flow(port_expose=1234)
        .add()
        .add(needs=['gateway', 'executor0'], name='my_target')
    )
    with f:
        results = Client(port=1234).post(
            on='/search',
            inputs=Document(),
            return_results=True,
            target_executor='my_target',
        )
        assert len(results[0].data.docs) == 1


def test_target_executor_with_two_pathways_one_skip():
    f = (
        Flow(port_expose=1234)
        .add()
        .add(needs=['gateway', 'executor0'])
        .add(name='my_target')
    )
    with f:
        results = Client(port=1234).post(
            on='/search',
            inputs=Document(),
            return_results=True,
            target_executor='my_target',
        )
        assert len(results[0].data.docs) == 1


def test_target_executor_with_shards():
    f = Flow(port_expose=1234).add(shards=2).add(name='my_target')
    with f:
        results = Client(port=1234).post(
            on='/search',
            inputs=Document(),
            return_results=True,
            target_executor='my_target',
        )
        assert len(results[0].data.docs) == 1
