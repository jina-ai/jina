import argparse
from argparse import ArgumentParser

from ...base import set_base_parser
from ...helper import add_arg_group, _SHOW_ALL_ARGS
from .... import __default_host__
from ....enums import SkipOnErrorType, SocketType
from ....helper import random_port


def mixin_zed_runtime_parser(parser=None) -> 'ArgumentParser':
    """Mixing in arguments required by :class:`ZEDRuntime` into the given parser."""

    if not parser:
        parser = set_base_parser()

    gp0 = add_arg_group(parser, title='ZEDRuntime')

    gp0.add_argument('--uses', type=str, default='_pass',
                     help='the config of the executor, it could be '
                          '> a YAML file path, '
                          '> a supported executor\'s class name, '
                          '> one of "_clear", "_pass", "_logforward" '
                          '> the content of YAML config (must starts with "!")'
                          '> a docker image')
    gp0.add_argument('--py-modules', type=str, nargs='*', metavar='PATH',
                     help='the customized python modules need to be imported before loading the'
                          ' executor')

    gp0.add_argument('--port-in', type=int, default=random_port(),
                     help='port for input data, default a random port between [49152, 65535]')
    gp0.add_argument('--port-out', type=int, default=random_port(),
                     help='port for output data, default a random port between [49152, 65535]')
    gp0.add_argument('--host-in', type=str, default=__default_host__,
                     help=f'host address for input, by default it is {__default_host__}')
    gp0.add_argument('--host-out', type=str, default=__default_host__,
                     help=f'host address for output, by default it is {__default_host__}')
    gp0.add_argument('--socket-in', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PULL_BIND,
                     help='socket type for input port')
    gp0.add_argument('--socket-out', type=SocketType.from_string, choices=list(SocketType),
                     default=SocketType.PUSH_BIND,
                     help='socket type for output port')

    gp0.add_argument('--dump-interval', type=int, default=240,
                     help='serialize the model in the pod every n seconds if model changes. '
                          '-1 means --read-only. ')
    gp0.add_argument('--read-only', action='store_true', default=False,
                     help='do not allow the pod to modify the model, '
                          'dump_interval will be ignored')
    gp0.add_argument('--separated-workspace', action='store_true', default=False,
                     help='the data and config files are separated for each pea in this pod, '
                          'only effective when BasePod\'s `parallel` > 1')

    gp0.add_argument('--memory-hwm', type=int, default=-1,
                     help='memory high watermark of this pod in Gigabytes, pod will restart when this is reached. '
                          '-1 means no restriction')
    gp0.add_argument('--max-idle-time', type=int, default=60,
                     help='label this pea as inactive when it does not '
                          'process any request after certain time (in second)')

    gp0.add_argument('--skip-on-error', type=SkipOnErrorType.from_string, choices=list(SkipOnErrorType),
                     default=SkipOnErrorType.NONE,
                     help='skip strategy on error message.')

    gp0.add_argument('--num-part', type=int, default=0,
                     help='the number of messages expected from upstream, 0 and 1 means single part'
                     if _SHOW_ALL_ARGS else argparse.SUPPRESS)

    return parser
