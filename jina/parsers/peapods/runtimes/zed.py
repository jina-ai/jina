"""Argparser module for ZED runtime"""
import argparse

from ...helper import add_arg_group, _SHOW_ALL_ARGS, KVAppendAction
from .... import __default_host__
from .... import helper
from ....enums import OnErrorStrategy, SocketType


def mixin_zed_runtime_parser(parser):
    """Mixing in arguments required by :class:`ZEDRuntime` into the given parser.
    :param parser: the parser instance to which we add arguments
    """

    gp = add_arg_group(parser, title='ZEDRuntime')
    from jina import __default_executor__

    gp.add_argument(
        '--uses',
        type=str,
        default=__default_executor__,
        help='''
        The config of the executor, it could be one of the followings:
        * an Executor YAML file (.yml, .yaml, .jaml)
        * a Jina Hub Executor (must start with `jinahub://` or `jinahub+docker://`)
        * a docker image (must start with `docker://`)
        * the string literal of a YAML config (must start with `!` or `jtype: `)
        * the string literal of a JSON config

        When use it under Python, one can use the following values additionally:
        - a Python dict that represents the config
        - a text file stream has `.read()` interface
        ''',
    )
    gp.add_argument(
        '--uses-with',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
    Dictionary of keyword arguments that will override the `with` configuration in `uses`
    ''',
    )
    gp.add_argument(
        '--uses-metas',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
    Dictionary of keyword arguments that will override the `metas` configuration in `uses`
    ''',
    )
    gp.add_argument(
        '--uses-requests',
        action=KVAppendAction,
        metavar='KEY: VALUE',
        nargs='*',
        help='''
        Dictionary of keyword arguments that will override the `requests` configuration in `uses`
        ''',
    )
    gp.add_argument(
        '--py-modules',
        type=str,
        nargs='*',
        metavar='PATH',
        help='''
The customized python modules need to be imported before loading the executor

Note that the recommended way is to only import a single module - a simple python file, if your
executor can be defined in a single file, or an ``__init__.py`` file if you have multiple files,
which should be structured as a python package. For more details, please see the
`Executor cookbook <https://docs.jina.ai/fundamentals/executor/repository-structure/>`__
''',
    )

    gp.add_argument(
        '--port-in',
        type=int,
        default=helper.random_port(),
        help='The port for input data, default a random port between [49152, 65535]',
    )
    gp.add_argument(
        '--port-out',
        type=int,
        default=helper.random_port(),
        help='The port for output data, default a random port between [49152, 65535]',
    )
    gp.add_argument(
        '--hosts-in-connect',
        type=str,
        nargs='*',
        help=f'The host address for input, by default it is {__default_host__}',
    )
    gp.add_argument(
        '--host-in',
        type=str,
        default=__default_host__,
        help=f'The host address for input, by default it is {__default_host__}',
    )
    gp.add_argument(
        '--host-out',
        type=str,
        default=__default_host__,
        help=f'The host address for output, by default it is {__default_host__}',
    )
    gp.add_argument(
        '--socket-in',
        type=SocketType.from_string,
        choices=list(SocketType),
        default=SocketType.PULL_BIND,
        help='The socket type for input port',
    )
    gp.add_argument(
        '--socket-out',
        type=SocketType.from_string,
        choices=list(SocketType),
        default=SocketType.PUSH_BIND,
        help='The socket type for output port',
    )

    gp.add_argument(
        '--memory-hwm',
        type=int,
        default=-1,
        help='The memory high watermark of this pod in Gigabytes, pod will restart when this is reached. '
        '-1 means no restriction',
    )

    gp.add_argument(
        '--on-error-strategy',
        type=OnErrorStrategy.from_string,
        choices=list(OnErrorStrategy),
        default=OnErrorStrategy.IGNORE,
        help='''
The skip strategy on exceptions.

- IGNORE: Ignore it, keep running all Executors in the sequel flow
- SKIP_HANDLE: Skip all Executors in the sequel, only `pre_hook` and `post_hook` are called
- THROW_EARLY: Immediately throw the exception, the sequel flow will not be running at all

Note, `IGNORE`, `SKIP_EXECUTOR` and `SKIP_HANDLE` do not guarantee the success execution in the sequel flow. If something
is wrong in the upstream, it is hard to carry this exception and moving forward without any side-effect.
''',
    )

    gp.add_argument(
        '--native',
        action='store_true',
        default=False,
        help='If set, only native Executors is allowed, and the Executor is always run inside ZEDRuntime.',
    )

    gp.add_argument(
        '--num-part',
        type=int,
        default=0,
        help='the number of messages expected from upstream, 0 and 1 means single part'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--dynamic-routing-out',
        action='store_true',
        default=False,
        help='Tells if ZEDRuntime should respect routing graph for outgoing traffic.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--dynamic-routing-in',
        action='store_true',
        default=False,
        help='Tells if ZEDRuntime should handle incoming traffic as dynamic routing.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--grpc-data-requests',
        action='store_true',
        default=False,
        help='Tells if a Pea should use gRPC for data requests. Works only with dynamic routing out.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--runs-in-docker',
        action='store_true',
        default=False,
        help='Informs a Pea that runs in a container. Important to properly set networking information',
    )

    gp.add_argument(
        '--dump-path',
        type=str,
        default='',
        help='Dump path to be passed to the executor'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )

    gp.add_argument(
        '--k8s-disable-connection-pool',
        action='store_false',
        dest='k8s_connection_pool',
        default=True,
        help='Defines if connection pooling for replicas should be disabled in K8s. This mechanism implements load balancing between replicas of the same executor. This should be disabled if a service mesh (like istio) is used for load balancing.'
        if _SHOW_ALL_ARGS
        else argparse.SUPPRESS,
    )
