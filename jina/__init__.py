# do not change this line manually
# this is managed by git tag and updated on every release
__version__ = '0.0.1'

# do not change this line manually
# this is managed by proto/build-proto.sh and updated on every execution
__proto_version__ = '0.0.5'

from datetime import datetime

__uptime__ = datetime.now().strftime('%Y%m%d%H%M%S')

__jina_env__ = ('JINA_PROFILING',
                'JINA_WARN_UNNAMED',
                'JINA_VCS_VERSION',
                'JINA_CONTROL_PORT',
                'JINA_CONTRIB_MODULE',
                'JINA_IPC_SOCK_TMP',
                'JINA_LOG_FORMAT',
                'JINA_SOCKET_HWM',
                'JINA_ARRAY_QUANT')

from types import SimpleNamespace
import os

__default_host__ = os.environ.get('JINA_DEFAULT_HOST', '0.0.0.0')
__ready_signal__ = 'ready and listening'

JINA_GLOBAL = SimpleNamespace()
JINA_GLOBAL.imported = SimpleNamespace()
JINA_GLOBAL.imported.executors = False
JINA_GLOBAL.imported.drivers = False


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
        raise TypeError('namespace: %s is unrecognized' % namespace)

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
        raise TypeError('target must be a set, but received %r' % targets)

    import importlib
    for m in modules:
        try:
            mod = importlib.import_module(m)
            for k in dir(mod):
                # import the class
                if (getattr(mod, k).__class__.__name__ == import_type) and (not targets or k in targets):
                    try:
                        getattr(mod, k)
                        load_stat[m].append((k, True, ''))
                        if k in targets:
                            targets.remove(k)
                            if not targets:
                                return  # target execs are all found and loaded, return
                    except Exception as ex:
                        load_stat[m].append((k, False, ex))
                        bad_imports.append('.'.join([m, k]))
                        if k in targets:
                            raise ex  # target class is found but not loaded, raise return
        except Exception as ex:
            load_stat[m].append(('', False, ex))
            bad_imports.append(m)

    if targets:
        raise ImportError('%s can not be found in jina' % targets)

    if show_import_table:
        from .helper import print_load_table
        print_load_table(load_stat)
    else:
        if bad_imports:
            from .logging import default_logger
            default_logger.error('theses modules or classes can not be imported %s' % bad_imports)

    if namespace == 'jina.executors':
        JINA_GLOBAL.imported.executors = True
    elif namespace == 'jina.drivers':
        JINA_GLOBAL.imported.drivers = True


import_classes('jina.executors', show_import_table=False, import_once=True)
import_classes('jina.drivers', show_import_table=False, import_once=True)

# manually install the default signal handler
import signal

signal.signal(signal.SIGINT, signal.default_int_handler)
