import os
import sys
import warnings
from types import SimpleNamespace, ModuleType
from typing import Optional, List, Any, Dict

IMPORTED = SimpleNamespace()
IMPORTED.executors = False
IMPORTED.executors = False
IMPORTED.drivers = False
IMPORTED.hub = False


def _parse_targets(targets):
    if isinstance(targets, str):
        ret = {targets}
    elif isinstance(targets, list):
        ret = set(targets)
    elif targets is None:
        ret = {}
    else:
        raise TypeError(f'target must be a set, but received {targets!r}')
    return ret


def _raise_bad_imports_warnings(bad_imports, namespace):
    if not bad_imports:
        return
    if namespace != 'jina.hub':
        warnings.warn(
            f'theses modules or classes can not be imported {bad_imports}. '
            f'You can use `jina check` to list all executors and drivers')
    else:
        warnings.warn(
            f'due to the missing dependencies or bad implementations, '
            f'{bad_imports} can not be imported '
            f'if you are using these executors/drivers, they wont work. '
            f'You can use `jina check` to list all executors and drivers')


def _get_modules(namespace):
    from setuptools import find_packages
    from pkgutil import get_loader

    try:
        path = os.path.dirname(get_loader(namespace).path)
    except AttributeError as e:
        if namespace == 'jina.hub':
            warnings.warn(f'hub submodule is not initialized. Please try "git submodule update --init"', ImportWarning)
        raise ImportError(f'{namespace} can not be imported. {e}')

    modules = _get_submodules(path, namespace)

    for pkg in find_packages(path):
        modules.add('.'.join([namespace, pkg]))
        pkgpath = os.path.join(path, pkg.replace('.', '/'))
        modules = modules.union(_get_submodules(pkgpath, namespace, prefix=pkg))

    return _filter_modules(modules)


def _get_submodules(path, namespace, prefix=None):
    from pkgutil import iter_modules
    _prefix = '.'.join([namespace, prefix]) if prefix else namespace
    modules = set()
    for info in iter_modules([path]):
        is_hub_module = namespace == 'jina.hub' and info.ispkg
        is_nonhub_module = namespace != 'jina.hub' and not info.ispkg
        module_name = '.'.join([_prefix, info.name])
        if is_hub_module or is_nonhub_module:
            modules.add(module_name)
    return modules


def _filter_modules(modules):
    import re
    ignored_module_pattern = re.compile(r'\.tests|\.api|\.bump_version')
    return {m for m in modules if not ignored_module_pattern.findall(m)}


def _load_default_config(cls_obj):
    from .executors.requests import get_default_reqs
    try:
        _request = get_default_reqs(type.mro(cls_obj))
    except ValueError as e:
        warnings.warn(f'Please ensure a config yml is given for {cls_obj.__class__.__name__}. {e}')
        pass


