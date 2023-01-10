import aiohttp
import pytest

from jina import Executor, Flow, requests
from jina.clients.base.helper import HTTPClientlet, WebsocketClientlet
from jina.clients.request.helper import _new_data_request
from jina.excepts import BadServer
from jina.logging.logger import JinaLogger
from jina.types.request.data import DataRequest

logger = JinaLogger('clientlet')


class ClientTestExecutor(Executor):
    @requests
    def error(self, **kwargs):
        raise NotImplementedError


@pytest.fixture
def flow_with_exception_request():
    return Flow().add(uses=ClientTestExecutor).add()


@pytest.mark.asyncio
async def test_http_clientlet():
    from jina.helper import random_port

    port = random_port()
    with Flow(port=port, protocol='http').add():
        async with HTTPClientlet(
            url=f'http://localhost:{port}/post', logger=logger
        ) as iolet:
            request = _new_data_request('/', None, {'a': 'b'})
            assert request.header.target_executor == ''
            r = await iolet.send_message(request)
            response = DataRequest(await r.json())
    assert response.header.exec_endpoint == '/'
    assert response.parameters == {'a': 'b'}


@pytest.mark.asyncio
async def test_http_clientlet_target():
    from jina.helper import random_port

    port = random_port()
    with Flow(port=port, protocol='http').add():
        async with HTTPClientlet(
            url=f'http://localhost:{port}/post', logger=logger
        ) as iolet:
            request = _new_data_request('/', 'nothing', {'a': 'b'})
            assert request.header.target_executor == 'nothing'
            r = await iolet.send_message(request)
            response = DataRequest(await r.json())
    assert response.header.exec_endpoint == '/'
    assert response.parameters == {'a': 'b'}


@pytest.mark.asyncio
async def test_websocket_clientlet():
    with pytest.raises(aiohttp.ClientError):
        async with WebsocketClientlet(url='ws://localhost:12345', logger=logger):
            pass


def test_client_behaviour(flow_with_exception_request, mocker):
    on_done_mock = mocker.Mock()
    on_always_mock = mocker.Mock()
    on_error_mock = None

    with pytest.raises(BadServer):
        with flow_with_exception_request as f:
            f.post(
                '',
                on_done=on_done_mock,
                on_error=on_error_mock,
                on_always=on_always_mock,
            )
        on_always_mock.assert_called_once()
        on_done_mock.assert_not_called()
