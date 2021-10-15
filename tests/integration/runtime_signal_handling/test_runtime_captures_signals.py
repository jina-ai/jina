import multiprocessing
import os
import time

import pytest
import signal

import zmq

from jina.clients.request import request_generator
from jina.parsers import set_gateway_parser, set_pea_parser
from jina import Executor, DocumentArray, Document, requests

from cli.api import gateway, executor_native
from jina.peapods.grpc import Grpclet
from jina.types.message import Message


class DummyExecutor(Executor):
    def __init__(self, dir=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dir = dir
        self.request_count = 0

    @requests
    def slow_count(self, **kwargs):
        time.sleep(0.5)
        self.request_count += 1

    def close(self):
        super().close()
        with open(f'{self.dir}/test.txt', 'w') as fp:
            fp.write(f'proper close;{self.request_count}')


def _create_test_data_message():
    req = list(
        request_generator(
            '/', DocumentArray([Document(text='input document') for _ in range(10)])
        )
    )[0]
    msg = Message(None, req, 'test', '123')
    return msg


# TODO: This test should also work with ZEDRuntime, but it needs some improvement to pass it
@pytest.mark.parametrize('signal', [signal.SIGTERM, signal.SIGINT])
@pytest.mark.parametrize('grpc_data_requests', [True])
def test_executor_runtimes(signal, tmpdir, grpc_data_requests):
    import time

    args = set_pea_parser().parse_args([])

    def run(args):

        args.uses = {
            'jtype': 'DummyExecutor',
            'with': {'dir': str(tmpdir)},
            'metas': {'workspace': str(tmpdir)},
        }
        args.grpc_data_requests = grpc_data_requests
        executor_native(args)

    process = multiprocessing.Process(target=run, args=(args,))
    process.start()
    time.sleep(0.5)

    if grpc_data_requests:
        Grpclet._create_grpc_stub(f'{args.host}:{args.port_in}', is_async=False).Call(
            _create_test_data_message()
        )
    else:
        socket = zmq.Context().socket(zmq.PUSH)
        socket.connect(f'tcp://localhost:{args.port_in}')
        socket.send_multipart(_create_test_data_message().dump())
    time.sleep(0.1)

    os.kill(process.pid, signal)
    process.join()
    with open(f'{tmpdir}/test.txt', 'r') as fp:
        output = fp.read()
    split = output.split(';')
    assert split[0] == 'proper close'
    assert split[1] == '1'


@pytest.mark.parametrize('signal', [signal.SIGTERM, signal.SIGINT])
@pytest.mark.parametrize('protocol', ['grpc', 'http', 'websocket'])
def test_gateway(signal, protocol):
    import time

    def run():
        args = set_gateway_parser().parse_args(['--protocol', protocol])
        gateway(args)

    process = multiprocessing.Process(target=run)
    process.start()
    time.sleep(0.5)
    os.kill(process.pid, signal)
    process.join()
