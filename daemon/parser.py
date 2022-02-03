import argparse
import os
import sys

from jina import __resources_path__, __default_host__
from jina.parsers.base import set_base_parser
from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS
from jina.parsers.orchestrate.base import mixin_base_ppr_parser
from daemon.models.enums import PartialDaemonModes


def mixin_daemon_parser(parser):
    """
    # noqa: DAR101
    # noqa: DAR102
    # noqa: DAR103
    """
    gp = add_arg_group(parser, title='Daemon')
    gp.add_argument(
        '--no-store',
        action='store_true',
        default=False,
        help='''
    Disable loading from local store (if any), while starting JinaD
    ''',
    )
    gp.add_argument(
        '--mode',
        type=str,
        choices=list(PartialDaemonModes),
        default=None,
        help='Mode for partial jinad. Can be flow/deployment/pod. If none provided main jinad is run.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )


def mixin_remote_jinad_parser(parser):
    """Add the networking options for JinaD
    :param parser: the parser
    """
    gp = add_arg_group(parser, title='RemoteJinad')
    _add_host(gp)

    gp.add_argument(
        '--port',
        type=int,
        default=8000,
        help='The port of the host exposed for connecting to.',
    )


def _add_host(arg_group):
    arg_group.add_argument(
        '--host',
        type=str,
        default=__default_host__,
        help=f'The host address of JinaD, by default it is {__default_host__}.',
    )


def get_main_parser():
    """
    Return main parser
    :return: main parser
    """

    parser = set_base_parser()

    mixin_remote_jinad_parser(parser)
    mixin_base_ppr_parser(parser)
    mixin_daemon_parser(parser)

    from jina import __resources_path__

    parser.set_defaults(
        port=8000,
        workspace='/tmp/jinad',
        log_config=os.getenv(
            'JINAD_LOG_CONFIG',
            os.path.join(__resources_path__, 'logging.daemon.yml'),
        ),
    )

    return parser


def _get_run_args(print_args: bool = True):
    """Fetch run args for jinad

    :param print_args: True if we want to print args to console
    :return: jinad args
    """
    from jina.helper import colored
    from daemon import daemon_logger

    parser = get_main_parser()
    from argparse import _StoreAction, _StoreTrueAction

    args, argv = parser.parse_known_args()
    # avoid printing for partial daemon (args.mode is set)
    if print_args and args.mode is None:

        default_args = {
            a.dest: a.default
            for a in parser._actions
            if isinstance(a, (_StoreAction, _StoreTrueAction))
        }

        with open(os.path.join(__resources_path__, 'jina.logo')) as fp:
            logo_str = fp.read()
        param_str = []
        for k, v in sorted(vars(args).items()):
            j = f'{k.replace("_", "-"): >30.30} = {str(v):30.30}'
            if default_args.get(k, None) == v:
                param_str.append('   ' + j)
            else:
                param_str.append('🔧️ ' + colored(j, 'blue', 'on_yellow'))
        param_str = '\n'.join(param_str)
        daemon_logger.info(f'\n{logo_str}\n▶️  {" ".join(sys.argv)}\n{param_str}\n')
    return args
