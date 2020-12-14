import numpy as np

from jina.excepts import BadClientCallback
from jina.flow import Flow


def validate(x):
    raise NotImplementedError


def test_client_on_error():
    # In this particular test, when you write two tests in a row, you are testing the following case:
    #
    # You are testing exception in client's callback, not error in client's request generator
    # The exception breaks the async for req in stub.Call(req_iter) on the client
    # Server probably has something hold in the stream
    # Restart the client, keep server untouched.
    # Now, server stucks (because it considers the last connection wasn't end yet)
    def validate(x):
        raise NotImplementedError

    with Flow().add() as f:
        t = 0
        try:
            f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=False)
        except BadClientCallback:
            t = 1
        f.index_ndarray(np.random.random([5, 4]), output_fn=validate, continue_on_error=True)
        assert t == 1


def test_on_bad_iterator():
    # this should not stuck the server as request_generator's error is handled on the client side
    f = Flow().add()
    with f:
        f.index([1, 2, 3])
