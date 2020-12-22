import os
import re
from types import SimpleNamespace
from typing import Dict, Any

import yaml

from .helper import JinaResolver, JinaLoader

__all__ = ['JAML', 'JAMLCompatible']


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
        from ..helper import parse_arg
        expand_map = SimpleNamespace()
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


class JAMLCompatibleType(type):
    """Metaclass for :class:`JAMLCompatible`.
    It enables any class inherit from :class:`JAMLCompatible` to auto-register itself at :class:`JAML`"""

    def __new__(cls, *args, **kwargs):
        _cls = super().__new__(cls, *args, **kwargs)
        JAML.register(_cls)
        return _cls


class JAMLCompatible(metaclass=JAMLCompatibleType):
    """:class:`JAMLCompatible` is a mixin class designed to be used with multiple inheritance.
    It will add :meth:`to_yaml` and :meth:`from_yaml` to the target class,
    making that class JAML-friendly.

    .. warning::
        For the sake of cooperative multiple inheritance, do NOT implement :meth:`__init__` for this class
    """

    _version = ''  #: YAML version number, this will be later overridden if YAML config says the other way

    @classmethod
    def to_yaml(cls, representer, data):
        """Required by :mod:`pyyaml` write interface """
        from .parsers import get_parser
        tmp = get_parser(cls, version=data._version).dump(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def from_yaml(cls, constructor, node):
        """Required by :mod:`pyyaml` load interface """
        data = constructor.construct_mapping(node, deep=True)
        from .parsers import get_parser
        return get_parser(cls, version=data.get('version', None)).parse(cls, data)
