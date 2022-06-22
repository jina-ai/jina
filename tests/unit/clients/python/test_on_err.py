from typing import Optional

import aiohttp
import numpy as np
import pytest
from docarray.document.generators import from_ndarray

from docarray import DocumentArray
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


@pytest.mark.parametrize(
    'protocol,exception',
    [
        ('websocket', aiohttp.ClientError),
        ('grpc', ConnectionError),
        ('http', aiohttp.ClientError),
    ],
)
def test_client_on_error_call(protocol, exception):

    with pytest.raises(exception):
        Client(host='0.0.0.0', protocol=protocol, port=12345).post(
            '/blah',
            inputs=DocumentArray.empty(10),
        )


@pytest.mark.parametrize(
    'protocol,exception',
    [
        ('websocket', aiohttp.client_exceptions.ClientConnectorError),
        ('grpc', ConnectionError),
        ('http', aiohttp.client_exceptions.ClientConnectorError),
    ],
)
def test_client_on_error_raise_exception(protocol, exception):
    class OnError:
        def __init__(self):
            self.is_called = False

        def __call__(self, response, exception_param: Optional[Exception] = None):
            self.is_called = True
            assert type(exception_param) == exception

    on_error = OnError()

    Client(host='0.0.0.0', protocol=protocol, port=12345).post(
        '/blah',
        inputs=DocumentArray.empty(10),
        on_error=on_error,
    )

    assert on_error.is_called


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_on_error_deprecation(protocol):
    class OnError:
        def __init__(self):
            self.is_called = False

        def __call__(self, response):  # this is deprecated
            self.is_called = True

    on_error = OnError()

    Client(host='0.0.0.0', protocol=protocol, port=12345).post(
        '/blah',
        inputs=DocumentArray.empty(10),
        on_error=on_error,
    )

    assert on_error.is_called


@pytest.mark.parametrize('protocol', ['websocket', 'grpc', 'http'])
def test_client_on_always_after_exception(protocol):
    class OnAlways:
        def __init__(self):
            self.is_called = False

        def __call__(self, response):
            self.is_called = True

    on_always = OnAlways()

    Client(host='0.0.0.0', protocol=protocol, port=12345).post(
        '/blah',
        inputs=DocumentArray.empty(10),
        on_always=on_always,
    )

    assert on_always.is_called
