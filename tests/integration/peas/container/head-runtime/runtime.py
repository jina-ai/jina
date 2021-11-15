import sys

from jina.peapods.runtimes.head import HeadRuntime
from jina.parsers import set_pea_parser


def run(*args, **kwargs):
    runtime_args = set_pea_parser().parse_args(args)
    with HeadRuntime(runtime_args) as runtime:
        runtime.run_forever()


if __name__ == '__main__':
    run(*sys.argv[1:])
