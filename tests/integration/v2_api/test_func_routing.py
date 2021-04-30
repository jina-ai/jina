from jina import Flow, Document, Executor, requests, DocumentSet


def test_func_simple_routing(mocker):
    class MyExecutor(Executor):
        @requests(on='/search')
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'queryset', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    f = Flow().add(uses=MyExecutor)

    done_mock = mocker.Mock()
    fail_mock = mocker.Mock()

    with f:
        f.post(
            [Document() for _ in range(3)],
            on='/search',
            parameters={'hello': 'world', 'topk': 10},
            on_done=done_mock,
            on_error=fail_mock,
        )

    done_mock.assert_called_once()
    fail_mock.assert_not_called()

    done_mock = mocker.Mock()
    fail_mock = mocker.Mock()

    with f:
        f.post(
            [Document() for _ in range(3)],
            on='/random',
            parameters={'hello': 'world', 'topk': 10},
            on_done=done_mock,
            on_error=fail_mock,
        )

    fail_mock.assert_called_once()
    done_mock.assert_not_called()


def test_func_default_routing():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            for j in ('docs', 'groundtruths', 'queryset', 'parameters'):
                assert j in kwargs
            assert len(kwargs['docs']) == 3

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post(
            [Document() for _ in range(3)],
            on='/some_endpoint',
            parameters={'hello': 'world', 'topk': 10},
        )


def test_func_return_():
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            return DocumentSet([Document(), Document()])

    f = Flow().add(uses=MyExecutor)

    with f:
        f.post(
            [Document() for _ in range(3)],
            on='/some_endpoint',
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
            [Document() for _ in range(3)],
            on='/some_endpoint',
            parameters={'hello': 'world', 'topk': 10},
            on_done=validate,
        )

    mock.assert_called_once()


def test_dealer_routing():
    f = Flow().add(parallels=3)

    with f:
        f.post([Document() for _ in range(100)], request_size=2, on='/some_endpoint')
