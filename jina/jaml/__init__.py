import copy
import os
import re
import string
import tempfile
import warnings
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple, Union

import yaml
from yaml.constructor import FullConstructor

from jina.jaml.helper import (
    JinaLoader,
    JinaResolver,
    get_jina_loader_with_runtime,
    load_py_modules,
    parse_config_source,
)

__all__ = ['JAML', 'JAMLCompatible']

from jina.excepts import BadConfigSource

internal_var_regex = re.compile(
    r'{.+}|\$[a-zA-Z0-9_]*\b'
)  # detects exp's of the form {var} or $var

context_regex_str = r'\${{\s[a-zA-Z0-9_]*\s}}'
context_var_regex = re.compile(
    context_regex_str
)  # matches expressions of form '${{ var }}'

context_dot_regex_str = (
    r'\${{\sCONTEXT\.[a-zA-Z0-9_]*\s}}|\${{\scontext\.[a-zA-Z0-9_]*\s}}'
)
context_dot_regex = re.compile(
    context_dot_regex_str
)  # matches expressions of form '${{ ENV.var }}' or '${{ env.var }}'

new_env_regex_str = r'\${{\sENV\.[a-zA-Z0-9_]*\s}}|\${{\senv\.[a-zA-Z0-9_]*\s}}'
new_env_var_regex = re.compile(
    new_env_regex_str
)  # matches expressions of form '${{ ENV.var }}' or '${{ env.var }}'

env_var_deprecated_regex_str = r'\$[a-zA-Z0-9_]*'
env_var_deprecated_regex = re.compile(
    r'\$[a-zA-Z0-9_]*'
)  # matches expressions of form '$var'

env_var_regex_str = env_var_deprecated_regex_str + '|' + new_env_regex_str
env_var_regex = re.compile(env_var_regex_str)  # matches either of the above

yaml_ref_regex = re.compile(
    r'\${{([\w\[\].]+)}}'
)  # matches expressions of form '${{root.name[0].var}}'