def import_classes(namespace: str, targets=None,
                   show_import_table: bool = False,
                   import_once: bool = False):
    """
    Import all or selected executors into the runtime. This is called when Jina is first imported for registering the YAML
    constructor beforehand. It can be also used to import third-part or external executors.

    :param namespace: the namespace to import
    :param targets: the list of executor names to import
    :param show_import_table: show the import result as a table
    :param import_once: import everything only once, to avoid repeated import

    :return: for `targets=None`, the dependency tree of the imported classes under the `namespace`; for `target!=None`, the imported class object
    """

    _namespace2type = {
        'jina.executors': 'ExecutorType',
        'jina.drivers': 'DriverType',
        'jina.hub': 'ExecutorType'
    }
    _import_type = _namespace2type.get(namespace)
    if _import_type is None:
        raise TypeError(f'namespace: {namespace} is unrecognized')

    _targets = _parse_targets(targets)
    _return_cls_obj = True if _targets else False
    _imported_property = namespace.split('.')[-1]
    _is_imported = getattr(IMPORTED, _imported_property)
    if import_once and _is_imported:
        warnings.warn(f'{namespace} has already imported. If you want to re-imported, please set `import_once=False`',
                      ImportWarning)
        return {}

    try:
        modules = _get_modules(namespace)
    except ImportError as e:
        warnings.warn(f'{namespace} has no module to import. {e}', ImportWarning)
        return {}

    from collections import defaultdict
    load_stat = defaultdict(list)
    bad_imports = []

    depend_tree = {}
    _imported_cls_objs = []
    from importlib import import_module
    from .helper import colored
    for m in modules:
        try:
            mod = import_module(m)
            for _attr in dir(mod):
                _c = getattr(mod, _attr)
                # import the class
                if _c.__class__.__name__ != _import_type:
                    continue
                if _targets and _attr not in _targets:
                    continue
                try:
                    d = depend_tree
                    for vvv in _c.mro()[:-1][::-1]:
                        if vvv.__name__ not in d:
                            d[vvv.__name__] = {}
                        d = d[vvv.__name__]
                    d['module'] = m
                    # load the default request for this executor if possible
                    _load_default_config(_c)
                    if _attr in _targets:
                        _imported_cls_objs.append(_c)
                        _targets.remove(_attr)
                        if not _targets:
                            break
                            # return _c  # target execs are all found and loaded, return
                    load_stat[m].append(
                        (_attr, True, colored('▸', 'green').join(f'{vvv.__name__}' for vvv in _c.mro()[:-1][::-1])))
                except Exception as ex:
                    load_stat[m].append((_attr, False, ex))
                    bad_imports.append('.'.join([m, _attr]))
                    if _attr in _targets:
                        raise ex  # target class is found but not loaded, raise return
        except Exception as ex:
            load_stat[m].append(('', False, ex))
            bad_imports.append(m)
    if _targets:
        raise ImportError(f'{_targets} can not be found/load')

    if show_import_table:
        _print_load_table(load_stat)
    else:
        _raise_bad_imports_warnings(bad_imports, namespace)

    setattr(IMPORTED, _imported_property, True)

    if _return_cls_obj:
        return _imported_cls_objs
    else:
        return depend_tree


class ImportExtensions:
    """
    A context manager for wrapping extension import and fallback.
    It guides the user to pip install correct package by looking up
    extra-requirements.txt
    """

    def __init__(self, required: bool, logger=None,
                 help_text: str = None, pkg_name: str = None, verbose: bool = True):
        """

        :param required: set to True if you want to raise the ModuleNotFound error
        :param logger: when not given, built-in warnings.warn will be used
        :param help_text: the help text followed after
        :param pkg_name: the package name to find in extra_requirements.txt, when not given
                the ModuleNotFound exec_val will be used as the best guess
        """
        self._required = required
        self._tags = []
        self._help_text = help_text
        self._logger = logger
        self._pkg_name = pkg_name
        self._verbose = verbose

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        if exc_type == ModuleNotFoundError:
            missing_module = self._pkg_name or exc_val.name
            from pkg_resources import resource_filename
            with open(resource_filename('jina', '/'.join(('resources', 'extra-requirements.txt')))) as fp:
                for v in fp:
                    if (v.strip()
                            and not v.startswith('#')
                            and v.startswith(missing_module)
                            and ':' in v):
                        missing_module, install_tags = v.split(':')
                        self._tags.append(missing_module)
                        self._tags.extend(vv.strip() for vv in install_tags.split(','))
                        break

            if self._tags:
                req_msg = 'fallback to default behavior'
                if self._required:
                    req_msg = 'and it is required'
                err_msg = f'Module "{missing_module}" is not installed, {req_msg}. ' \
                          f'You are trying to use an extension feature not enabled by the ' \
                          'current installation.\n' \
                          'This feature is available in: '
                from .helper import colored
                err_msg += ' '.join(colored(f'[{tag}]', attrs='bold') for tag in self._tags)
                err_msg += f'\nUse {colored("pip install jina[TAG]", attrs="bold")} to enable it'

            else:
                err_msg = f'{exc_val.msg}'

            if self._required:
                if self._verbose:
                    if self._logger:
                        self._logger.critical(err_msg)
                        if self._help_text:
                            self._logger.error(self._help_text)
                    else:
                        warnings.warn(err_msg, RuntimeWarning, stacklevel=2)
                raise exc_val
            else:
                if self._verbose:
                    if self._logger:
                        self._logger.warning(err_msg)
                        if self._help_text:
                            self._logger.info(self._help_text)
                    else:
                        warnings.warn(err_msg, RuntimeWarning, stacklevel=2)
                return True  # suppress the error


