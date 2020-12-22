import collections
import os
from typing import Union, TextIO, Dict

from yaml import MappingNode
from yaml.composer import Composer
from yaml.constructor import FullConstructor, ConstructorError
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner

from jina.importer import PathImporter


class JinaConstructor(FullConstructor):
    """Convert List into tuple when doing hashing"""

    def get_hashable_key(self, key):
        try:
            hash(key)
        except:
            if isinstance(key, list):
                for i in range(len(key)):
                    if not isinstance(key[i], collections.abc.Hashable):
                        key[i] = self.get_hashable_key(key[i])
                key = tuple(key)
                return key
            raise ValueError(f'unhashable key: {key}')
        return key

    def construct_mapping(self, node, deep=True):
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return self._construct_mapping(node, deep=deep)

    def _construct_mapping(self, node, deep=True):
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                                   'expected a mapping node, but found %s' % node.id,
                                   node.start_mark)
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=True)
            if not isinstance(key, collections.abc.Hashable):
                try:
                    key = self.get_hashable_key(key)
                except Exception as exc:
                    raise ConstructorError('while constructing a mapping', node.start_mark,
                                           'found unacceptable key (%s)' % exc, key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)

            mapping[key] = value
        return mapping


class JinaResolver(Resolver):
    """Remove `on|On|ON` as bool resolver"""
    pass


class JinaLoader(Reader, Scanner, Parser, Composer, JinaConstructor, JinaResolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        JinaConstructor.__init__(self)
        JinaResolver.__init__(self)


# remove on|On|ON resolver
JinaResolver.yaml_implicit_resolvers.pop('o')
JinaResolver.yaml_implicit_resolvers.pop('O')


def parse_config_source(path: Union[str, TextIO],
                        allow_stream: bool = True,
                        allow_yaml_file: bool = True,
                        allow_builtin_resource: bool = True,
                        allow_raw_yaml_content: bool = True,
                        allow_raw_driver_yaml_content: bool = True,
                        allow_class_type: bool = True, *args, **kwargs) -> TextIO:
    # priority, filepath > classname > default
    import io
    from pkg_resources import resource_filename
    if not path:
        raise FileNotFoundError
    elif allow_stream and hasattr(path, 'read'):
        # already a readable stream
        return path
    elif allow_yaml_file and (path.endswith('.yml') or path.endswith('.yaml')):
        return open(_complete_path(path), encoding='utf8')
    elif allow_builtin_resource and path.startswith('_') and os.path.exists(
            resource_filename('jina', '/'.join(('resources', f'executors.{path}.yml')))):
        return resource_filename('jina', '/'.join(('resources', f'executors.{path}.yml')))
    elif allow_raw_yaml_content and path.startswith('!'):
        # possible YAML content
        path = path.replace('|', '\n    with: ')
        return io.StringIO(path)
    elif allow_raw_driver_yaml_content and path.startswith('- !'):
        # possible driver YAML content, right now it is only used for debugging
        with open(resource_filename('jina', '/'.join(
                ('resources', 'executors.base.all.yml' if path.startswith('- !!') else 'executors.base.yml')))) as fp:
            _defaults = fp.read()
        path = path.replace('- !!', '- !').replace('|', '\n        with: ')  # for indent, I know, its nasty
        path = _defaults.replace('*', path)
        return io.StringIO(path)
    elif allow_class_type and path.isidentifier():
        # possible class name
        return io.StringIO(f'!{path}')
    else:
        raise FileNotFoundError(f'{path} can not be resolved, it should be a readable stream,'
                                ' or a valid file path, or a supported class name.')


def _complete_path(path: str) -> str:
    _p = None
    if os.path.exists(path):
        # this checks both abs and relative paths already
        _p = path
    else:
        _p = _search_file_in_paths(path)
    if _p:
        return _p
    else:
        raise FileNotFoundError(f'can not find {path}')


def _search_file_in_paths(path):
    """searches in all dirs of the PATH environment variable and all dirs of files used in the call stack.
    """
    import inspect
    search_paths = []
    frame = inspect.currentframe()

    # iterates over the call stack
    while frame:
        search_paths.append(os.path.dirname(inspect.getfile(frame)))
        frame = frame.f_back
    search_paths += os.environ['PATH'].split(os.pathsep)

    # return first occurrence of path. If it does not exist, return None.
    for p in search_paths:
        _p = os.path.join(p, path)
        if os.path.exists(_p):
            return _p


def _load_py_modules(d: Dict) -> None:
    """Find 'py_modules' in the dict recursively and then load them """
    mod = []

    def _finditem(obj, key='py_modules'):
        if key in obj:
            if isinstance(key, str):
                mod.append(obj[key])
            elif isinstance(key, list) or isinstance(key, tuple):
                mod.extend(obj[key])
        for k, v in obj.items():
            if isinstance(v, dict):
                _finditem(v, key)

    _finditem(d)
    mod = [_complete_path(m) for m in mod]
    PathImporter.add_modules(*mod)