class ContextVarTemplate(string.Template):
    delimiter = '$$'  # variables that should be substituted with values from the context are internally denoted with '$$'


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

    You need to use specific syntax to tell Jina to evaluate an expression rather than treat it as a string,
    which is based on GitHub actions syntax, and looks like this:

    .. highlight:: yaml
    .. code-block:: yaml

        ${{ <expression> }}

    This expression can be evaluated directly (i.e. substituted by the real value) when being loaded,
    by using :meth:`load(substitute=True)`

    JAML supports three different kinds of variables to be used as expressions: `Environment variables`
    (coming form the environment itself), `context variables` (being passed as a dict),
    and `internal references` (included in the .yaml file itself).

    An environment variable `var` is accessed through the following syntax:

    .. highlight:: yaml
    .. code-block:: yaml

        ${{ env.var }}

    Note the mandatory spaces before and after the variable denotation.

    Context variables can be accessed using the following syntax:

    .. highlight:: yaml
    .. code-block:: yaml

        ${{ context_var }}

    Or, if you want to be explicit:

    .. highlight:: yaml
    .. code-block:: yaml

        ${{ context.context_var }}

    These context variables are passed as a dict:

    .. highlight:: python
    .. code-block:: python

        obj = JAML.load(
            fp, substitute=True, context={'context_var': 3.14, 'context_var2': 'hello-world'}
        )

    Internal references point to other variables in the yaml file itself, and can be accessed using the following syntax:

    .. highlight:: yaml
    .. code-block:: yaml

        ${{root.path.to.var}}

    Note omission of spaces in this syntax.


    .. note::
        :class:`BaseFlow`, :class:`BaseExecutor`, :class:`BaseGateway`
        and all their subclasses have already implemented JAML interfaces,
        to load YAML config into objects, please use :meth:`Flow.load_config`,
        :meth:`BaseExecutor.load_config`, etc.

    """

    @staticmethod
    def load(
        stream,
        substitute: bool = False,
        context: Dict[str, Any] = None,
        runtime_args: Optional[Dict[str, Any]] = None,
    ):
        """Parse the first YAML document in a stream and produce the corresponding Python object.

        .. note::
            :class:`BaseFlow`, :class:`BaseExecutor`, :class:`BaseGateway`
            and all their subclasses have already implemented JAML interfaces,
            to load YAML config into objects, please use :meth:`Flow.load_config`,
            :meth:`BaseExecutor.load_config`, etc.

        :param stream: the stream to load
        :param substitute: substitute environment, internal reference and context variables.
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        :return: the Python object

        """
        r = yaml.load(stream, Loader=get_jina_loader_with_runtime(runtime_args))

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
    def registered_classes() -> Dict:
        """
        Return a dict of tags and :class:`JAMLCompatible` classes that have been registered.

        :return: tags and classes
        """
        return {
            k[1:]: v
            for k, v in JinaLoader.yaml_constructors.items()
            if k and k.startswith('!')
        }

    @staticmethod
    def cls_from_tag(tag: str) -> Optional['JAMLCompatible']:
        """Fetch class from yaml tag

        :param tag: yaml tag
        :return: class object from tag
        """
        if not tag.startswith('!'):
            tag = '!' + tag
        bound = JinaLoader.yaml_constructors.get(tag, None)
        return bound.__self__ if bound else None

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

        from jina.helper import parse_arg

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
                            if resolve_ref and yaml_ref_regex.findall(v):
                                sub_d[k] = _resolve_yaml_reference(v, p)
                            else:
                                sub_d[k] = _sub(v)
            elif isinstance(sub_d, list):
                for idx, v in enumerate(sub_d):
                    if isinstance(v, (dict, list)):
                        _replace(v, p[idx], resolve_ref)
                    else:
                        if isinstance(v, str):
                            if resolve_ref and yaml_ref_regex.findall(v):
                                sub_d[idx] = _resolve_yaml_reference(v, p)
                            else:
                                sub_d[idx] = _sub(v)

        def _var_to_substitutable(v, exp=context_var_regex):
            def repl_fn(matchobj):
                return '$$' + matchobj.group(0)[4:-3]

            return re.sub(exp, repl_fn, v)

        def _to_env_var_synatx(v):
            v = _var_to_substitutable(v, new_env_var_regex)

            def repl_fn(matchobj):
                match_str = matchobj.group(0)
                match_str = match_str.replace('ENV.', '')
                match_str = match_str.replace('env.', '')
                return match_str[1:]

            return re.sub(r'\$\$[a-zA-Z0-9_.]*', repl_fn, v)

        def _to_normal_context_var(v):
            def repl_fn(matchobj):
                match_str = matchobj.group(0)
                match_str = match_str.replace('CONTEXT.', '')
                match_str = match_str.replace('context.', '')
                return match_str

            return re.sub(context_dot_regex, repl_fn, v)

        def _sub(v):

            # substitute template with actual value either from context or env variable
            # v could contain template of the form
            #
            # 1)    ${{ var }},${{ context.var }},${{ CONTEXT.var }} when need to be parsed with the context dict
            # or
            # 2 )   ${{ ENV.var }},${{ env.var }},$var ( deprecated) when need to be parsed with env
            #
            #
            # internally env var (1) and context var (2) are treated differently, both of them are cast to a unique and
            # normalize template format and then are parsed
            # 1) context variables placeholder are cast to $$var then we use the ContextVarTemplate to parse the context
            # variables
            # 2) env variables placeholder are cast to $var then we leverage the os.path.expandvars to replace by
            # environment variables.

            if env_var_deprecated_regex.findall(v) and not env_var_regex.findall(
                v
            ):  # catch expressions of form '$var'
                warnings.warn(
                    'Specifying environment variables via the syntax `$var` is deprecated.'
                    'Use `${{ ENV.var }}` instead.',
                    category=DeprecationWarning,
                )
            if new_env_var_regex.findall(
                v
            ):  # handle expressions of form '${{ ENV.var}}',
                v = _to_env_var_synatx(v)
            if context_dot_regex.findall(v):
                v = _to_normal_context_var(v)
            if context_var_regex.findall(v):  # handle expressions of form '${{ var }}'
                v = _var_to_substitutable(v)
                if context:
                    v = ContextVarTemplate(v).safe_substitute(
                        context
                    )  # use vars provided in context
            v = os.path.expandvars(
                v
            )  # gets env var and parses to python objects if neededd
            return parse_arg(v)

        def _resolve_yaml_reference(v, p):

            org_v = v
            # internal references are of the form ${{path}} where path is a yaml path like root.executors[0].name

            def repl_fn(matchobj):
                match_str = matchobj.group(0)
                match_str_origin = match_str

                match_str = re.sub(
                    yaml_ref_regex, '{\\1}', match_str
                )  # from ${{var}} to {var} to leverage python formatter

                try:
                    # "root" context is now the global namespace
                    # "this" context is now the current node namespace
                    match_str = match_str.format(root=expand_map, this=p, ENV=env_map)
                except AttributeError as ex:
                    raise AttributeError(
                        'variable replacement is failed, please check your YAML file.'
                    ) from ex
                except KeyError:
                    return match_str_origin

                return match_str

            v = re.sub(yaml_ref_regex, repl_fn, v)

            return parse_arg(v)

        _scan(d, expand_map)
        _scan(dict(os.environ), env_map)

        # first do var replacement
        _replace(d, expand_map)

        # do `resolve_passes` rounds of scan-replace to resolve internal references
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
        from jina.jaml.parsers import get_parser

        config_dict = get_parser(cls, version=data._version).dump(data)
        config_dict_with_jtype = {
            'jtype': cls.__name__
        }  # specifies the type of Jina object that is represented
        config_dict_with_jtype.update(config_dict)
        # To maintain compatibility with off-the-shelf parsers we don't want any tags ('!...') to show up in the output
        # Since pyyaml insists on receiving a tag, we need to pass the default map tag. This won't show up in the output
        return representer.represent_mapping(
            representer.DEFAULT_MAPPING_TAG, config_dict_with_jtype
        )

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
        from jina.jaml.parsers import get_parser

        return get_parser(cls, version=data.get('version', None)).parse(
            cls, data, runtime_args=constructor.runtime_args
        )

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
        with open(f, 'w', encoding='utf-8') as fp:
            JAML.dump(self, fp)

    @classmethod
    def load_config(
        cls,
        source: Union[str, TextIO, Dict],
        *,
        allow_py_modules: bool = True,
        substitute: bool = True,
        context: Optional[Dict[str, Any]] = None,
        uses_with: Optional[Dict] = None,
        uses_metas: Optional[Dict] = None,
        uses_requests: Optional[Dict] = None,
        extra_search_paths: Optional[List[str]] = None,
        py_modules: Optional[str] = None,
        runtime_args: Optional[Dict[str, Any]] = None,
        uses_dynamic_batching: Optional[Dict] = None,
        needs: Optional[Set[str]] = None,
        include_gateway: bool = True,
        noblock_on_start: bool = False,
        **kwargs,
    ) -> 'JAMLCompatible':
        """A high-level interface for loading configuration with features
        of loading extra py_modules, substitute env & context variables. Any class that
        implements :class:`JAMLCompatible` mixin can enjoy this feature, e.g. :class:`BaseFlow`,
        :class:`BaseExecutor`, :class:`BaseGateway` and all their subclasses.

        Support substitutions in YAML:
            - Environment variables: ``${{ ENV.VAR }}`` (recommended), ``$VAR`` (deprecated).
            - Context dict (``context``): ``${{ CONTEXT.VAR }}``(recommended), ``${{ VAR }}``.
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
            assert b.name == 'hello-world'

            # load Executor from yaml file and substitute variables from a dict
            b = BaseExecutor.load_config('a.yml', context={'VAR_A': 'hello-world'})
            assert b.name == 'hello-world'

            # disable substitute
            b = BaseExecutor.load_config('a.yml', substitute=False)


        .. # noqa: DAR401
        :param source: the multi-kind source of the configs.
        :param allow_py_modules: allow importing plugins specified by ``py_modules`` in YAML at any levels
        :param substitute: substitute environment, internal reference and context variables.
        :param context: context replacement variables in a dict, the value of the dict is the replacement.
        :param uses_with: dictionary of parameters to overwrite from the default config's with field
        :param uses_metas: dictionary of parameters to overwrite from the default config's metas field
        :param uses_requests: dictionary of parameters to overwrite from the default config's requests field
        :param extra_search_paths: extra paths used when looking for executor yaml files
        :param py_modules: Optional py_module from which the object need to be loaded
        :param runtime_args: Optional dictionary of parameters runtime_args to be directly passed without being parsed into a yaml config
        :param uses_dynamic_batching: dictionary of parameters to overwrite from the default config's dynamic_batching field
        :param needs: the name of the Deployment(s) that this Deployment receives data from. One can also use "gateway" to indicate the connection with the gateway.
        :param include_gateway: Defines if the gateway deployment should be included, defaults to True
        :param noblock_on_start: If set, starting a Pod/Deployment does not block the thread/process. It then relies on '
            '`wait_start_success` at outer function for the postpone check.
        :param kwargs: kwargs for parse_config_source
        :return: :class:`JAMLCompatible` object
        """
        if runtime_args:
            kwargs['runtimes_args'] = (
                dict()
            )  # when we have runtime args it is needed to have an empty runtime args session in the yam config

        if py_modules:
            kwargs['runtimes_args']['py_modules'] = py_modules

        if isinstance(source, str) and os.path.exists(source):
            extra_search_paths = (extra_search_paths or []) + [os.path.dirname(source)]

        stream, s_path = parse_config_source(
            source, extra_search_paths=extra_search_paths, **kwargs
        )
        with stream as fp:
            # first load yml with no tag
            no_tag_yml = JAML.load_no_tags(fp)
            if no_tag_yml:
                no_tag_yml.update(**kwargs)

                # if there is `override_with` u should make sure that `uses_with` does not remain in the yaml
                def _delitem(
                    obj,
                    key,
                ):
                    value = obj.get(key, None)
                    if value:
                        del obj[key]
                        return
                    for k, v in obj.items():
                        if isinstance(v, dict):
                            _delitem(v, key)

                if uses_with is not None:
                    _delitem(no_tag_yml, key='uses_with')
                if uses_metas is not None:
                    _delitem(no_tag_yml, key='uses_metas')
                if uses_requests is not None:
                    _delitem(no_tag_yml, key='uses_requests')
                if uses_dynamic_batching is not None:
                    _delitem(no_tag_yml, key='uses_dynamic_batching')
                cls._override_yml_params(no_tag_yml, 'with', uses_with)
                cls._override_yml_params(no_tag_yml, 'metas', uses_metas)
                cls._override_yml_params(no_tag_yml, 'requests', uses_requests)
                cls._override_yml_params(
                    no_tag_yml, 'dynamic_batching', uses_dynamic_batching
                )

            else:
                raise BadConfigSource(
                    f'can not construct {cls} from an empty {source}. nothing to read from there'
                )
            if substitute:
                # expand variables
                no_tag_yml = JAML.expand_dict(no_tag_yml, context)

            if allow_py_modules:
                _extra_search_paths = extra_search_paths or []
                load_py_modules(
                    no_tag_yml,
                    extra_search_paths=(
                        (_extra_search_paths + [os.path.dirname(s_path)])
                        if s_path
                        else _extra_search_paths
                    ),
                )

            from jina.enums import DeploymentRoleType
            from jina.orchestrate.deployments import Deployment
            from jina.orchestrate.flow.base import Flow

            if issubclass(cls, Flow):
                no_tag_yml_copy = copy.copy(no_tag_yml)
                # only needed for Flow
                if no_tag_yml_copy.get('with') is None:
                    no_tag_yml_copy['with'] = {}
                no_tag_yml_copy['with']['extra_search_paths'] = (
                    no_tag_yml_copy['with'].get('extra_search_paths') or []
                ) + (extra_search_paths or [])

                if cls.is_valid_jaml(no_tag_yml_copy):
                    no_tag_yml = no_tag_yml_copy

                tag_yml = JAML.unescape(
                    JAML.dump(no_tag_yml),
                    include_unknown_tags=False,
                    jtype_whitelist=('Flow',),
                )
            elif issubclass(cls, Deployment):
                no_tag_yml['with']['extra_search_paths'] = (
                    no_tag_yml['with'].get('extra_search_paths') or []
                ) + (extra_search_paths or [])
                no_tag_yml['with']['include_gateway'] = (
                    no_tag_yml['with'].get('include_gateway') or include_gateway
                )
                no_tag_yml['with']['noblock_on_start'] = noblock_on_start
                no_tag_yml['with']['deployment_role'] = DeploymentRoleType.DEPLOYMENT

                if needs:
                    no_tag_yml['needs'] = list(needs)

                tag_yml = JAML.unescape(
                    JAML.dump(no_tag_yml),
                    include_unknown_tags=False,
                    jtype_whitelist=('Deployment',),
                )
            else:
                # revert yaml's tag and load again, this time with substitution
                tag_yml = JAML.unescape(JAML.dump(no_tag_yml))
            # load into object, no more substitute
            obj = JAML.load(tag_yml, substitute=False, runtime_args=runtime_args)
            if not isinstance(obj, cls):
                raise BadConfigSource(
                    f'Can not construct {cls} object from {source}. Source might be an invalid configuration.'
                )

            if type(source) == str:
                obj._config_loaded = source
            return obj

    @classmethod
    def _override_yml_params(cls, raw_yaml, field_name, override_field):
        if override_field:
            field_params = raw_yaml.get(field_name, {})
            field_params.update(**override_field)
            raw_yaml[field_name] = field_params

    @staticmethod
    def is_valid_jaml(obj: Dict) -> bool:
        """
        Verifies the yaml syntax of a given object by first serializing it and attempting to deserialize and catch
        parser errors
        :param obj: yaml object
        :return: whether the syntax is valid or not

        """
        serialized_yaml = JAML.unescape(
            JAML.dump(obj),
            include_unknown_tags=False,
        )

        try:
            yaml.safe_load(serialized_yaml)
        # we only need to validate syntax, e.g, need to detect parser errors
        except yaml.parser.ParserError:
            return False
        except yaml.error.YAMLError:
            return True
        return True

    def _add_runtime_args(self, _runtime_args: Optional[Dict]):
        if _runtime_args:
            self.runtime_args = SimpleNamespace(**_runtime_args)
        else:
            self.runtime_args = SimpleNamespace()
