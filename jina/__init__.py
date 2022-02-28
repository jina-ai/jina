"""
Top-level module of Jina.

The primary function of this module is to import all of the public Jina
interfaces into a single place. The interfaces themselves are located in
sub-modules, as described below.

"""

import datetime as _datetime
import os as _os
import platform as _platform
import signal as _signal
import sys as _sys
import types as _types
import warnings as _warnings
import docarray as _docarray


if _sys.version_info < (3, 7, 0):
    raise OSError(f'Jina requires Python >= 3.7, but yours is {_sys.version_info}')

__windows__ = _sys.platform == 'win32'


def _warning_on_one_line(message, category, filename, lineno, *args, **kwargs):
    return '\033[1;33m%s: %s\033[0m \033[1;30m(raised from %s:%s)\033[0m\n' % (
        category.__name__,
        message,
        filename,
        lineno,
    )


_warnings.formatwarning = _warning_on_one_line
_warnings.simplefilter('always', DeprecationWarning)

# fix fork error on MacOS but seems no effect? must do EXPORT manually before jina start
_os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# JINA_MP_START_METHOD has higher priority than os-patch
_start_method = _os.environ.get('JINA_MP_START_METHOD', None)

if _start_method and _start_method.lower() in {'fork', 'spawn', 'forkserver'}:
    from multiprocessing import set_start_method as _set_start_method

    _set_start_method(_start_method.lower())
    _warnings.warn(f'multiprocessing start method is set to `{_start_method.lower()}`')
    _os.environ.pop('JINA_MP_START_METHOD')
elif _sys.version_info >= (3, 8, 0) and _platform.system() == 'Darwin':
    # DO SOME OS-WISE PATCHES

    # temporary fix for python 3.8 on macos where the default start is set to "spawn"
    # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    from multiprocessing import set_start_method as _set_start_method

    _set_start_method('fork')

# do not change this line manually
# this is managed by git tag and updated on every release
# NOTE: this represents the NEXT release version

__version__ = '3.0.4'

# do not change this line manually
# this is managed by proto/build-proto.sh and updated on every execution
__proto_version__ = '0.1.8'
try:
    __docarray_version__ = _docarray.__version__
except AttributeError as e:
    raise OSError(
        '`docarray` dependency is not installed correctly, please reinstall with `pip install -U --force-reinstall docarray`'
    )

__uptime__ = _datetime.datetime.now().isoformat()

# update on MacOS
# 1. clean this tuple,
# 2. grep -rohEI --exclude-dir=jina/hub --exclude-dir=tests --include \*.py "\'JINA_.*?\'" jina  | sort -u | sed "s/$/,/g"
# 3. copy all lines EXCEPT the first (which is the grep command in the last line)
__jina_env__ = (
    'JINA_ARRAY_QUANT',
    'JINA_CONTROL_PORT',
    'JINA_DEFAULT_HOST',
    'JINA_DEFAULT_TIMEOUT_CTRL',
    'JINA_DISABLE_UVLOOP',
    'JINA_FULL_CLI',
    'JINA_HUBBLE_REGISTRY',
    'JINA_HUB_CACHE_DIR',
    'JINA_HUB_ROOT',
    'JINA_K8S_USE_TEST_PIP',
    'JINA_LOG_CONFIG',
    'JINA_LOG_LEVEL',
    'JINA_LOG_NO_COLOR',
    'JINA_LOG_WORKSPACE',
    'JINA_MP_START_METHOD',
    'JINA_OPTIMIZER_TRIAL_WORKSPACE',
    'JINA_DEPLOYMENT_NAME',
    'JINA_RANDOM_PORT_MAX',
    'JINA_RANDOM_PORT_MIN',
    'JINA_VCS_VERSION',
)

__default_host__ = _os.environ.get(
    'JINA_DEFAULT_HOST', '127.0.0.1' if __windows__ else '0.0.0.0'
)
__docker_host__ = 'host.docker.internal'
__default_executor__ = 'BaseExecutor'
__default_reducer_executor__ = 'ReducerExecutor'
__default_endpoint__ = '/default'
__ready_msg__ = 'ready and listening'
__stop_msg__ = 'terminated'
__unset_msg__ = '(unset)'
__args_executor_func__ = {
    'docs',
    'parameters',
    'docs_matrix',
}
__args_executor_init__ = {'metas', 'requests', 'runtime_args'}
__root_dir__ = _os.path.dirname(_os.path.abspath(__file__))
__resources_path__ = _os.path.join(
    _os.path.dirname(_sys.modules['jina'].__file__), 'resources'
)

_names_with_underscore = [
    '__version__',
    '__proto_version__',
    '__default_host__',
    '__ready_msg__',
    '__stop_msg__',
    '__jina_env__',
    '__uptime__',
    '__root_dir__',
    '__default_endpoint__',
    '__default_executor__',
    '__num_args_executor_func__',
    '__unset_msg__',
    '__windows__',
]

try:
    _signal.signal(_signal.SIGINT, _signal.default_int_handler)
except Exception as exc:
    _warnings.warn(f'failed to set default signal handler: {exc!r}`')


def _set_nofile(nofile_atleast=4096):
    """
    Set nofile soft limit to at least 4096, useful for running matlplotlib/seaborn on
    parallel executing plot generators vs. Ubuntu default ulimit -n 1024 or OS X El Captian 256
    temporary setting extinguishing with Python session.

    :param nofile_atleast: nofile soft limit
    :return: nofile soft limit and nofile hard limit
    """

    try:
        import resource as res
    except ImportError:  # Windows
        res = None

    if res is None:
        return (None,) * 2

    soft, ohard = res.getrlimit(res.RLIMIT_NOFILE)
    hard = ohard

    if soft < nofile_atleast:
        soft = nofile_atleast
        if hard < soft:
            hard = soft

        try:
            res.setrlimit(res.RLIMIT_NOFILE, (soft, hard))
        except (ValueError, res.error):
            try:
                hard = soft
                print(f'trouble with max limit, retrying with soft,hard {soft},{hard}')
                res.setrlimit(res.RLIMIT_NOFILE, (soft, hard))
            except Exception:
                print('failed to set ulimit, giving up')
                soft, hard = res.getrlimit(res.RLIMIT_NOFILE)

    return soft, hard


_set_nofile()

# ONLY FIRST CLASS CITIZENS ARE ALLOWED HERE, namely Document, Executor Flow

# Client
from jina.clients import Client

# Document
from docarray import Document, DocumentArray

# Executor
from jina.serve.executors import BaseExecutor as Executor
from jina.serve.executors.decorators import requests

# Flow
from jina.orchestrate.flow.base import Flow
from jina.orchestrate.flow.asyncio import AsyncFlow

__all__ = [_s for _s in dir() if not _s.startswith('_')]
__all__.extend(_names_with_underscore)
