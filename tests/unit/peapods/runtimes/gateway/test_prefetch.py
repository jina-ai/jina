import asyncio
from asyncio import Future

import pytest

from jina.helper import ArgNamespace, random_identity
from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.gateway.prefetch import PrefetchCaller
from jina.proto import jina_pb2


def _generate_request():
    req = jina_pb2.RequestProto()
    req.request_id = random_identity()
    req.data.docs.add()
    return req


class ZmqletMock:
    def __init__(self):
        self.sent_future = Future()
        self.received_event = asyncio.Event()

    async def recv_message(self, **kwargs):
        msg = await self.sent_future
        self.sent_future = Future()
        self.received_event.set()
        return msg

    async def send_message(self, message):
        self.sent_future.set_result(_generate_request())
        await self.received_event.wait()
        self.sent_future.set_result(message.response)


@pytest.mark.asyncio
async def test_concurrent_requests():
    args = ArgNamespace.kwargs2namespace({}, set_gateway_parser())
    mock_zmqlet = ZmqletMock()
    servicer = PrefetchCaller(args, mock_zmqlet)

    request = _generate_request()

    response = servicer.send(iter([request]))

    async for r in response:
        assert r.proto == request

    await servicer.close()
