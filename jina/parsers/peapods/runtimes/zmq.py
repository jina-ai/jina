"""Argparser module for ZMQ runtimes"""
import os

from ...helper import add_arg_group
from .... import helper


def mixin_zmq_runtime_parser(parser):
    """Mixing in arguments required by :class:`ZMQRuntime` into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='ZMQRuntime')
    gp.add_argument(
        '--zmq-identity',
        type=str,
        help='The identity of a ZMQRuntime. It is used for unique socket identification towards other ZMQRuntimes.',
    )
    gp.add_argument(
        '--port-ctrl',
        type=int,
        default=os.environ.get('JINA_CONTROL_PORT', helper.random_port()),
        help='The port for controlling the runtime, default a random port between [49152, 65535]',
    )
    gp.add_argument(
        '--ctrl-with-ipc',
        action='store_true',
        default=False,
        help='If set, use ipc protocol for control socket',
    )
    gp.add_argument(
        '--timeout-ctrl',
        type=int,
        default=int(os.getenv('JINA_DEFAULT_TIMEOUT_CTRL', '5000')),
        help='The timeout in milliseconds of the control request, -1 for waiting forever',
    )

    gp.add_argument(
        '--ssh-server',
        type=str,
        default=None,
        help='The SSH server through which the tunnel will be created, '
        'can actually be a fully specified `user@server:port` ssh url.',
    )
    gp.add_argument(
        '--ssh-keyfile',
        type=str,
        default=None,
        help='This specifies a key to be used in ssh login, default None. '
        'regular default ssh keys will be used without specifying this argument.',
    )
    gp.add_argument(
        '--ssh-password',
        type=str,
        default=None,
        help='The ssh password to the ssh server.',
    )
