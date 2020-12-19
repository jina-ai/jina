import collections
import os
import re
from types import SimpleNamespace
from typing import Dict, Any

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

    You can use expressions to programmatically set variables in YAML files and access contexts.
    An expression can be any combination of literal values, references to a context, or functions.
    You can combine literals, context references, and functions using operators.

    You need to use specific syntax to tell Jina to evaluate an expression rather than treat it as a string.

    .. highlight:: yaml
    .. code-block:: yaml

        ${{ <expression> }}

    To evaluate (i.e. substitute the value to the real value) the expression when loading, use :meth:`load(substitute=True)`.

    To substitute the value based on a dict,

    .. highlight:: python
    .. code-block:: python

        obk = JAML.load(fp, substitute=True,
                              context={'context_var': 3.14,
                                       'context_var2': 'hello-world'})
    """

    @staticmethod
    def load(stream,
             substitute: bool = False,
             context: Dict[str, Any] = None):
        """Parse the first YAML document in a stream and produce the corresponding Python object.

        :param substitute: substitute environment, internal reference and context variables.
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        """
        r = yaml.load(stream, Loader=JinaLoader)
        if substitute:
            r = JAML.expand_dict(r, context)
        return r

    @staticmethod
    def load_no_tags(stream, **kwargs):
        """Load yaml object but ignore all customized tags, e.g. !Executor, !Driver, !Flow
        """
        safe_yml = '\n'.join(v if not re.match(r'^[\s-]*?!\b', v) else v.replace('!', '__tag: ') for v in stream)
        return JAML.load(safe_yml, **kwargs)

    @staticmethod
    def expand_dict(d: Dict, context: Dict = None, resolve_cycle_ref=True) -> Dict[str, Any]:
        from .helper import parse_arg
        expand_map = SimpleNamespace()
        context_map = SimpleNamespace()
        env_map = SimpleNamespace()
        pat = re.compile(r'\${{\s*([\w\[\].]+)\s*}}')

        def _scan(sub_d, p):
            if isinstance(sub_d, dict):
                for k, v in sub_d.items():
                    if isinstance(v, dict):
                        p.__dict__[k] = SimpleNamespace()
                        _scan(v, p.__dict__[k])
                    elif isinstance(v, list):
                        p.__dict__[k] = list()
                        _scan(v, p.__dict__[k])
                    else:
                        p.__dict__[k] = v
            elif isinstance(sub_d, list):
                for idx, v in enumerate(sub_d):
                    if isinstance(v, dict):
                        p.append(SimpleNamespace())
                        _scan(v, p[idx])
                    elif isinstance(v, list):
                        p.append(list())
                        _scan(v, p[idx])
                    else:
                        p.append(v)

        def _replace(sub_d, p):
            if isinstance(sub_d, dict):
                for k, v in sub_d.items():
                    if isinstance(v, dict) or isinstance(v, list):
                        _replace(v, p.__dict__[k])
                    else:
                        if isinstance(v, str) and pat.findall(v):
                            sub_d[k] = _sub(v, p)
            elif isinstance(sub_d, list):
                for idx, v in enumerate(sub_d):
                    if isinstance(v, dict) or isinstance(v, list):
                        _replace(v, p[idx])
                    else:
                        if isinstance(v, str) and pat.findall(v):
                            sub_d[idx] = _sub(v, p)

        def _sub(v, p):
            v = re.sub(pat, '{\\1}', v)

            if resolve_cycle_ref:
                try:
                    # "root" context is now the global namespace
                    # "this" context is now the current node namespace
                    v = v.format(root=expand_map, this=p, ENV=env_map)
                except KeyError:
                    pass
                try:
                    v = v.format_map(context)
                except KeyError:
                    pass
            if isinstance(v, str):
                v = parse_arg(v)
            return v

        _scan(d, expand_map)
        _scan(dict(os.environ), env_map)

        _replace(d, expand_map)
        return d

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
