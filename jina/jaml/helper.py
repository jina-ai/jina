import collections

from yaml import MappingNode
from yaml.composer import Composer
from yaml.constructor import FullConstructor, ConstructorError
from yaml.parser import Parser
from yaml.reader import Reader
from yaml.resolver import Resolver
from yaml.scanner import Scanner


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
