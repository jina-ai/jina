import os
import re
import tempfile
import warnings
from types import SimpleNamespace
from typing import Dict, Any, Union, TextIO, Optional, List, Tuple

import yaml
from yaml.constructor import FullConstructor

from .helper import JinaResolver, JinaLoader, parse_config_source, load_py_modules

__all__ = ['JAML', 'JAMLCompatible']

from ..excepts import BadConfigSource
from ..helper import expand_env_var

subvar_regex = re.compile(
    r'\${{\s*([\w\[\].]+)\s*}}'
)  #: regex for substituting variables
internal_var_regex = re.compile(r'{.+}|\$[a-zA-Z0-9_]*\b')


class JAML:
    """A Jina YAML parser supports loading and dumping and substituting variables.

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

    To evaluate (i.e. substitute the value to the real value)
    the expression when loading, use :meth:`load(substitute=True)`.

    To substitute the value based on a dict,

    .. highlight:: python
    .. code-block:: python

        obj = JAML.load(fp, substitute=True,
                            context={'context_var': 3.14,
                                    'context_var2': 'hello-world'})

    .. note::
        :class:`BaseFlow`, :class:`BaseExecutor`, :class:`BaseDriver`
        and all their subclasses have already implemented JAML interfaces,
        to load YAML config into objects, please use :meth:`Flow.load_config`,
        :meth:`BaseExecutor.load_config`, etc.

    """

    @staticmethod
    def load(stream, substitute: bool = False, context: Dict[str, Any] = None):
        """Parse the first YAML document in a stream and produce the corresponding Python object.

        .. note::
            :class:`BaseFlow`, :class:`BaseExecutor`, :class:`BaseDriver`
            and all their subclasses have already implemented JAML interfaces,
            to load YAML config into objects, please use :meth:`Flow.load_config`,
            :meth:`BaseExecutor.load_config`, etc.

        :param substitute: substitute environment, internal reference and context variables.
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :param stream: the stream to load
        :return: the Python object

        """
        r = yaml.load(stream, Loader=JinaLoader)
        if substitute:
            r = JAML.expand_dict(r, context)
        return r

    @staticmethod
    def escape(value: str, include_unknown_tags: bool = True) -> str:
        """
        Escape the YAML content by replacing all customized tags ``!`` to ``jtype: ``.

        :param value: the original YAML content
        :param include_unknown_tags: if to include unknown tags during escaping
        :return: escaped YAML
        """
        if include_unknown_tags:
            r = r'!(\w+)\b'
        else:
            r = '|'.join(JAML.registered_tags())
            r = rf'!({r})\b'
        return re.sub(r, r'jtype: \1', value)

    @staticmethod
    def unescape(
        value: str,
        include_unknown_tags: bool = True,
        jtype_whitelist: Tuple[str, ...] = None,
    ) -> str:
        """
        Unescape the YAML content by replacing all ``jtype: `` to tags.

        :param value: the escaped YAML content
        :param include_unknown_tags: if to include unknown tags during unescaping
        :param jtype_whitelist: the list of jtype to be unescaped
        :return: unescaped YAML
        """
        if include_unknown_tags:
            r = r'jtype: (\w+)\b'
        elif jtype_whitelist:
            r = '|'.join(jtype_whitelist)
            r = rf'jtype: ({r})\b'
        else:
            r = '|'.join(JAML.registered_tags())
            r = rf'jtype: ({r})\b'
        return re.sub(r, r'!\1', value)

    @staticmethod
    def registered_tags() -> List[str]:
        """
        Return a list of :class:`JAMLCompatible` classes that have been registered.

        :return: tags
        """
        return list(
            v[1:]
            for v in set(JinaLoader.yaml_constructors.keys())
            if v and v.startswith('!')
        )

    @staticmethod
    def load_no_tags(stream, **kwargs):
        """
        Load yaml object but ignore all customized tags, e.g. !Executor, !Driver, !Flow.

        :param stream: the output stream
        :param kwargs: other kwargs
        :return: the Python object
        """
        safe_yml = JAML.escape('\n'.join(v for v in stream))
        return JAML.load(safe_yml, **kwargs)

    @staticmethod
    def expand_dict(
        d: Dict,
        context: Optional[Union[Dict, SimpleNamespace]] = None,
        resolve_cycle_ref=True,
        resolve_passes: int = 3,
    ) -> Dict[str, Any]:
        """
        Expand variables from YAML file.

        :param d: yaml file loaded as python dict
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :param resolve_cycle_ref: resolve internal reference if True.
        :param resolve_passes: number of rounds to resolve internal reference.
        :return: expanded dict.
        """
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

        def _replace(sub_d, p, resolve_ref=False):
            if isinstance(sub_d, dict):
                for k, v in sub_d.items():
                    if isinstance(v, (dict, list)):
                        _replace(v, p.__dict__[k], resolve_ref)
                    else:
                        if isinstance(v, str):
                            if resolve_ref and internal_var_regex.findall(v):
                                sub_d[k] = _resolve(v, p)
                            else:
                                sub_d[k] = _sub(v)
            elif isinstance(sub_d, list):
                for idx, v in enumerate(sub_d):
                    if isinstance(v, (dict, list)):
                        _replace(v, p[idx], resolve_ref)
                    else:
                        if isinstance(v, str):
                            if resolve_ref and internal_var_regex.findall(v):
                                sub_d[idx] = _resolve(v, p)
                            else:
                                sub_d[idx] = _sub(v)

        def _sub(v):
            org_v = v
            v = expand_env_var(v)
            if not (isinstance(v, str) and subvar_regex.findall(v)):
                return v

            # 0. replace ${{var}} to {var} to use .format
            v = re.sub(subvar_regex, '{\\1}', v)

            # 1. substitute the envs (new syntax: ${{ENV.VAR_NAME}})
            try:
                v = v.format(ENV=env_map)
            except KeyError:
                pass

            # 2. substitute the envs (old syntax: $VAR_NAME)
            if os.environ:
                try:
                    v = v.format_map(dict(os.environ))
                except KeyError:
                    pass

            # 3. substitute the context dict
            if context:
                try:
                    if isinstance(context, dict):
                        v = v.format_map(context)
                    elif isinstance(context, SimpleNamespace):
                        v = v.format(root=context, this=context)
                except (KeyError, AttributeError):
                    pass

            # 4. make string to float/int/list/bool with best effort
            v = parse_arg(v)

            if isinstance(v, str) and internal_var_regex.findall(v):
                # replacement failed, revert back to before
                v = org_v

            return v

        def _resolve(v, p):
            # resolve internal reference
            org_v = v
            v = re.sub(subvar_regex, '{\\1}', v)
            try:
                # "root" context is now the global namespace
                # "this" context is now the current node namespace
                v = v.format(root=expand_map, this=p, ENV=env_map)
            except AttributeError as ex:
                raise AttributeError(
                    'variable replacement is failed, please check your YAML file.'
                ) from ex
            except KeyError:
                pass

            v = parse_arg(v)

            if isinstance(v, str) and internal_var_regex.findall(v):
                # replacement failed, revert back to before
                v = org_v

            return v

        _scan(d, expand_map)
        _scan(dict(os.environ), env_map)
        # first do var replacement
        _replace(d, expand_map)

        # do three rounds of scan-replace to resolve internal references
        for _ in range(resolve_passes):
            # rebuild expand_map
            expand_map = SimpleNamespace()
            _scan(d, expand_map)

            # resolve internal reference
            if resolve_cycle_ref:
                _replace(d, expand_map, resolve_ref=True)

        return d

    @staticmethod
    def dump(data, stream=None, **kwargs):
        """
        Serialize a Python object into a YAML stream.

        If stream is None, return the produced string instead.

        :param data: the data to serialize
        :param stream: the output stream
        :param kwargs: other kwargs
        :return: the yaml output
        """
        return yaml.dump(
            data, stream=stream, default_flow_style=False, sort_keys=False, **kwargs
        )

    @staticmethod
    def register(cls):
        """
        Register a class for dumping loading.

            - if it has attribute yaml_tag use that to register, else use class name
            - if it has methods to_yaml/from_yaml use those to dump/load else dump attributes
              as mapping

        :param cls: the class to register
        :return: the registered class
        """
        tag = getattr(cls, 'yaml_tag', '!' + cls.__name__)

        try:
            yaml.add_representer(cls, cls._to_yaml)
        except AttributeError:

            def t_y(representer, data):
                """
                Wrapper function for the representer.

                :param representer: yaml representer
                :param data: state of the representer
                :return: node
                """
                return representer.represent_yaml_object(
                    tag, data, cls, flow_style=representer.default_flow_style
                )

            yaml.add_representer(cls, t_y)
        try:
            yaml.add_constructor(tag, cls._from_yaml, JinaLoader)
        except AttributeError:

            def f_y(constructor, node):
                """
                Wrapper function for the constructor.

                :param constructor: yaml constructor
                :param node: to be added
                :return: generator
                """
                return constructor.construct_yaml_object(node, cls)

            yaml.add_constructor(tag, f_y, JinaLoader)
        return cls


