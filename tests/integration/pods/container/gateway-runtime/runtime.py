import sys

from jina.parsers import set_gateway_parser
from jina.parsers.helper import _update_gateway_args
from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.gateway.request_handling import GatewayRequestHandler


def run(*args, **kwargs):
    runtime_args = set_gateway_parser().parse_args(args)
    _update_gateway_args(runtime_args)

    with AsyncNewLoopRuntime(runtime_args, req_handler_cls=GatewayRequestHandler) as runtime:
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
