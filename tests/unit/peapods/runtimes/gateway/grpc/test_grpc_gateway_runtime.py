import time
import multiprocessing

from jina.parsers import set_gateway_parser
from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime


def test_grpc_gateway_runtime_init_close():
    def create_runtime():
        with GRPCGatewayRuntime(
            set_gateway_parser().parse_args(['--grpc-data-requests', '--graph-description', '{"start-gateway": ["pod0"], "pod0": ["end-gateway"]}', '--pods-addresses', '["pod0": ["0.0.0.0:3246", "0.0.0.0:3247"]'])
        ) as runtime:
            runtime.run_forever()

    p = multiprocessing.Process(target=create_runtime)
    p.start()
    time.sleep(1.0)
    p.terminate()
    p.join()

    assert p.exitcode == 0
