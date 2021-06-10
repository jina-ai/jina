from typing import Dict, Any, Type

from ..base import VersionedYAMLParser
from ....enums import PodRoleType
from ....flow.base import Flow
from ....helper import expand_env_var, ArgNamespace
from ....parsers import set_gateway_parser, set_pod_parser


class LegacyParser(VersionedYAMLParser):
    """The legacy parser."""

    version = 'legacy'  # the version number this parser designed for

    def parse(self, cls: Type['Flow'], data: Dict) -> 'Flow':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :return: the Flow YAML parser given the syntax version number
        """
        p = data.get('with', {})  # type: Dict[str, Any]
        a = p.pop('args') if 'args' in p else ()
        k = p.pop('kwargs') if 'kwargs' in p else {}
        # maybe there are some hanging kwargs in "parameters"
        tmp_a = (expand_env_var(v) for v in a)
        tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
        obj = cls(*tmp_a, **tmp_p)

        pp = data.get('pods', {})
        for pod_name, pod_attr in pp.items():
            p_pod_attr = {kk: expand_env_var(vv) for kk, vv in pod_attr.items()}
            if pod_name != 'gateway':
                # ignore gateway when reading, it will be added during build()
                obj.add(name=pod_name, **p_pod_attr, copy_flow=False)

        return obj

    def dump(self, data: 'Flow') -> Dict:
        """
        :param data: versioned flow object
        :return: the dictionary given a versioned flow object
        """
        r = {}
        if data._version:
            r['version'] = data._version

        if data._kwargs:
            r['with'] = data._kwargs

        if data._pod_nodes:
            r['pods'] = {}

        if 'gateway' in data._pod_nodes:
            # always dump gateway as the first pod, if exist
            r['pods']['gateway'] = {}

        for k, v in data._pod_nodes.items():
            if k == 'gateway':
                continue

            kwargs = {'needs': list(v.needs)} if v.needs else {}

            parser = set_pod_parser()
            if v.role == PodRoleType.GATEWAY:
                parser = set_gateway_parser()

            non_default_kw = ArgNamespace.get_non_defaults_args(v.args, parser)

            kwargs.update(non_default_kw)

            if 'name' in kwargs:
                kwargs.pop('name')

            r['pods'][k] = kwargs
        return r
