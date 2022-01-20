from jina import Flow, Executor, requests


def test_empty_post_request(mocker):
    class MyExecutor(Executor):
        @requests
        def foo(self, **kwargs):
            print('hello world')

    f = Flow().add(uses=MyExecutor, shards=2, polling='ALL')
    with f:
        on_error_mock = mocker.Mock()
        on_done_mock = mocker.Mock()
        f.post('', on_error=on_error_mock, on_done=on_done_mock)

        on_error_mock.assert_not_called()
        on_done_mock.assert_called_once()
