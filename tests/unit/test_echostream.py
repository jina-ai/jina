import logging

from jina.flow import Flow
from jina.parser import set_pea_parser
from jina.peapods.pea import BasePea
from jina.peapods.zmq import Zmqlet
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.helper import get_random_identity
from tests import random_docs


def test_simple_zmqlet():
    args = set_pea_parser().parse_args([
        '--host-in', '0.0.0.0',
        '--host-out', '0.0.0.0',
        '--port-in', '12346',
        '--port-out', '12347',
        '--socket-in', 'PULL_CONNECT',
        '--socket-out', 'PUSH_CONNECT',
        '--timeout-ctrl', '-1'])

    args2 = set_pea_parser().parse_args([
        '--host-in', '0.0.0.0',
        '--host-out', '0.0.0.0',
        '--port-in', '12347',
        '--port-out', '12346',
        '--socket-in', 'PULL_BIND',
        '--socket-out', 'PUSH_BIND',
        '--uses', '_logforward',
        '--timeout-ctrl', '-1'
    ])

    logger = logging.getLogger('zmq-test')
    with BasePea(args2) as z1, Zmqlet(args, logger) as z:
        req = jina_pb2.RequestProto()
        req.request_id = get_random_identity()
        d = req.index.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        z.send_message(msg)


def test_flow_with_jump():
    f = (Flow().add(name='r1')
         .add(name='r2')
         .add(name='r3', needs='r1')
         .add(name='r4', needs='r2')
         .add(name='r5', needs='r3')
         .add(name='r6', needs='r4')
         .add(name='r8', needs='r6')
         .add(name='r9', needs='r5')
         .add(name='r10', needs=['r9', 'r8']))

    with f:
        f.index(random_docs(10))


def test_flow_with_parallel():
    f = (Flow().add(name='r1')
         .add(name='r2', parallel=3))

    with f:
        f.index(random_docs(100))
