import sys

from jina.parsers import set_gateway_parser
from jina.parsers.helper import _set_gateway_uses
from jina.serve.runtimes.gateway import GatewayRuntime


def run(*args, **kwargs):
    runtime_cls = GatewayRuntime
    print(f' args {args}')
    runtime_args = set_gateway_parser().parse_args(args)
    print(f' protocol {runtime_args.protocol}')
    _set_gateway_uses(runtime_args)

    print(f' runtime_cls {runtime_cls}')
    with runtime_cls(runtime_args) as runtime:
        print(f' Lets run forever')
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
