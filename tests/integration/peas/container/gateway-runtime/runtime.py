import sys

from jina.peapods.runtimes.gateway.grpc import GRPCGatewayRuntime
from jina.peapods.runtimes.gateway.http import HTTPGatewayRuntime
from jina.peapods.runtimes.gateway.websocket import WebSocketGatewayRuntime
from jina.enums import GatewayProtocolType

from jina.parsers import set_gateway_parser


def run(*args, **kwargs):
    runtime_cls = None
    print(f' args {args}')
    runtime_args = set_gateway_parser().parse_args(args)
    print(f' protocol {runtime_args.protocol}')
    if runtime_args.protocol == GatewayProtocolType.GRPC:
        runtime_cls = GRPCGatewayRuntime
    elif runtime_args.protocol == GatewayProtocolType.HTTP:
        runtime_cls = HTTPGatewayRuntime
    elif runtime_args.protocol == GatewayProtocolType.WEBSOCKET:
        runtime_cls = WebSocketGatewayRuntime

    print(f' runtime_cls {runtime_cls}')
    with runtime_cls(runtime_args) as runtime:
        print(f' Lets run forever')
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
