from docarray import Document, Executor, Flow, requests


def test_target_executor(mocker):
    class UpExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            pass

    class DownExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            pass

    f = (
        Flow()
        .add(uses=UpExecutor, shards=3, name='up')
        .add(uses=DownExecutor, needs='gateway', name='down')
        .needs(needs=['up', 'down'])
    )

    with f:
        success_mock = mocker.Mock()
        fail_mock = mocker.Mock()
        f.post(
            on='/foo',
            target_executor='down',
            inputs=Document(),
            on_done=success_mock,
            on_error=fail_mock,
        )
        success_mock.assert_called()
        fail_mock.assert_not_called()
