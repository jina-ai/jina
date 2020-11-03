import logging
import uuid

from jina.flow import Flow
from jina.parser import set_pea_parser
from jina.peapods.pea import BasePea
from jina.peapods.zmq import Zmqlet
from jina.proto import jina_pb2
from jina.proto.message import ProtoMessage
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
        req = jina_pb2.Request()
        req.request_id = uuid.uuid1().hex
        d = req.index.docs.add()
        d.tags['id'] = 2
        msg = ProtoMessage(None, req, 'tmp', '')
        z.send_message(msg)


def test_flow_with_jump():
    f = (Flow().add(name='r1', uses='_pass')
         .add(name='r2', uses='_pass')
         .add(name='r3', uses='_pass', needs='r1')
         .add(name='r4', uses='_pass', needs='r2')
         .add(name='r5', uses='_pass', needs='r3')
         .add(name='r6', uses='_pass', needs='r4')
         .add(name='r8', uses='_pass', needs='r6')
         .add(name='r9', uses='_pass', needs='r5')
         .add(name='r10', uses='_merge', needs=['r9', 'r8']))

    with f:
        f.index(random_docs(10))


def test_flow_with_parallel():
    f = (Flow().add(name='r1', uses='_pass')
         .add(name='r2', uses='_pass', parallel=3))

    with f:
        f.index(random_docs(100))
