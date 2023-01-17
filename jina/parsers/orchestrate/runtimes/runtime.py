"""Argparser module for WorkerRuntime"""

from jina.parsers.helper import KVAppendAction


def mixin_base_runtime_parser(arg_group):
    """Mixing in arguments required by any class that extends :class:`AsynNewLoopRuntime` into the given parser.
    :param arg_group: the parser instance to which we add arguments
    """

    arg_group.add_argument(
        '--grpc-server-options',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help="Dictionary of kwargs arguments that will be passed to the grpc server as options when starting the "
             "server, example : {'grpc.max_send_message_length': -1}",
        default=None,
    )


def mixin_raft_parser(arg_group):
    """Mixing in arguments required by the RAFT Node. All these args are used to configure the RAFT nodes
    """

    arg_group.add_argument(
        '--raft-configuration',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help="Dictionary of kwargs arguments that will be passed to the RAFT node as configuration options when "
             "starting the RAFT node.",
        default=None,
    )
