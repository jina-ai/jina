import sys

from jina.serve.runtimes.asyncio import AsyncNewLoopRuntime
from jina.serve.runtimes.head.request_handling import HeaderRequestHandler
from jina.parsers import set_pod_parser


def run(*args, **kwargs):
    runtime_args = set_pod_parser().parse_args(args)
    runtime_args.host = runtime_args.host[0]
    runtime_args.port = runtime_args.port

    with AsyncNewLoopRuntime(
        args=runtime_args, req_handler_cls=HeaderRequestHandler
    ) as runtime:
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
