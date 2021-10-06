import aiohttp
import pytest
from jina import Flow
from jina.types.request import Request
from jina.clients.request.helper import _new_data_request
from jina.clients.base.helper import HTTPClientlet, WebsocketClientlet


@pytest.mark.asyncio
async def test_http_clientlet():
    with Flow(port_expose=12345, protocol='http').add():
        async with HTTPClientlet(url='http://localhost:12345/post') as iolet:
            request = _new_data_request('/', None, {'a': 'b'})
            r = await iolet.send_message(request)
            response = Request(await r.json())
            response = response.as_typed_request(response.request_type).as_response()
            assert response.header.exec_endpoint == '/'
            assert response.parameters == {'a': 'b'}


@pytest.mark.asyncio
async def test_websocket_clientlet():
    with pytest.raises(aiohttp.ClientError):
        async with WebsocketClientlet(url='ws://localhost:12345') as iolet:
            pass
