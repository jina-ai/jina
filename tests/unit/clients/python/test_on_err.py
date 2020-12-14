import numpy as np

from jina.flow import Flow


def validate(x):
    raise NotImplementedError


def test_on_error(mocker):
    response_mock = mocker.Mock(wrap=validate)
    f = Flow().add()
    with f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=response_mock, continue_on_error=True)

    response_mock.assert_called()


def test_on_bad_iterator():
    # this should not stuck the server as request_generator's error is handled on the client side
    f = Flow().add()
    with f:
        f.index([1, 2, 3])
