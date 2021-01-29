import argparse

from ...helper import add_arg_group, _SHOW_ALL_ARGS
from .... import __default_host__
from ....enums import OnErrorStrategy, SocketType
from ....helper import random_port


def mixin_zed_runtime_parser(parser):
    """Mixing in arguments required by :class:`ZEDRuntime` into the given parser."""

    gp = add_arg_group(parser, title='ZEDRuntime')

    gp.add_argument('--uses', type=str, default='_pass',
                    help='''
The config of the executor, it could be one of the followings: 
- an Executor-level YAML file path (*.yml/yaml) 
- a name of a class inherited from `jina.Executor`
- a docker image (must start with `docker://`)
- builtin executors, e.g. `_pass`, `_logforward`, `_merge` 
- the string literal of a YAML config (must start with `!`)
- the string literal of a JSON config
- the string literal of a YAML driver config (must start with `- !!`)

When use it under Python, one can use the following values additionally:
- a Python dict that represents the config
- a text file stream has `.read()` interface
''')
    gp.add_argument('--py-modules', type=str, nargs='*', metavar='PATH',
                    help='''
The customized python modules need to be imported before loading the executor

Note, when importing multiple files and there is a dependency between them, then one has to write the dependencies in 
reverse order. That is, if `__init__.py` depends on `A.py`, which again depends on `B.py`, then you need to write: 

--py-modules __init__.py --py-modules B.py --py-modules A.py

''')

    gp.add_argument('--port-in', type=int, default=random_port(),
                    help='The port for input data, default a random port between [49152, 65535]')
    gp.add_argument('--port-out', type=int, default=random_port(),
                    help='The port for output data, default a random port between [49152, 65535]')
    gp.add_argument('--host-in', type=str, default=__default_host__,
                    help=f'The host address for input, by default it is {__default_host__}')
    gp.add_argument('--host-out', type=str, default=__default_host__,
                    help=f'The host address for output, by default it is {__default_host__}')
    gp.add_argument('--socket-in', type=SocketType.from_string, choices=list(SocketType),
                    default=SocketType.PULL_BIND,
                    help='The socket type for input port')
    gp.add_argument('--socket-out', type=SocketType.from_string, choices=list(SocketType),
                    default=SocketType.PUSH_BIND,
                    help='The socket type for output port')

    gp.add_argument('--dump-interval', type=int, default=240,
                    help='Serialize the model in the pod every n seconds if model changes. '
                         '-1 means --read-only. ')
    gp.add_argument('--read-only', action='store_true', default=False,
                    help='If set, do not allow the pod to modify the model, '
                         'dump_interval will be ignored')

    gp.add_argument('--memory-hwm', type=int, default=-1,
                    help='The memory high watermark of this pod in Gigabytes, pod will restart when this is reached. '
                         '-1 means no restriction')

    gp.add_argument('--on-error-strategy', type=OnErrorStrategy.from_string, choices=list(OnErrorStrategy),
                    default=OnErrorStrategy.IGNORE,
                    help='''
The skip strategy on exceptions.

- IGNORE: Ignore it, keep running all Drivers & Executors logics in the sequel flow
- SKIP_EXECUTOR: Skip all Executors in the sequel, but drivers are still called
- SKIP_HANDLE: Skip all Drivers & Executors in the sequel, only `pre_hook` and `post_hook` are called
- THROW_EARLY: Immediately throw the exception, the sequel flow will not be running at all 
                    
Note, `IGNORE`, `SKIP_EXECUTOR` and `SKIP_HANDLE` do not guarantee the success execution in the sequel flow. If something 
is wrong in the upstream, it is hard to carry this exception and moving forward without any side-effect.
''')

    gp.add_argument('--num-part', type=int, default=0,
                    help='the number of messages expected from upstream, 0 and 1 means single part'
                    if _SHOW_ALL_ARGS else argparse.SUPPRESS)

