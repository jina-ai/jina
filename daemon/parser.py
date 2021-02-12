import os
import sys

from pkg_resources import resource_filename

from jina.parsers.base import set_base_parser
from jina.parsers.helper import add_arg_group
from jina.parsers.peapods.base import mixin_base_ppr_parser
from jina.parsers.peapods.runtimes.remote import mixin_remote_parser


def mixin_daemon_parser(parser):
    gp = add_arg_group(parser, title='Daemon')

    gp.add_argument('--no-fluentd',
                    action='store_true', default=False,
                    help='do not start fluentd, no log streaming')

    gp.add_argument('--workspace', type=str, default='/tmp/jinad',
                    help='the directory for storing all uploaded dependencies')


def get_main_parser():
    parser = set_base_parser()

    mixin_remote_parser(parser)
    mixin_base_ppr_parser(parser)
    mixin_daemon_parser(parser)

    parser.set_defaults(port_expose=8000,
                        log_config=os.getenv('JINAD_LOG_CONFIG',
                                             resource_filename(
                                                 'jina', '/'.join(('resources', 'logging.daemon.yml')))))

    return parser


def _get_run_args(print_args: bool = True):
    from jina.helper import colored
    from . import daemon_logger
    parser = get_main_parser()
    from argparse import _StoreAction, _StoreTrueAction
    args = parser.parse_args()
    if print_args:
        from pkg_resources import resource_filename
        default_args = {a.dest: a.default for a in parser._actions if
                        isinstance(a, (_StoreAction, _StoreTrueAction))}

        with open(resource_filename('jina', '/'.join(('resources', 'jina.logo')))) as fp:
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
