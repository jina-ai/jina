import asyncio
import time

import pytest
from google.protobuf import json_format
from grpc import RpcError

from jina import __default_host__
from jina.parsers import set_pea_parser
from jina.peapods.grpc import Grpclet
from jina.proto import jina_pb2
from jina.types.message.common import ControlMessage


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_send_receive(mocker):
    # AsyncMock does not seem to exist in python 3.7, this is a manual workaround
    receive_cb = mocker.Mock()

    async def mock_wrapper(msg):
        receive_cb()

    args = set_pea_parser().parse_args([])
    grpclet = Grpclet(args=args, message_callback=mock_wrapper)
    asyncio.get_event_loop().create_task(grpclet.start())

    receive_cb.assert_not_called()

    await grpclet.send_message(_create_msg(args))
    await asyncio.sleep(0.1)
    receive_cb.assert_called()

    await grpclet.close(None)


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_send_non_blocking(mocker):
    receive_cb = mocker.Mock()

    async def blocking_cb(msg):
        receive_cb()
        time.sleep(1.0)
        return msg

    args = set_pea_parser().parse_args([])
    grpclet = Grpclet(args=args, message_callback=blocking_cb)
    asyncio.get_event_loop().create_task(grpclet.start())

    receive_cb.assert_not_called()
    await grpclet.send_message(_create_msg(args))

    await asyncio.sleep(0.1)
    assert receive_cb.call_count == 1
    await grpclet.send_message(_create_msg(args))
    await asyncio.sleep(0.1)
    assert receive_cb.call_count == 2

    await grpclet.close(None)


@pytest.mark.slow
@pytest.mark.asyncio
@pytest.mark.timeout(5)
async def test_send_static_ctrl_msg(mocker):
    # AsyncMock does not seem to exist in python 3.7, this is a manual workaround
    receive_cb = mocker.Mock()

    async def mock_wrapper(msg):
        receive_cb()

    args = set_pea_parser().parse_args([])
    grpclet = Grpclet(args=args, message_callback=mock_wrapper)
    asyncio.get_event_loop().create_task(grpclet.start())

    receive_cb.assert_not_called()

    while True:
        try:

            def send_status():
                return Grpclet.send_ctrl_msg(
                    pod_address=f'{args.host}:{args.port_in}', command='STATUS'
                )

            await asyncio.get_event_loop().run_in_executor(None, send_status)
            break
        except RpcError:
            await asyncio.sleep(0.1)

    receive_cb.assert_called()
    await grpclet.close(None)


def _create_msg(args):
    msg = ControlMessage('STATUS')
    routing_pb = jina_pb2.RoutingTableProto()
    routing_table = {
        'active_pod': 'executor1',
        'pods': {
            'executor1': {
                'host': __default_host__,
                'port': args.port_in,
                'expected_parts': 1,
                'out_edges': [{'pod': 'executor2'}],
            },
            'executor2': {
                'host': __default_host__,
                'port': args.port_in,
                'expected_parts': 1,
                'out_edges': [],
            },
        },
    }
    json_format.ParseDict(routing_table, routing_pb)
    msg.envelope.routing_table.CopyFrom(routing_pb)
    return msg
