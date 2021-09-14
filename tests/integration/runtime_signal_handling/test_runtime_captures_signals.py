import multiprocessing
import os
import pytest
import signal

from jina.parsers import set_gateway_parser, set_pea_parser
from jina import Executor

from cli.api import gateway, executor_native


class DummyExecutor(Executor):
    def __init__(self, dir=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.dir = dir

    def close(self):
        super().close()
        with open(f'{self.dir}/test.txt', 'w') as fp:
            fp.write('proper close')


@pytest.mark.parametrize(
    'signal, graceful', [(signal.SIGTERM, False), (signal.SIGINT, True)]
)
def test_zed_runtime(signal, graceful, tmpdir):
    import time

    def run():
        args = set_pea_parser().parse_args([])
        args.uses = {
            'jtype': 'DummyExecutor',
            'with': {'dir': str(tmpdir)},
            'metas': {'workspace': str(tmpdir)},
        }
        executor_native(args)

    process = multiprocessing.Process(target=run)
    process.start()
    time.sleep(0.5)
    os.kill(process.pid, signal)
    process.join()
    if graceful:
        with open(f'{tmpdir}/test.txt', 'r') as fp:
            output = fp.read()
        assert output == 'proper close'


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
