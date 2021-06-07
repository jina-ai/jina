import os
import sys
import warnings
from types import SimpleNamespace, ModuleType
from typing import Optional, List, Any, Dict

from . import __resources_path__

IMPORTED = SimpleNamespace()
IMPORTED.executors = False
IMPORTED.executors = False
IMPORTED.hub = False
IMPORTED.schema_executors = {}


class ImportExtensions:
    """
    A context manager for wrapping extension import and fallback. It guides the user to pip install correct package by looking up extra-requirements.txt.

    :param required: set to True if you want to raise the ModuleNotFound error
    :param logger: when not given, built-in warnings.warn will be used
    :param help_text: the help text followed after
    :param pkg_name: the package name to find in extra_requirements.txt, when not given the ModuleNotFound exec_val will be used as the best guess
    """

    def __init__(
        self,
        required: bool,
        logger=None,
        help_text: Optional[str] = None,
        pkg_name: Optional[str] = None,
        verbose: bool = True,
    ):
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
            with open(os.path.join(__resources_path__, 'extra-requirements.txt')) as fp:
                for v in fp:
                    if (
                        v.strip()
                        and not v.startswith('#')
                        and v.startswith(missing_module)
                        and ':' in v
                    ):
                        missing_module, install_tags = v.split(':')
                        self._tags.append(missing_module)
                        self._tags.extend(vv.strip() for vv in install_tags.split(','))
                        break

            if self._tags:
                req_msg = 'fallback to default behavior'
                if self._required:
                    req_msg = 'and it is required'
                err_msg = (
                    f'Module "{missing_module}" is not installed, {req_msg}. '
                    f'You are trying to use an extension feature not enabled by the '
                    'current installation.\n'
                    'This feature is available in: '
                )
                from .helper import colored

                err_msg += ' '.join(
                    colored(f'[{tag}]', attrs='bold') for tag in self._tags
                )
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


class PathImporter:
    """The class to import modules from paths."""

    @staticmethod
    def add_modules(*paths) -> Optional[ModuleType]:
        """
        Import modules from paths.

        :param paths: Paths of the modules.
        :return: The target module.
        """
        from .jaml.helper import complete_path

        paths = [complete_path(m) for m in paths]

        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError(
                    f'cannot import module from {p}, file not exist'
                )
            module = PathImporter._path_import(p)
        return module

    @staticmethod
    def _path_import(absolute_path: str) -> Optional[ModuleType]:
        import importlib.util

        try:
            # I dont want to trust user path based on directory structure, "jinahub", period
            spec = importlib.util.spec_from_file_location('jinahub', absolute_path)
            module = importlib.util.module_from_spec(spec)
            user_module_name = os.path.splitext(os.path.basename(absolute_path))[0]
            if user_module_name == '__init__':
                # __init__ can not be used as a module name
                spec_name = spec.name
            elif user_module_name not in sys.modules:
                spec_name = user_module_name
            else:
                warnings.warn(
                    f'''
                {user_module_name} shadows one of built-in Python module name.
                It is imported as `jinahub.{user_module_name}`
                
                Affects:
                - Either, change your code from using `from {user_module_name} import ...` to `from jinahub.{user_module_name} import ...`
                - Or, rename {user_module_name} to another name
                '''
                )
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
                    f'{colored("✓", "green") if import_stat else colored("✗", "red"):<5} {cls_name if cls_name else colored("Module load error", "red"):<25} {k:<40} {str(err_reason)}'
                )
                cached.add(cls_name)
    if load_table:
        load_table.sort()
        load_table = [
            '',
            '%-5s %-25s %-40s %-s' % ('Load', 'Class', 'Module', 'Dependency'),
            '%-5s %-25s %-40s %-s' % ('-' * 5, '-' * 25, '-' * 40, '-' * 10),
        ] + load_table
        pr = logger.info if logger else print
        pr('\n'.join(load_table))


def _print_dep_tree_rst(fp, dep_tree, title='Executor'):
    tableview = set()
    treeview = []

    def _iter(d, depth):
        for k, v in d.items():
            if k != 'module':
                treeview.append('   ' * depth + f'- `{k}`')
                tableview.add(
                    f'| `{k}` | '
                    + (f'`{d["module"]}`' if 'module' in d else ' ')
                    + ' |'
                )
                _iter(v, depth + 1)

    _iter(dep_tree, 0)

    fp.write(
        f'# List of {len(tableview)} {title}s in Jina\n\n'
        f'This version of Jina includes {len(tableview)} {title}s.\n\n'
        f'## Inheritances in a Tree View\n'
    )
    fp.write('\n'.join(treeview))

    fp.write(f'\n\n## Modules in a Table View \n\n| Class | Module |\n')
    fp.write('| --- | --- |\n')
    fp.write('\n'.join(sorted(tableview)))


def _raise_bad_imports_warnings(bad_imports, namespace):
    if not bad_imports:
        return
    if namespace != 'jina.hub':
        warnings.warn(
            f'theses modules or classes can not be imported {bad_imports}. '
            f'You can use `jina check` to list all executors'
        )
    else:
        warnings.warn(
            f'due to the missing dependencies or bad implementations, '
            f'{bad_imports} can not be imported '
            f'if you are using these executors, they wont work. '
            f'You can use `jina check` to list all executors'
        )


def _get_modules(namespace):
    from setuptools import find_packages
    from pkgutil import get_loader

    try:
        _path = os.path.dirname(get_loader(namespace).path)
    except AttributeError as ex:
        if namespace == 'jina.hub':
            warnings.warn(
                f'hub submodule is not initialized. Please try "git submodule update --init"',
                ImportWarning,
            )
        raise ImportError(f'{namespace} can not be imported. {ex}')

    _modules = _get_submodules(_path, namespace)

    for _pkg in find_packages(_path):
        _modules.add('.'.join([namespace, _pkg]))
        _pkgpath = os.path.join(_path, _pkg.replace('.', '/'))
        _modules |= _get_submodules(_pkgpath, namespace, prefix=_pkg)

    return _filter_modules(_modules)


def _get_submodules(path, namespace, prefix=None):
    from pkgutil import iter_modules

    _prefix = '.'.join([namespace, prefix]) if prefix else namespace
    modules = set()
    for _info in iter_modules([path]):
        _is_hub_module = namespace == 'jina.hub' and _info.ispkg
        _is_nonhub_module = namespace != 'jina.hub' and not _info.ispkg
        module_name = '.'.join([_prefix, _info.name])
        if _is_hub_module or _is_nonhub_module:
            modules.add(module_name)
    return modules


def _filter_modules(modules):
    import re

    _ignored_module_pattern = re.compile(r'\.tests|\.api|\.bump_version')
    return {m for m in modules if not _ignored_module_pattern.findall(m)}


def _update_depend_tree(cls_obj, module_name, cur_tree):
    d = cur_tree
    for vvv in cls_obj.mro()[:-1][::-1]:
        if vvv.__name__ not in d:
            d[vvv.__name__] = {}
        d = d[vvv.__name__]
    d['module'] = module_name
