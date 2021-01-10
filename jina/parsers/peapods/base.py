import argparse

from pkg_resources import resource_filename

from ..helper import add_arg_group, _SHOW_ALL_ARGS
from ...helper import get_random_identity


def mixin_base_ppr_parser(parser):
    """Mixing in arguments required by pea/pod/runtime module into the given parser.
    """

    gp = add_arg_group(parser, title='Essential')
    gp.add_argument('--name', type=str,
                    help='the name of this Pea, used to identify the pea/pod and its logs.')

    gp.add_argument('--log-config', type=str,
                    default=resource_filename('jina',
                                              '/'.join(('resources', 'logging.default.yml'))),
                    help='the yaml config of the logger. note the executor inside will inherit this log config')

    # hidden CLI used for internal only

    gp.add_argument('--identity', type=str, default=get_random_identity(),
                    help='the identity of the sockets, default a random string. Important for load balancing messages'
                    if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp.add_argument('--log-id', type=str, default=get_random_identity(),
                    help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp.add_argument('--show-exc-info', action='store_true', default=False,
                    help='if true then exception stack information to be added to the logging message, '
                         'useful in debugging')