class JAMLCompatibleType(type):
    """
    Metaclass for :class:`JAMLCompatible`.

    It enables any class inherit from :class:`JAMLCompatible` to auto-register itself at :class:`JAML`
    """

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
        """
        A low-level interface required by :mod:`pyyaml` write interface.

        .. warning::
            This function should not be used directly, please use :meth:`save_config`.

        :param representer: the class that will serialize
        :param data: the data to serialize
        :return: the node's representation
        """
        from .parsers import get_parser

        tmp = get_parser(cls, version=data._version).dump(data)
        return representer.represent_mapping('!' + cls.__name__, tmp)

    @classmethod
    def _from_yaml(cls, constructor: FullConstructor, node):
        """A low-level interface required by :mod:`pyyaml` load interface.

        .. warning::
            This function should not be used directly, please use :meth:`load_config`.

        :param constructor: the class that will construct
        :param node: the node to traverse
        :return: the parser associated with the class
        """
        data = constructor.construct_mapping(node, deep=True)
        from .parsers import get_parser

        return get_parser(cls, version=data.get('version', None)).parse(cls, data)

    def save_config(self, filename: Optional[str] = None):
        """
        Save the object's config into a YAML file.

        :param filename: file path of the yaml file, if not given then :attr:`config_abspath` is used
        """
        f = filename or getattr(self, 'config_abspath', None)
        if not f:
            f = tempfile.NamedTemporaryFile(
                'w',
                delete=False,
            ).name
            warnings.warn(
                f'no "filename" is given, {self!r}\'s config will be saved to: {f}'
            )
        with open(f, 'w', encoding='utf8') as fp:
            JAML.dump(self, fp)

    @classmethod
    def load_config(
        cls,
        source: Union[str, TextIO, Dict],
        *,
        allow_py_modules: bool = True,
        substitute: bool = True,
        context: Optional[Dict[str, Any]] = None,
        override_with: Optional[Dict] = None,
        override_metas: Optional[Dict] = None,
        **kwargs,
    ) -> 'JAMLCompatible':
        """A high-level interface for loading configuration with features
        of loading extra py_modules, substitute env & context variables. Any class that
        implements :class:`JAMLCompatible` mixin can enjoy this feature, e.g. :class:`BaseFlow`,
        :class:`BaseExecutor`, :class:`BaseDriver` and all their subclasses.

        Support substitutions in YAML:
            - Environment variables: `${{ENV.VAR}}` (recommended), ``${{VAR}}``, ``$VAR``.
            - Context dict (``context``): ``${{VAR}}``(recommended), ``$VAR``.
            - Internal reference via ``this`` and ``root``: ``${{this.same_level_key}}``, ``${{root.root_level_key}}``

        Substitutions are carried in the order and multiple passes to resolve variables with best effort.

        .. highlight:: yaml
        .. code-block:: yaml

            !BaseEncoder
            metas:
                name: ${{VAR_A}}  # env or context variables
                workspace: my-${{this.name}}  # internal reference

        .. highlight:: python
        .. code-block:: python

            # load Executor from yaml file
            BaseExecutor.load_config('a.yml')

            # load Executor from yaml file and substitute environment variables
            os.environ['VAR_A'] = 'hello-world'
            b = BaseExecutor.load_config('a.yml')
            assert b.name == hello-world

            # load Executor from yaml file and substitute variables from a dict
            b = BaseExecutor.load_config('a.yml', context={'VAR_A': 'hello-world'})
            assert b.name == hello-world

            # disable substitute
            b = BaseExecutor.load_config('a.yml', substitute=False)


        .. # noqa: DAR401
        :param source: the multi-kind source of the configs.
        :param allow_py_modules: allow importing plugins specified by ``py_modules`` in YAML at any levels
        :param substitute: substitute environment, internal reference and context variables.
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :param override_with: dictionary of parameters to overwrite from the default config
        :param override_metas: dictionary of parameters to overwrite from the default config
        :param kwargs: kwargs for parse_config_source
        :return: :class:`JAMLCompatible` object
        """
        stream, s_path = parse_config_source(source, **kwargs)
        with stream as fp:
            # first load yml with no tag
            no_tag_yml = JAML.load_no_tags(fp)
            if no_tag_yml:
                no_tag_yml.update(**kwargs)
                if override_with is not None:
                    with_params = no_tag_yml.get('with', None)
                    if with_params:
                        with_params.update(**override_with)
                        no_tag_yml.update(with_params)
                    else:
                        no_tag_yml['with'] = override_with
                if override_metas is not None:
                    metas_params = no_tag_yml.get('metas', None)
                    if metas_params:
                        metas_params.update(**override_metas)
                        no_tag_yml.update(metas_params)
                    else:
                        no_tag_yml['metas'] = override_metas

            else:
                raise BadConfigSource(
                    f'can not construct {cls} from an empty {source}. nothing to read from there'
                )
            if substitute:
                # expand variables
                no_tag_yml = JAML.expand_dict(no_tag_yml, context)
            if allow_py_modules:
                # also add YAML parent path to the search paths
                load_py_modules(
                    no_tag_yml,
                    extra_search_paths=(os.path.dirname(s_path),) if s_path else None,
                )
            from ..flow.base import Flow

            if issubclass(cls, Flow):
                tag_yml = JAML.unescape(
                    JAML.dump(no_tag_yml),
                    include_unknown_tags=False,
                    jtype_whitelist=('Flow',),
                )
            else:
                # revert yaml's tag and load again, this time with substitution
                tag_yml = JAML.unescape(JAML.dump(no_tag_yml))
            # load into object, no more substitute
            return JAML.load(tag_yml, substitute=False)
