"""
Top-level module of Jina.

The primary function of this module is to import all of the public Jina
interfaces into a single place. The interfaces themselves are located in
sub-modules, as described below.

"""

# DO SOME OS-WISE PATCHES

import datetime as _datetime
import os as _os
import platform as _platform
import signal as _signal
import sys as _sys
import types as _types

if _sys.version_info < (3, 7, 0):
    raise OSError(f'Jina requires Python 3.7 and above, but yours is {_sys.version_info}')

if _sys.version_info >= (3, 8, 0) and _platform.system() == 'Darwin':
    # temporary fix for python 3.8 on macos where the default start is set to "spawn"
    # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    from multiprocessing import set_start_method as _set_start_method

    _set_start_method('fork')

# fix fork error on MacOS but seems no effect? must do EXPORT manually before jina start
_os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

# Underscore variables shared globally

__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

# do not change this line manually
# this is managed by git tag and updated on every release
# NOTE: this represents the NEXT release version
__version__ = '0.7.11'

# do not change this line manually
# this is managed by proto/build-proto.sh and updated on every execution
__proto_version__ = '0.0.76'

__uptime__ = _datetime.datetime.now().strftime('%Y%m%d%H%M%S')

# update on MacOS
# 1. clean this tuple,
# 2. grep -ohE "\'JINA_.*?\'" **/*.py | sort -u | sed "s/$/,/g"
# 3. copy all lines EXCEPT the first (which is the grep command in the last line)
__jina_env__ = ('JINA_ARRAY_QUANT',
                'JINA_BINARY_DELIMITER',
                'JINA_CONTRIB_MODULE',
                'JINA_CONTRIB_MODULE_IS_LOADING',
                'JINA_CONTROL_PORT',
                'JINA_DB_COLLECTION',
                'JINA_DB_HOSTNAME',
                'JINA_DB_NAME',
                'JINA_DB_PASSWORD',
                'JINA_DB_USERNAME',
                'JINA_DEFAULT_HOST',
                'JINA_DISABLE_UVLOOP',
                'JINA_EXECUTOR_WORKDIR',
                'JINA_FULL_CLI',
                'JINA_IPC_SOCK_TMP',
                'JINA_LOG_CONFIG',
                'JINA_LOG_NO_COLOR',
                'JINA_POD_NAME',
                'JINA_PROFILING',
                'JINA_RANDOM_PORTS',
                'JINA_SOCKET_HWM',
                'JINA_TEST_GPU',
                'JINA_TEST_PRETRAINED',
                'JINA_VCS_VERSION',
                'JINA_WARN_UNNAMED')

__default_host__ = _os.environ.get('JINA_DEFAULT_HOST', '0.0.0.0')
__ready_msg__ = 'ready and listening'
__stop_msg__ = 'terminated'
__binary_delimiter__ = _os.environ.get('JINA_BINARY_DELIMITER', '460841a0a8a430ae25d9ad7c1f048c57').encode()
__root_dir__ = _os.path.dirname(_os.path.abspath(__file__))

_names_with_underscore = ['__version__', '__copyright__', '__license__',
                          '__proto_version__', '__default_host__', '__ready_msg__',
                          '__stop_msg__', '__binary_delimiter__', '__jina_env__',
                          '__uptime__', '__root_dir__']

# ADD GLOBAL NAMESPACE VARIABLES

JINA_GLOBAL = _types.SimpleNamespace()
JINA_GLOBAL.logserver = _types.SimpleNamespace()

import jina.importer as _ji

# driver first, as executor may contain driver
_ji.import_classes('jina.drivers', show_import_table=False, import_once=True)
_ji.import_classes('jina.executors', show_import_table=False, import_once=True)
_ji.import_classes('jina.hub', show_import_table=False, import_once=True)

_signal.signal(_signal.SIGINT, _signal.default_int_handler)


def _set_nofile(nofile_atleast=4096):
    """
    sets nofile soft limit to at least 4096, useful for running matlplotlib/seaborn on
    parallel executing plot generators vs. Ubuntu default ulimit -n 1024 or OS X El Captian 256
    temporary setting extinguishing with Python session.
    """

    try:
        import resource as res
    except ImportError:  # Windows
        res = None

    from .logging import default_logger
    if res is None:
        return (None,) * 2

    soft, ohard = res.getrlimit(res.RLIMIT_NOFILE)
    hard = ohard

    if soft < nofile_atleast:
        soft = nofile_atleast
        if hard < soft:
            hard = soft

        default_logger.debug(f'setting soft & hard ulimit -n {soft} {hard}')
        try:
            res.setrlimit(res.RLIMIT_NOFILE, (soft, hard))
        except (ValueError, res.error):
            try:
                hard = soft
                default_logger.warning(f'trouble with max limit, retrying with soft,hard {soft},{hard}')
                res.setrlimit(res.RLIMIT_NOFILE, (soft, hard))
            except Exception:
                default_logger.warning('failed to set ulimit, giving up')
                soft, hard = res.getrlimit(res.RLIMIT_NOFILE)

    default_logger.debug(f'ulimit -n soft,hard: {soft} {hard}')
    return soft, hard


_set_nofile()

# Primitive data type
from jina.types.ndarray.generic import NdArray
from jina.types.request import Request
from jina.types.message import Message
from jina.types.querylang import QueryLang
from jina.types.document import Document

# Flow
from jina.flow import Flow

__all__ = [_s for _s in dir() if not _s.startswith('_')]
__all__.extend([_s for _s in _names_with_underscore])
