import multiprocessing
import time

from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.gateway.grpc import GRPCRuntime


def test_grpc_gateway_runtime_init_close():
    def create_runtime():
        with GRPCRuntime(
            set_gateway_parser().parse_args(['--grpc-data-requests'])
        ) as runtime:
            runtime.run_forever()

    p = multiprocessing.Process(target=create_runtime)
    p.start()
    time.sleep(1.0)
    p.terminate()
    p.join()

    assert p.exitcode == 0
