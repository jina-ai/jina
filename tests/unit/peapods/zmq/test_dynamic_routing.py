import threading
import time

import pytest
from google.protobuf import json_format

from jina.logging.logger import JinaLogger
from jina.helper import random_identity
from jina.parsers import set_pea_parser
from jina.peapods.zmq import Zmqlet, AsyncZmqlet, ZmqStreamlet
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.types.routing.table import RoutingTable


def get_args():
    """Calculates a fresh set of ports with every call implicitly."""
    return set_pea_parser().parse_args(
        [
            '--host-in',
            '0.0.0.0',
            '--host-out',
            '0.0.0.0',
            '--socket-in',
            'ROUTER_BIND',
            '--socket-out',
            'ROUTER_BIND',
            '--timeout-ctrl',
            '-1',
            '--dynamic-routing-out',
        ]
    )


def callback(msg):
    pass


def test_simple_dynamic_routing_zmqlet():
    args1 = get_args()
    args2 = get_args()

    logger = JinaLogger('zmq-test')
    with Zmqlet(args1, logger) as z1, Zmqlet(args2, logger) as z2:
        assert z1.msg_sent == 0
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 0
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        routing_pb = jina_pb2.RoutingTableProto()
        routing_table = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': [{'pod': 'pod2'}],
                },
                'pod2': {
                    'host': '0.0.0.0',
                    'port': args2.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
            },
        }
        json_format.ParseDict(routing_table, routing_pb)
        msg.envelope.routing_table.CopyFrom(routing_pb)
        z2.recv_message(callback)

        assert z2.msg_sent == 0
        assert z2.msg_recv == 0

        z1.send_message(msg)
        z2.recv_message(callback)
        assert z1.msg_sent == 1
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 1


@pytest.mark.slow
def test_double_dynamic_routing_zmqlet():
    args1 = get_args()
    args2 = get_args()
    args3 = get_args()

    logger = JinaLogger('zmq-test')
    with Zmqlet(args1, logger) as z1, Zmqlet(args2, logger) as z2, Zmqlet(
        args3, logger
    ) as z3:
        assert z1.msg_sent == 0
        assert z2.msg_sent == 0
        assert z3.msg_sent == 0
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        routing_table = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': [{'pod': 'pod2'}, {'pod': 'pod3'}],
                },
                'pod2': {
                    'host': '0.0.0.0',
                    'port': args2.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
                'pod3': {
                    'host': '0.0.0.0',
                    'port': args3.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
            },
        }
        msg.envelope.routing_table.CopyFrom(RoutingTable(routing_table).proto)

        number_messages = 100
        trips = 10
        for i in range(trips):
            for j in range(number_messages):
                z1.send_message(msg)
            time.sleep(1)
            for i in range(number_messages):
                z2.recv_message(callback)
                z3.recv_message(callback)

        total_number_messages = number_messages * trips

        assert z1.msg_sent == 2 * total_number_messages
        assert z2.msg_sent == 0
        assert z2.msg_recv == total_number_messages
        assert z3.msg_sent == 0
        assert z3.msg_recv == total_number_messages


async def send_msg(zmqlet, msg):
    await zmqlet.send_message(msg)


@pytest.mark.asyncio
async def test_double_dynamic_routing_async_zmqlet():
    args1 = get_args()
    args2 = get_args()
    args3 = get_args()

    logger = JinaLogger('zmq-test')
    with AsyncZmqlet(args1, logger) as z1, AsyncZmqlet(
        args2, logger
    ) as z2, AsyncZmqlet(args3, logger) as z3:
        assert z1.msg_sent == 0
        assert z2.msg_sent == 0
        assert z3.msg_sent == 0
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        routing_pb = jina_pb2.RoutingTableProto()
        routing_table = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': [{'pod': 'pod2'}, {'pod': 'pod3'}],
                },
                'pod2': {
                    'host': '0.0.0.0',
                    'port': args2.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
                'pod3': {
                    'host': '0.0.0.0',
                    'port': args3.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
            },
        }
        json_format.ParseDict(routing_table, routing_pb)
        msg.envelope.routing_table.CopyFrom(routing_pb)

        await send_msg(z1, msg)

        await z2.recv_message(callback)
        await z3.recv_message(callback)

        assert z1.msg_sent == 2
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 1
        assert z3.msg_sent == 0
        assert z3.msg_recv == 1


@pytest.mark.slow
def test_double_dynamic_routing_zmqstreamlet():
    args1 = get_args()
    args2 = get_args()
    args3 = get_args()

    logger = JinaLogger('zmq-test')
    with ZmqStreamlet(args=args1, logger=logger) as z1, ZmqStreamlet(
        args=args2, logger=logger
    ) as z2, ZmqStreamlet(args=args3, logger=logger) as z3:
        assert z1.msg_sent == 0
        assert z2.msg_sent == 0
        assert z3.msg_sent == 0
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        routing_pb = jina_pb2.RoutingTableProto()
        routing_table = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': [{'pod': 'pod2'}, {'pod': 'pod3'}],
                },
                'pod2': {
                    'host': '0.0.0.0',
                    'port': args2.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
                'pod3': {
                    'host': '0.0.0.0',
                    'port': args3.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
            },
        }
        json_format.ParseDict(routing_table, routing_pb)
        msg.envelope.routing_table.CopyFrom(routing_pb)
        for pea in [z1, z2, z3]:
            thread = threading.Thread(target=pea.start, args=(callback,))
            thread.daemon = True
            thread.start()

        number_messages = 1000
        for i in range(number_messages):
            z1.send_message(msg)

        time.sleep(5)

        assert z1.msg_sent == 2 * number_messages
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == number_messages
        assert z3.msg_sent == 0
        assert z3.msg_recv == number_messages


def test_remote_local_dynamic_routing_zmqlet():
    args1 = get_args()

    args2 = get_args()
    args2.zmq_identity = 'test-identity'
    args2.hosts_in_connect = [f'{args1.host}:{args1.port_out}']

    logger = JinaLogger('zmq-test')
    with Zmqlet(args1, logger) as z1, Zmqlet(args2, logger) as z2:
        assert z1.msg_sent == 0
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 0
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        routing_pb = jina_pb2.RoutingTableProto()
        routing_table = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': [{'pod': 'pod2', 'send_as_bind': True}],
                },
                'pod2': {
                    'host': '0.0.0.0',
                    'port': args2.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                    'target_identity': args2.zmq_identity,
                },
            },
        }
        json_format.ParseDict(routing_table, routing_pb)
        msg.envelope.routing_table.CopyFrom(routing_pb)
        z2.recv_message(callback)

        assert z2.msg_sent == 0
        assert z2.msg_recv == 0

        z1.send_message(msg)
        z2.recv_message(callback)

        assert z1.msg_sent == 1
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 1
