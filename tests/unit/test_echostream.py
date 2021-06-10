import logging

from jina import Flow
from jina.parsers import set_pea_parser
from jina.peapods.peas import BasePea
from jina.peapods.zmq import Zmqlet
from jina.proto import jina_pb2
from jina.types.message import Message
from jina.helper import random_identity
from tests import random_docs


def test_simple_zmqlet():
    args = set_pea_parser().parse_args(
        [
            '--host-in',
            '0.0.0.0',
            '--host-out',
            '0.0.0.0',
            '--socket-in',
            'PULL_CONNECT',
            '--socket-out',
            'PUSH_CONNECT',
            '--timeout-ctrl',
            '-1',
        ]
    )

    args2 = set_pea_parser().parse_args(
        [
            '--host-in',
            '0.0.0.0',
            '--host-out',
            '0.0.0.0',
            '--port-in',
            str(args.port_out),
            '--port-out',
            str(args.port_in),
            '--socket-in',
            'PULL_BIND',
            '--socket-out',
            'PUSH_BIND',
            '--timeout-ctrl',
            '-1',
        ]
    )

    logger = logging.getLogger('zmq-test')
    with BasePea(args2), Zmqlet(args, logger) as z:
        req = jina_pb2.RequestProto()
        req.request_id = random_identity()
        d = req.data.docs.add()
        d.tags['id'] = 2
        msg = Message(None, req, 'tmp', '')
        z.send_message(msg)


def test_flow_with_jump():
    f = (
        Flow()
        .add(name='r1')
        .add(name='r2')
        .add(name='r3', needs='r1')
        .add(name='r4', needs='r2')
        .add(name='r5', needs='r3')
        .add(name='r6', needs='r4')
        .add(name='r8', needs='r6')
        .add(name='r9', needs='r5')
        .add(name='r10', needs=['r9', 'r8'])
    )

    with f:
        f.index(random_docs(10))


def test_flow_with_parallel():
    f = Flow().add(name='r1').add(name='r2', parallel=3)

    with f:
        f.index(random_docs(100))
