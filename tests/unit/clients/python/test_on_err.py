import numpy as np
import pytest

from jina.excepts import BadClientCallback
from jina.flow import Flow


def test_on_error():
    def validate(x):
        raise NotImplementedError

    f = Flow().add()

    with pytest.raises(BadClientCallback), f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=False)

    with f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=True)
