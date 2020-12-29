import argparse

from jina.parsers.base import set_base_parser
from jina.parsers.helper import add_arg_group, _SHOW_ALL_ARGS


def set_pea_parser(parser=None):
    from ...enums import SocketType, PeaRoleType, SkipOnErrorType
    from ...helper import random_port, get_random_identity
    from ... import __default_host__

    if not parser:
        parser = set_base_parser()

    set_runtime_parser(parser)

    gp0 = add_arg_group(parser, 'pea basic arguments')
    gp0.add_argument('--identity', type=str, default=get_random_identity(),
                     help='the identity of the sockets, default a random string (Important for load balancing messages'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp2 = add_arg_group(parser, 'pea network arguments')

    gp2.add_argument('--host', type=str, default=__default_host__,
                     help=f'host address of the pea, by default it is {__default_host__}.')
    gp2.add_argument('--port-in', type=int, default=random_port(),
                     help='port for input data, default a random port between [49152, 65535]')
    gp2.add_argument('--port-out', type=int, default=random_port(),
                     help='port for output data, default a random port between [49152, 65535]')
    gp2.add_argument('--host-in', type=str, default=__default_host__,
                     help=f'host address for input, by default it is {__default_host__}')
    gp2.add_argument('--host-out', type=str, default=__default_host__,
                     help=f'host address for output, by default it is {__default_host__}')
    gp2.add_argument('--socket-in', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PULL_BIND,
                     help='socket type for input port')
    gp2.add_argument('--socket-out', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PUSH_BIND,
                     help='socket type for output port')
    gp2.add_argument('--port-ctrl', type=int, default=os.environ.get('JINA_CONTROL_PORT', random_port()),
                     help='port for controlling the pod, default a random port between [49152, 65535]')
    gp2.add_argument('--ctrl-with-ipc', action='store_true', default=False,
                     help='use ipc protocol for control socket')
    gp2.add_argument('--timeout-ctrl', type=int, default=5000,
                     help='timeout (ms) of the control request, -1 for waiting forever')
    gp2.add_argument('--timeout', type=int, default=-1,
                     help='timeout (ms) of all requests, -1 for waiting forever')
    gp2.add_argument('--expose-public', action='store_true', default=False,
                     help='expose the public IP address to remote when necessary, by default it exposes'
                          'private IP address, which only allows accessing under the same network/subnet')

    gp3 = add_arg_group(parser, 'pea IO arguments')
    gp3.add_argument('--dump-interval', type=int, default=240,
                     help='serialize the model in the pod every n seconds if model changes. '
                          '-1 means --read-only. ')
    gp3.add_argument('--read-only', action='store_true', default=False,
                     help='do not allow the pod to modify the model, '
                          'dump_interval will be ignored')
    gp3.add_argument('--separated-workspace', action='store_true', default=False,
                     help='the data and config files are separated for each pea in this pod, '
                          'only effective when BasePod\'s `parallel` > 1')
    gp3.add_argument('--pea-id', type=int, default=-1,
                     help='the id of the storage of this pea, only effective when `separated_workspace=True`'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    gp5 = add_arg_group(parser, 'pea messaging arguments')
    gp5.add_argument('--num-part', type=int, default=0,
                     help='the number of messages expected from upstream, 0 and 1 means single part'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp5.add_argument('--role', type=PeaRoleType.from_string, choices=list(PeaRoleType),
                     help='the role of this pea in a pod' if _SHOW_ALL_ARGS else argparse.SUPPRESS)
    gp5.add_argument('--skip-on-error', type=SkipOnErrorType.from_string, choices=list(SkipOnErrorType),
                     default=SkipOnErrorType.NONE,
                     help='skip strategy on error message.')

    gp6 = add_arg_group(parser, 'pea EXPERIMENTAL arguments')
    gp6.add_argument('--memory-hwm', type=int, default=-1,
                     help='memory high watermark of this pod in Gigabytes, pod will restart when this is reached. '
                          '-1 means no restriction')
    gp6.add_argument('--max-idle-time', type=int, default=60,
                     help='label this pea as inactive when it does not '
                          'process any request after certain time (in second)')

    gp8 = add_arg_group(parser, 'ssh tunneling arguments')
    gp8.add_argument('--ssh-server', type=str, default=None,
                     help='the SSH server through which the tunnel will be created, '
                          'can actually be a fully specified "user@server:port" ssh url.')
    gp8.add_argument('--ssh-keyfile', type=str, default=None,
                     help='this specifies a key to be used in ssh login, default None. '
                          'regular default ssh keys will be used without specifying this argument.')
    gp8.add_argument('--ssh-password', type=str, default=None,
                     help='ssh password to the ssh server.')

    return parser