import collections
import json
import os
import warnings
from typing import Union, TextIO, Dict, Tuple, Optional, List

from yaml import MappingNode
from yaml.composer import Composer
from yaml.constructor import FullConstructor, ConstructorError
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner

from jina.excepts import BadConfigSource
from jina.helper import is_yaml_filepath
from jina.importer import PathImporter


class JinaConstructor(FullConstructor):
    """Convert List into tuple when doing hashing."""

    def get_hashable_key(self, key):
        """
        Get the hash value of key.

        :param key: key value to be hashed.
        :return: Hash value of key.
        """
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
        """
        Build the mapping from node.

        :param node: the node to traverse
        :param deep: required param from YAML constructor
        :return: Mapped data
        """
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        return self._construct_mapping(node, deep=deep)

    def _construct_mapping(self, node, deep=True):
        if not isinstance(node, MappingNode):
            raise ConstructorError(
                None,
                None,
                'expected a mapping node, but found %s' % node.id,
                node.start_mark,
            )
        mapping = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=True)
            if not isinstance(key, collections.abc.Hashable):
                try:
                    key = self.get_hashable_key(key)
                except Exception as exc:
                    raise ConstructorError(
                        'while constructing a mapping',
                        node.start_mark,
                        'found unacceptable key (%s)' % exc,
                        key_node.start_mark,
                    )
            value = self.construct_object(value_node, deep=deep)

            mapping[key] = value
        return mapping


class JinaResolver(Resolver):
    """Remove `on|On|ON` as bool resolver."""

    pass


class JinaLoader(Reader, Scanner, Parser, Composer, JinaConstructor, JinaResolver):
    """
    The Jina loader which should be able to load YAML safely.

    :param stream: the stream to load.
    """

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


def parse_config_source(
    path: Union[str, TextIO, Dict],
    allow_stream: bool = True,
    allow_yaml_file: bool = True,
    allow_raw_yaml_content: bool = True,
    allow_class_type: bool = True,
    allow_dict: bool = True,
    allow_json: bool = True,
    extra_search_paths: Optional[List[str]] = None,
    *args,
    **kwargs,
) -> Tuple[TextIO, Optional[str]]:
    """
    Check if the text or text stream is valid.

    .. # noqa: DAR401
    :param path: the multi-kind source of the configs.
    :param allow_stream: flag
    :param allow_yaml_file: flag
    :param allow_raw_yaml_content: flag
    :param allow_class_type: flag
    :param allow_dict: flag
    :param allow_json: flag
    :param extra_search_paths: extra paths to search for
    :param args: unused
    :param kwargs: unused
    :return: a tuple, the first element is the text stream, the second element is the file path associate to it
            if available.
    """
    import io

    if not path:
        raise BadConfigSource
    elif allow_dict and isinstance(path, dict):
        from jina.jaml import JAML

        tmp = JAML.dump(path)
        return io.StringIO(tmp), None
    elif allow_stream and hasattr(path, 'read'):
        # already a readable stream
        return path, None
    elif allow_yaml_file and is_yaml_filepath(path):
        comp_path = complete_path(path, extra_search_paths)
        return open(comp_path, encoding='utf8'), comp_path
    elif allow_raw_yaml_content and path.lstrip().startswith(('!', 'jtype')):
        # possible YAML content
        path = path.replace('|', '\n    with: ')
        return io.StringIO(path), None
    elif allow_class_type and path.isidentifier():
        # possible class name
        return io.StringIO(f'!{path}'), None
    elif allow_json and isinstance(path, str):
        try:
            from jina.jaml import JAML

            tmp = json.loads(path)
            tmp = JAML.dump(tmp)
            return io.StringIO(tmp), None
        except json.JSONDecodeError:
            raise BadConfigSource(path)
    else:
        raise BadConfigSource(
            f'{path} can not be resolved, it should be a readable stream,'
            ' or a valid file path, or a supported class name.'
        )


def complete_path(path: str, extra_search_paths: Optional[List[str]] = None) -> str:
    """
    Complete the path of file via searching in abs and relative paths.

    :param path: path of file.
    :param extra_search_paths: extra paths to conduct search
    :return: Completed file path.
    """
    _p = _search_file_in_paths(path, extra_search_paths)
    if _p is None and os.path.exists(path):
        # this checks both abs and relative paths already
        _p = path
    if _p:
        return os.path.abspath(_p)
    else:
        raise FileNotFoundError(f'can not find {path}')


def _search_file_in_paths(path, extra_search_paths: Optional[List[str]] = None):
    """
    Search in all dirs of the PATH environment variable and all dirs of files used in the call stack.

    :param path: the path to search for
    :param extra_search_paths: any extra locations to search for
    :return: the path (if found)
    """
    import inspect

    search_paths = []
    if extra_search_paths:
        search_paths.extend((v for v in extra_search_paths))

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


def load_py_modules(d: Dict, extra_search_paths: Optional[List[str]] = None) -> None:
    """
    Find 'py_modules' in the dict recursively and then load them.

    :param d: the dictionary to traverse
    :param extra_search_paths: any extra paths to search
    """
    mod = []

    def _finditem(obj, key='py_modules'):
        value = obj.get(key, [])
        if isinstance(value, str):
            mod.append(value)
        elif isinstance(value, (list, tuple)):
            mod.extend(value)
        for k, v in obj.items():
            if isinstance(v, dict):
                _finditem(v, key)

    _finditem(d)
    if mod:
        if len(mod) > 1:
            warnings.warn(
                'It looks like you are trying to import multiple python modules using'
                ' `py_modules`. When using multiple python files to define an executor,'
                ' the recommended practice is to structure the files in a python'
                ' package, and only import the `__init__.py` file of that package.'
                ' For more details, please check out the cookbook: '
                'https://docs.jina.ai/fundamentals/executor/repository-structure/'
            )

        mod = [complete_path(m, extra_search_paths) for m in mod]
        PathImporter.add_modules(*mod)
