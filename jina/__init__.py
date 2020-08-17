__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

# do not change this line manually
# this is managed by git tag and updated on every release
__version__ = '0.4.9'

# do not change this line manually
# this is managed by proto/build-proto.sh and updated on every execution
__proto_version__ = '0.0.58'

import platform
import sys

# do some os-wise patches

if sys.version_info < (3, 7, 0):
    raise OSError('Jina requires Python 3.7 and above, but yours is %s' % sys.version_info)

if sys.version_info >= (3, 8, 0) and platform.system() == 'Darwin':
    # temporary fix for python 3.8 on macos where the default start is set to "spawn"
    # https://docs.python.org/3/library/multiprocessing.html#contexts-and-start-methods
    from multiprocessing import set_start_method

    set_start_method('fork')

from datetime import datetime
import random
from types import SimpleNamespace
import os

# fix fork error on MacOS but seems no effect? must do EXPORT manually before jina start
os.environ['OBJC_DISABLE_INITIALIZE_FORK_SAFETY'] = 'YES'

__uptime__ = datetime.now().strftime('%Y%m%d%H%M%S')

# update on MacOS
# 1. clean this tuple,
# 2. grep -ohE "\'JINA_.*?\'" **/*.py | sort -u | sed "s/$/,/g"
# 3. copy all lines EXCEPT the first (which is the grep command in the last line)
__jina_env__ = ('JINA_ARRAY_QUANT',
                'JINA_CONTRIB_MODULE',
                'JINA_CONTRIB_MODULE_IS_LOADING',
                'JINA_CONTROL_PORT',
                'JINA_DEFAULT_HOST',
                'JINA_EXECUTOR_WORKDIR',
                'JINA_FULL_CLI',
                'JINA_IPC_SOCK_TMP',
                'JINA_LOG_FILE',
                'JINA_LOG_LONG',
                'JINA_LOG_NO_COLOR',
                'JINA_LOG_PROFILING',
                'JINA_LOG_SSE',
                'JINA_LOG_VERBOSITY',
                'JINA_POD_NAME',
                'JINA_PROFILING',
                'JINA_SOCKET_HWM',
                'JINA_STACK_CONFIG',
                'JINA_TEST_CONTAINER',
                'JINA_TEST_GPU',
                'JINA_TEST_PRETRAINED',
                'JINA_TEST_FAISS',
                'JINA_VCS_VERSION',
                'JINA_VERSION',
                'JINA_WARN_UNNAMED',
                'JINA_BINARY_DELIMITER',
                'JINA_DISABLE_UVLOOP')

__default_host__ = os.environ.get('JINA_DEFAULT_HOST', '0.0.0.0')
__ready_msg__ = 'ready and listening'
__stop_msg__ = 'terminated'
__binary_delimiter__ = os.environ.get('JINA_BINARY_DELIMITER', '460841a0a8a430ae25d9ad7c1f048c57').encode()

JINA_GLOBAL = SimpleNamespace()
JINA_GLOBAL.imported = SimpleNamespace()
JINA_GLOBAL.imported.executors = False
JINA_GLOBAL.imported.drivers = False
JINA_GLOBAL.stack = SimpleNamespace()
JINA_GLOBAL.stack.id = random.randint(0, 10000)
JINA_GLOBAL.logserver = SimpleNamespace()


