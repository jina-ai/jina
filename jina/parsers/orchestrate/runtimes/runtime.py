"""Argparser module for WorkerRuntime"""

from jina import __default_host__, helper
from jina.parsers.helper import KVAppendAction


def mixin_base_runtime_parser(arg_group):
    """Mixing in arguments required by any class that extends :class:`AsynNewLoopRuntime` into the given parser.
    :param arg_group: the parser instance to which we add arguments
    """

    arg_group.add_argument(
        '--port-in',
        type=int,
        default=helper.random_port(),
        dest='port',
        help='The port for input data to bind to, default a random port between [49152, 65535]',
    )
    arg_group.add_argument(
        '--host-in',
        type=str,
        default=__default_host__,
        help=f'The host address for binding to, by default it is {__default_host__}',
    )

    arg_group.add_argument(
        '--grpc-server-options',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help="Dictionary of kwargs arguments that will be passed to the grpc server as options when starting the server, example : {'grpc.max_send_message_length': -1}",
        default=None,
    )
