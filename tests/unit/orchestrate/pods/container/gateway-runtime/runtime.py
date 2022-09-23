import sys

from jina.enums import GatewayProtocolType
from jina.parsers import set_gateway_parser
from jina.serve.runtimes.gateway import GatewayRuntime


def run(*args, **kwargs):
    runtime_cls = GatewayRuntime
    print(f' args {args}')
    runtime_args = set_gateway_parser().parse_args(args)
    print(f' protocol {runtime_args.protocol}')

    gateway_dict = {
        GatewayProtocolType.GRPC: 'GRPCGateway',
        GatewayProtocolType.WEBSOCKET: 'WebSocketGateway',
        GatewayProtocolType.HTTP: 'HTTPGateway',
    }
    if not runtime_args.uses:
        runtime_args.uses = gateway_dict[runtime_args.protocol]

    print(f' runtime_cls {runtime_cls}')
    with runtime_cls(runtime_args) as runtime:
        print(f' Lets run forever')
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
