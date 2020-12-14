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
