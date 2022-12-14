import sys

from jina.serve.runtimes.head import HeadRuntime
from jina.parsers import set_pod_parser


def run(*args, **kwargs):
    runtime_args = set_pod_parser().parse_args(args)
    runtime_args.host = runtime_args.host[0]
    runtime_args.port = runtime_args.port[0]
    with HeadRuntime(runtime_args) as runtime:
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