def _load_contrib_module(logger=None) -> Optional[List[Any]]:
    if 'JINA_CONTRIB_MODULE_IS_LOADING' not in os.environ:

        contrib = os.getenv('JINA_CONTRIB_MODULE')
        os.environ['JINA_CONTRIB_MODULE_IS_LOADING'] = 'true'

        modules = []

        if contrib:
            pr = logger.info if logger else print
            pr(f'find a value in $JINA_CONTRIB_MODULE={contrib}, will load them as external modules')
            for p in contrib.split(','):
                m = PathImporter.add_modules(p)
                modules.append(m)
                pr(f'successfully registered {m} class, you can now use it via yaml.')
    else:
        modules = None

    return modules


class PathImporter:

    @staticmethod
    def _get_module_name(path: str, use_abspath: bool = False, use_basename: bool = True) -> str:
        module_name = os.path.dirname(os.path.abspath(path) if use_abspath else path)
        if use_basename:
            module_name = os.path.basename(module_name)
        module_name = module_name.replace('/', '.').strip('.')
        return module_name

    @staticmethod
    def add_modules(*paths) -> Optional[ModuleType]:
        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError(f'cannot import module from {p}, file not exist')
            module = PathImporter._path_import(p)
        return module

    @staticmethod
    def _path_import(absolute_path: str) -> Optional[ModuleType]:
        import importlib.util
        try:
            # module_name = (PathImporter._get_module_name(absolute_path) or
            #                PathImporter._get_module_name(absolute_path, use_abspath=True) or 'jinahub')

            # I dont want to trust user path based on directory structure, "jinahub", period
            spec = importlib.util.spec_from_file_location('jinahub', absolute_path)
            module = importlib.util.module_from_spec(spec)
            user_module_name = os.path.splitext(os.path.basename(absolute_path))[0]
            if user_module_name == '__init__':
                # __init__ can not be used as a module name
                spec_name = spec.name
            else:
                spec_name = f'{spec.name}.{user_module_name}'
            sys.modules[spec_name] = module
            spec.loader.exec_module(module)
        except Exception as ex:
            raise ImportError(f'can not import module from {absolute_path}') from ex
        return module


def _print_load_table(load_stat: Dict[str, List[Any]], logger=None):
    from .helper import colored

    load_table = []
    cached = set()

    for k, v in load_stat.items():
        for cls_name, import_stat, err_reason in v:
            if cls_name not in cached:
                load_table.append(
                    f'{colored("✓", "green") if import_stat else colored("✗", "red"):<5} {cls_name if cls_name else colored("Module load error", "red"):<25} {k:<40} {str(err_reason)}')
                cached.add(cls_name)
    if load_table:
        load_table.sort()
        load_table = ['', '%-5s %-25s %-40s %-s' % ('Load', 'Class', 'Module', 'Dependency'),
                      '%-5s %-25s %-40s %-s' % ('-' * 5, '-' * 25, '-' * 40, '-' * 10)] + load_table
        pr = logger.info if logger else print
        pr('\n'.join(load_table))


def _print_load_csv_table(load_stat: Dict[str, List[Any]], logger=None):
    from .helper import colored

    load_table = []
    for k, v in load_stat.items():
        for cls_name, import_stat, err_reason in v:
            load_table.append(
                f'{colored("✓", "green") if import_stat else colored("✗", "red")} {cls_name if cls_name else colored("Module_load_error", "red")} {k} {str(err_reason)}')
    if load_table:
        pr = logger.info if logger else print
        pr('\n'.join(load_table))


def _print_dep_tree_rst(fp, dep_tree, title='Executor'):
    tableview = set()
    treeview = []

    def _iter(d, depth):
        for k, v in d.items():
            if k != 'module':
                treeview.append('   ' * depth + f'- `{k}`')
                tableview.add(f'| `{k}` | ' + (f'`{d["module"]}`' if 'module' in d else ' ') + ' |')
                _iter(v, depth + 1)

    _iter(dep_tree, 0)

    fp.write(f'# List of {len(tableview)} {title}s in Jina\n\n'
             f'This version of Jina includes {len(tableview)} {title}s.\n\n'
             f'## Inheritances in a Tree View\n')
    fp.write('\n'.join(treeview))

    fp.write(f'\n\n## Modules in a Table View \n\n| Class | Module |\n')
    fp.write('| --- | --- |\n')
    fp.write('\n'.join(sorted(tableview)))
