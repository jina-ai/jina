import argparse

from pkg_resources import resource_filename

from jina.helper import get_random_identity
from jina.parsers.base import set_base_parser
from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS


def mixin_base_peapods_parser(parser=None):
    """Mixing in arguments required by peapods module into the given parser.
    """
    if not parser:
        parser = set_base_parser()

    gp0 = add_arg_group(parser, title='Base Pea/Pod/Runtime')
    gp0.add_argument('--name', type=str,
                     help='the name of this Pea, used to identify the pea/pod and its logs.')
    gp0.add_argument('--identity', type=str, default=get_random_identity(),
                     help='the identity of the sockets, default a random string. Important for load balancing messages'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp0.add_argument('--log-config', type=str,
                     default=resource_filename('jina',
                                               '/'.join(('resources', 'logging.default.yml'))),
                     help='the yaml config of the logger. note the executor inside will inherit this log config')
    gp0.add_argument('--log-id', type=str, default=get_random_identity(),
                     help='the log id used to aggregate logs by fluentd' if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    return parser


