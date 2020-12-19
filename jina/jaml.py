import collections

import yaml
from yaml import MappingNode
from yaml.composer import Composer
from yaml.constructor import ConstructorError, FullConstructor
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner

__all__ = ['JAML']


class JAML:
    """A Jina style YAML loader and dumper, a wrapper on PyYAML.

    To use it:

    .. highlight:: python
    .. code-block:: python

        from jina.jaml import JAML

        JAML.load(...)
        JAML.dump(...)

        class DummyClass:
            pass

        JAML.register(DummyClass)
    """

    @staticmethod
    def load(stream, substitute: bool = False):
        """Parse the first YAML document in a stream
            and produce the corresponding Python object.
        """
        r = yaml.load(stream, Loader=JinaLoader)
        if substitute:
            from .helper import expand_dict
            r = expand_dict(r)
        return r

    @staticmethod
    def dump(data, stream=None, **kwargs):
        """
        Serialize a Python object into a YAML stream.
        If stream is None, return the produced string instead.
        """
        return yaml.dump(data, stream=stream, default_flow_style=False, **kwargs)

    @staticmethod
    def register(cls):
        """register a class for dumping loading
            - if it has attribute yaml_tag use that to register, else use class name
            - if it has methods to_yaml/from_yaml use those to dump/load else dump attributes
              as mapping
        """

        tag = getattr(cls, 'yaml_tag', '!' + cls.__name__)

        try:
            yaml.add_representer(cls, cls.to_yaml)
        except AttributeError:
            def t_y(representer, data):
                return representer.represent_yaml_object(
                    tag, data, cls, flow_style=representer.default_flow_style
                )

            yaml.add_representer(cls, t_y)
        try:
            yaml.add_constructor(tag, cls.from_yaml, JinaLoader)
        except AttributeError:

            def f_y(constructor, node):
                return constructor.construct_yaml_object(node, cls)

            yaml.add_constructor(tag, f_y, JinaLoader)
        return cls


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


# remove on|On|ON resolver
JinaResolver.yaml_implicit_resolvers.pop('o')
JinaResolver.yaml_implicit_resolvers.pop('O')


class JinaLoader(Reader, Scanner, Parser, Composer, JinaConstructor, JinaResolver):
    def __init__(self, stream):
        Reader.__init__(self, stream)
        Scanner.__init__(self)
        Parser.__init__(self)
        Composer.__init__(self)
        JinaConstructor.__init__(self)
        JinaResolver.__init__(self)
