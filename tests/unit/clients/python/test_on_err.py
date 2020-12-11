import numpy as np
import pytest

from jina.excepts import BadClientCallback
from jina.flow import Flow


def test_on_error(mocker):
    def validate(x):
        raise NotImplementedError

    f = Flow().add()

    with pytest.raises(BadClientCallback), f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=False)

    response_mock = mocker.Mock(wrap=validate)

    with f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=response_mock, continue_on_error=True)

    response_mock.assert_called()
