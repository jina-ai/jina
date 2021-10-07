import pytest
from jina import Flow
from jina.types.request import Request
from jina.helper import random_identity
from jina.clients.base.http import HTTPClientlet


def req():
    return {
        'request_id': random_identity(),
        'data': [{'id': random_identity()}],
        'exec_endpoint': '/',
    }


@pytest.mark.asyncio
async def test_http_clientlet():
    with Flow(port_expose=12345, protocol='http').add():
        async with HTTPClientlet(url='http://localhost:12345/post') as iolet:
            request = req()
            r = await iolet.send_message(request)
            response = Request(await r.json())
            response = response.as_typed_request(response.request_type).as_response()
            assert request['data'][0]['id'] == response.docs[0].id
            assert request['exec_endpoint'] == response.header.exec_endpoint
