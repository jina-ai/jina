import pytest
import numpy as np

from jina.flow import Flow
from jina.excepts import BadClientCallback


def validate(x):
    raise NotImplementedError


def test_client_on_error():
    # This will fail and get stuck
    # Not sure why this test case was removed
    f = Flow().add()
    with pytest.raises(BadClientCallback):
        with f:
            f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=False)

    # Recreating the flow instance will make it work.
    # But reusing the flow upon an error is a good test case
    # f = Flow().add()
    with f:
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=True)
