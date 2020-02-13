import sys


def _get_run_args(print_args: bool = True):
    from ..logging import default_logger
    from .parser import get_main_parser
    from termcolor import colored

    parser = get_main_parser()
    if len(sys.argv) > 1:
        args = parser.parse_args()
        if print_args:
            param_str = '\n'.join(['%30s = %s' % (colored(k, 'yellow'), v) for k, v in sorted(vars(args).items())])
            default_logger.info('usage: %s\n%s\n%s\n' % (' '.join(sys.argv), '_' * 50, param_str))
        return args
    else:
        parser.print_help()
        exit()


def main():
    """The main entrypoint of the CLI """
    from . import api
    args = _get_run_args()
    getattr(api, args.cli)(args)
