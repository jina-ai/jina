import multiprocessing
import os
import signal
import time

import pytest
from jina import Document, DocumentArray, Executor, requests
from jina.clients.request import request_generator
from jina.parsers import set_gateway_parser
from jina.serve.networking import GrpcConnectionPool
from jina_cli.api import executor_native, gateway

from tests.helper import _generate_args


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
    return req


@pytest.mark.parametrize('signal', [signal.SIGTERM, signal.SIGINT])
def test_executor_runtimes(signal, tmpdir):
    import time

    args = _generate_args()

    def run(args):

        args.uses = {
            'jtype': 'DummyExecutor',
            'with': {'dir': str(tmpdir)},
            'metas': {'workspace': str(tmpdir)},
        }
        executor_native(args)

    process = multiprocessing.Process(target=run, args=(args,))
    process.start()
    time.sleep(0.5)

    GrpcConnectionPool.send_request_sync(
        _create_test_data_message(), target=f'{args.host}:{args.port}'
    )

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
        args = set_gateway_parser().parse_args(
            [
                '--protocol',
                protocol,
                '--graph-description',
                '{}',
                '--deployments-addresses',
                '{}',
            ]
        )
        gateway(args)

    process = multiprocessing.Process(target=run)
    process.start()
    time.sleep(0.5)
    os.kill(process.pid, signal)
    process.join()
