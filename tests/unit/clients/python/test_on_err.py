import numpy as np
import pytest
from docarray import DocumentArray
from docarray.document.generators import from_ndarray

from jina import Client, Flow
from jina.excepts import BadClientCallback


def validate(x):
    raise NotImplementedError


@pytest.mark.skip(
    reason='something wrong with parametrize in the following, setting either False or True work, but combining them does not. see discussion in https://jinaai.slack.com/archives/C018F60RBL5/p1613984424012700?thread_ts=1613954151.005100&cid=C018F60RBL5'
)
@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_on_error(protocol):
    # In this particular test, when you write two tests in a row, you are testing the following case:
    #
    # You are testing exception in client's callback, not error in client's request generator
    # 1. The exception breaks the `async for req in stub.Call(req_iter)` on the client
    # 2. Server probably has something hold in the stream
    # 3. Restart the client, keep server untouched.
    # 4. Now, server stucks (because it considers the last connection wasn't end yet)
    def validate(x):
        raise NotImplementedError

    with Flow(protocol=protocol).add() as f:
        t = 0
        try:
            f.index(
                from_ndarray(np.random.random([5, 4])),
                on_done=validate,
                continue_on_error=False,
            )
        except BadClientCallback:
            # bad client callback will break the `async for req in stub.Call(req_iter)`
            t = 1
        # now query the gateway again, make sure gateway's channel is still usable
        f.index(
            from_ndarray(np.random.random([5, 4])),
            on_done=validate,
            continue_on_error=True,
        )
        assert t == 1


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_on_error_call(protocol):
    with pytest.raises(ConnectionError):
        Client(host='0.0.0.0', protocol=protocol, port=12345).post(
            '/blah',
            inputs=DocumentArray.empty(10),
        )


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_on_error_raise_exception(protocol):
    with pytest.raises(ConnectionError):
        Client(host='0.0.0.0', protocol=protocol, port=12345).post(
            '/blah',
            inputs=DocumentArray.empty(10),
        )
