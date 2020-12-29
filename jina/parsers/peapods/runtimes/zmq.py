import os

from ...base import set_base_parser
from ...helper import add_arg_group
from .... import __default_host__
from ....helper import random_port


def mixin_zmq_runtime_parser(parser=None):
    """Mixing in arguments required by :class:`ZMQRuntime` into the given parser."""

    if not parser:
        parser = set_base_parser()

    gp0 = add_arg_group(parser, title='ZMQRuntime')
    gp0.add_argument('--host', type=str, default=__default_host__,
                     help=f'host address of the runtime, by default it is {__default_host__}.')
    gp0.add_argument('--port-ctrl', type=int, default=os.environ.get('JINA_CONTROL_PORT', random_port()),
                     help='port for controlling the runtime, default a random port between [49152, 65535]')
    gp0.add_argument('--ctrl-with-ipc', action='store_true', default=False,
                     help='use ipc protocol for control socket')
    gp0.add_argument('--timeout-ctrl', type=int, default=5000,
                     help='timeout (ms) of the control request, -1 for waiting forever')

    gp0.add_argument('--ssh-server', type=str, default=None,
                     help='the SSH server through which the tunnel will be created, '
                          'can actually be a fully specified "user@server:port" ssh url.')
    gp0.add_argument('--ssh-keyfile', type=str, default=None,
                     help='this specifies a key to be used in ssh login, default None. '
                          'regular default ssh keys will be used without specifying this argument.')
    gp0.add_argument('--ssh-password', type=str, default=None,
                     help='ssh password to the ssh server.')


    return parser