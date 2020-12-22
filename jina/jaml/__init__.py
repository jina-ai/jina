import os
import re
import tempfile
import warnings
from types import SimpleNamespace
from typing import Dict, Any, Union, TextIO, Optional

import yaml

from .helper import JinaResolver, JinaLoader, parse_config_source, load_py_modules

__all__ = ['JAML', 'JAMLCompatible']

from ..excepts import BadConfigSource

subvar_regex = re.compile(r'\${{\s*([\w\[\].]+)\s*}}')  #: regex for substituting variables


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
                        if isinstance(v, str) and subvar_regex.findall(v):
                            sub_d[k] = _sub(v, p)
            elif isinstance(sub_d, list):
                for idx, v in enumerate(sub_d):
                    if isinstance(v, dict) or isinstance(v, list):
                        _replace(v, p[idx])
                    else:
                        if isinstance(v, str) and subvar_regex.findall(v):
                            sub_d[idx] = _sub(v, p)

        def _sub(v, p):
            v = re.sub(subvar_regex, '{\\1}', v)

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
        return yaml.dump(data, stream=stream, default_flow_style=False, sort_keys=False, **kwargs)

    @staticmethod
    def register(cls):
        """register a class for dumping loading
            - if it has attribute yaml_tag use that to register, else use class name
            - if it has methods to_yaml/from_yaml use those to dump/load else dump attributes
              as mapping
        """

        tag = getattr(cls, 'yaml_tag', '!' + cls.__name__)

        try:
            yaml.add_representer(cls, cls._to_yaml)
        except AttributeError:
            def t_y(representer, data):
                return representer.represent_yaml_object(
                    tag, data, cls, flow_style=representer.default_flow_style
                )

            yaml.add_representer(cls, t_y)
        try:
            yaml.add_constructor(tag, cls._from_yaml, JinaLoader)
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
    def _to_yaml(cls, representer, data):
        """A low-level interface required by :mod:`pyyaml` write interface

        .. warning::
            This function should not be used directly, please use :meth:`save_config`.

        """
        from .parsers import get_parser
        tmp = get_parser(cls, version=data._version).dump(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def _from_yaml(cls, constructor, node):
        """A low-level interface required by :mod:`pyyaml` load interface

        .. warning::
            This function should not be used directly, please use :meth:`load_config`.

        """
        data = constructor.construct_mapping(node, deep=True)
        from .parsers import get_parser
        return get_parser(cls, version=data.get('version', None)).parse(cls, data)

    def save_config(self, filename: Optional[str] = None):
        """Save the object's config into a YAML file

        :param filename: file path of the yaml file, if not given then :attr:`config_abspath` is used
        :return: successfully dumped or not
        """
        f = filename or getattr(self, 'config_abspath', None)
        if not f:
            f = tempfile.NamedTemporaryFile('w', delete=False, dir=os.environ.get('JINA_EXECUTOR_WORKDIR', None)).name
            warnings.warn(f'no "filename" is given, {self!r}\'s config will be saved to: {f}')
        with open(f, 'w', encoding='utf8') as fp:
            JAML.dump(self, fp)

    @classmethod
    def load_config(cls,
                    source: Union[str, TextIO], *,
                    allow_py_modules: bool = True,
                    substitute: bool = True,
                    context: Dict[str, Any] = None,
                    **kwargs) -> 'JAMLCompatible':
        """A high-level interface for loading configuration with features
        of loading extra py_modules, substitute env & context variables.

        :param source: the source of the configs (multi-kind)
        :param allow_py_modules: allow importing plugins specified by ``py_modules`` in YAML at any levels
        :param substitute: substitute environment, internal reference and context variables.
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :return: :class:`JAMLCompatible` object


        .. highlight:: python
        .. code-block:: python

            # load Executor from yaml file
            BaseExecutor.load_config('a.yml')

        """
        with parse_config_source(source, **kwargs) as fp:
            # first load yml with no tag
            no_tag_yml = JAML.load_no_tags(fp)
            if no_tag_yml:
                # extra arguments are parsed to inject_config
                no_tag_yml = cls.inject_config(no_tag_yml, **kwargs)
            else:
                raise BadConfigSource(f'can not construct {cls} from an empty {source}. nothing to read from there')

            if allow_py_modules:
                # also add YAML parent path to the search paths
                load_py_modules(no_tag_yml, extra_search_paths=(os.path.dirname(str(source)),))

            # revert yaml's tag and load again, this time with substitution
            revert_tag_yml = JAML.dump(no_tag_yml).replace('__tag: ', '!')
            return JAML.load(revert_tag_yml, substitute=substitute, context=context)

    @classmethod
    def inject_config(cls, raw_config: Dict, *args, **kwargs) -> Dict:
        """Inject/modify the config before loading it into an object.

        :param raw_config: raw config to work on


         .. note::
            This function is most likely to be overridden by its subclass.

        """
        return raw_config
