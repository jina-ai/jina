from jina import Flow, Document, Executor, requests, DocumentArray


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

    f = Flow().add(uses=MyExecutor)

    with f:
        results = f.post(
            on='/search',
            inputs=[(Document(), Document()) for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_results=True,
        )
        assert results[0].status.code == 0
        assert results[0].data.docs[0].tags['hello'] == 'world'

    with f:
        results = f.post(
            on='/random',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            return_results=True,
        )
        assert results[0].status.code == 0


def test_func_failure():
    class MyExecutor(Executor):
        @requests(on='/search')
        def foo(self, **kwargs):
            raise Exception()

    f = Flow().add(uses=MyExecutor)

    with f:
        results = f.post(
            on='/search',
            inputs=[(Document(), Document()) for _ in range(3)],
            return_results=True,
        )
        assert results[0].status.code == 3


def test_func_default_routing():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
        )


def test_func_return_():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            return DocumentArray([Document(), Document()])

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post(
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
        Flow()
        .add(uses=M1)
        .add(uses=M2, needs='gateway')
        .add(uses=Joiner, needs=['pod0', 'pod1'])
    )

    mock = mocker.Mock()

    def validate(req):
        texts = {d.text for d in req.docs}
        assert len(texts) == 6
        expect = {
            'hello 0!!!',
            'hello 1!!!',
            'hello 2!!!',
            'world 0!!!',
            'world 1!!!',
            'world 2!!!',
        }
        assert texts == expect
        mock()

    with f:
        f.post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(3)],
            parameters={'hello': 'world', 'topk': 10},
            on_done=validate,
        )

    mock.assert_called_once()


def test_dealer_routing(mocker):
    f = Flow().add(parallel=3)
    mock = mocker.Mock()
    with f:
        f.post(
            on='/some_endpoint',
            inputs=[Document() for _ in range(100)],
            request_size=2,
            on_done=mock,
        )

    mock.assert_called()


def test_target_peapod(mocker):
    class Foo(Executor):
        @requests(on='/hello')
        def foo(self, **kwargs):
            pass

    class Bar(Executor):
        @requests(on='/bye')
        def bar(self, **kwargs):
            pass

    f = Flow().add(name='p0', uses=Foo).add(name='p1', uses=Bar)

    with f:
        success_mock = mocker.Mock()
        fail_mock = mocker.Mock()
        f.post(
            '/hello',
            target_peapod='p0',
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
