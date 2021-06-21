import asyncio
import logging
import pytest
import threading
import time

from google.protobuf import json_format

from jina.parsers import set_pea_parser
from jina.peapods.zmq import Zmqlet, AsyncZmqlet, ZmqStreamlet
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.helper import random_identity


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
            'DEALER_CONNECT',
            '--timeout-ctrl',
            '-1',
            '--dynamic-out-routing',
        ]
    )


def callback(msg):
    pass


def test_simple_dynamic_routing_zmqlet():
    args1 = get_args()
    args1.port_ctrl = 51337
    args2 = get_args()
    args2.port_ctrl = 51338

    logger = logging.getLogger('zmq-test')
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
        routing_pb = jina_pb2.RoutingGraphProto()
        routing_graph = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': ['pod2'],
                },
                'pod2': {
                    'host': '0.0.0.0',
                    'port': args2.port_in,
                    'expected_parts': 1,
                    'out_edges': [],
                },
            },
        }
        json_format.ParseDict(routing_graph, routing_pb)
        msg.envelope.routing_graph.CopyFrom(routing_pb)
        z2.recv_message(callback)

        assert z2.msg_sent == 0
        assert z2.msg_recv == 0

        z1.send_message(msg)
        z2.recv_message(callback)
        assert z1.msg_sent == 1
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 1


def test_double_dynamic_routing_zmqlet():
    args1 = get_args()
    args2 = get_args()
    args3 = get_args()

    logger = logging.getLogger('zmq-test')
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
        routing_pb = jina_pb2.RoutingGraphProto()
        routing_graph = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': ['pod2', 'pod3'],
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
        json_format.ParseDict(routing_graph, routing_pb)
        msg.envelope.routing_graph.CopyFrom(routing_pb)

        number_messages = 100
        trips = 10
        for i in range(trips):
            for i in range(number_messages):
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

    logger = logging.getLogger('zmq-test')
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
        routing_pb = jina_pb2.RoutingGraphProto()
        routing_graph = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': ['pod2', 'pod3'],
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
        json_format.ParseDict(routing_graph, routing_pb)
        msg.envelope.routing_graph.CopyFrom(routing_pb)

        await send_msg(z1, msg)

        await z2.recv_message(callback)
        await z3.recv_message(callback)

        assert z1.msg_sent == 2
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == 1
        assert z3.msg_sent == 0
        assert z3.msg_recv == 1


def test_double_dynamic_routing_zmqstreamlet():
    args1 = get_args()
    args2 = get_args()
    args3 = get_args()

    logger = logging.getLogger('zmq-test')
    with ZmqStreamlet(args1, logger) as z1, ZmqStreamlet(
        args2, logger
    ) as z2, ZmqStreamlet(args3, logger) as z3:
        assert z1.msg_sent == 0
        assert z2.msg_sent == 0
        assert z3.msg_sent == 0
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        routing_pb = jina_pb2.RoutingGraphProto()
        routing_graph = {
            'active_pod': 'pod1',
            'pods': {
                'pod1': {
                    'host': '0.0.0.0',
                    'port': args1.port_in,
                    'expected_parts': 0,
                    'out_edges': ['pod2', 'pod3'],
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
        json_format.ParseDict(routing_graph, routing_pb)
        msg.envelope.routing_graph.CopyFrom(routing_pb)
        for pea in [z1, z2, z3]:
            thread = threading.Thread(target=pea.start, args=(callback,))
            thread.daemon = True
            thread.start()

        number_messages = 1000
        for i in range(number_messages):
            z1.send_message(msg)

        time.sleep(0.5)

        assert z1.msg_sent == 2 * number_messages
        assert z1.msg_recv == 0
        assert z2.msg_sent == 0
        assert z2.msg_recv == number_messages
        assert z3.msg_sent == 0
        assert z3.msg_recv == number_messages
