from jina.parsers.helper import KVAppendAction


def mixin_grpc_channel_options_parser(arg_group):
    """Mixing in arguments required by any class that extends :class:`AsynNewLoopRuntime` into the given parser.
    :param arg_group: the parser instance to which we add arguments
    """

    arg_group.add_argument(
        '--grpc-channel-options',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help="Dictionary of kwargs arguments that will be passed to the grpc channel as options when creating a channel, example : {'grpc.max_send_message_length': -1}. When max_attempts > 1, the 'grpc.service_config' option will not be applicable.",
        default=None,
    )