def import_classes(namespace: str, targets=None,
                   show_import_table: bool = False, import_once: bool = False):
    """
    Import all or selected executors into the runtime. This is called when Jina is first imported for registering the YAML
    constructor beforehand. It can be also used to import third-part or external executors.

    :param namespace: the namespace to import
    :param targets: the list of executor names to import
    :param show_import_table: show the import result as a table
    :param import_once: import everything only once, to avoid repeated import
    """

    import os, sys

    if namespace == 'jina.executors':
        import_type = 'ExecutorType'
        if import_once and JINA_GLOBAL.imported.executors:
            return
    elif namespace == 'jina.drivers':
        import_type = 'DriverType'
        if import_once and JINA_GLOBAL.imported.drivers:
            return
    else:
        raise TypeError(f'namespace: {namespace} is unrecognized')

    from setuptools import find_packages
    import pkgutil
    from pkgutil import iter_modules
    path = os.path.dirname(pkgutil.get_loader(namespace).path)

    modules = set()

    for info in iter_modules([path]):
        if not info.ispkg:
            modules.add('.'.join([namespace, info.name]))

    for pkg in find_packages(path):
        modules.add('.'.join([namespace, pkg]))
        pkgpath = path + '/' + pkg.replace('.', '/')
        if sys.version_info.major == 2 or (sys.version_info.major == 3 and sys.version_info.minor < 6):
            for _, name, ispkg in iter_modules([pkgpath]):
                if not ispkg:
                    modules.add('.'.join([namespace, pkg, name]))
        else:
            for info in iter_modules([pkgpath]):
                if not info.ispkg:
                    modules.add('.'.join([namespace, pkg, info.name]))

    from collections import defaultdict
    load_stat = defaultdict(list)
    bad_imports = []

    if isinstance(targets, str):
        targets = {targets}
    elif isinstance(targets, list):
        targets = set(targets)
    elif targets is None:
        targets = {}
    else:
        raise TypeError(f'target must be a set, but received {targets!r}')

    depend_tree = {}
    import importlib
    from .helper import colored
    for m in modules:
        try:
            mod = importlib.import_module(m)
            for k in dir(mod):
                # import the class
                if (getattr(mod, k).__class__.__name__ == import_type) and (not targets or k in targets):
                    try:
                        _c = getattr(mod, k)
                        load_stat[m].append(
                            (k, True, colored('▸', 'green').join(f'{vvv.__name__}' for vvv in _c.mro()[:-1][::-1])))
                        d = depend_tree
                        for vvv in _c.mro()[:-1][::-1]:
                            if vvv.__name__ not in d:
                                d[vvv.__name__] = {}
                            d = d[vvv.__name__]
                        d['module'] = m
                        if k in targets:
                            targets.remove(k)
                            if not targets:
                                return  # target execs are all found and loaded, return
                        try:
                            # load the default request for this executor if possible
                            from .executors.requests import get_default_reqs
                            get_default_reqs(type.mro(getattr(mod, k)))
                        except ValueError:
                            pass
                    except Exception as ex:
                        load_stat[m].append((k, False, ex))
                        bad_imports.append('.'.join([m, k]))
                        if k in targets:
                            raise ex  # target class is found but not loaded, raise return
        except Exception as ex:
            load_stat[m].append(('', False, ex))
            bad_imports.append(m)

    if targets:
        raise ImportError(f'{targets} can not be found in jina')

    if show_import_table:
        from .helper import print_load_table, print_dep_tree_rst
        print_load_table(load_stat)
    else:
        if bad_imports:
            from .logging import default_logger
            default_logger.error(f'theses modules or classes can not be imported {bad_imports}')

    if namespace == 'jina.executors':
        JINA_GLOBAL.imported.executors = True
    elif namespace == 'jina.drivers':
        JINA_GLOBAL.imported.drivers = True

    return depend_tree


# driver first, as executor may contain driver
import_classes('jina.drivers', show_import_table=False, import_once=True)
import_classes('jina.executors', show_import_table=False, import_once=True)

# manually install the default signal handler
import signal

signal.signal(signal.SIGINT, signal.default_int_handler)

# !/usr/bin/env python
try:
    import resource as res
except ImportError:  # Windows
    res = None


def raise_nofile(nofile_atleast=4096):
    """
    sets nofile soft limit to at least 4096, useful for running matlplotlib/seaborn on
    parallel executing plot generators vs. Ubuntu default ulimit -n 1024 or OS X El Captian 256
    temporary setting extinguishing with Python session.
    """
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


raise_nofile()
