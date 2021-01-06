import argparse
from typing import Dict, Any

from ..base import VersionedYAMLParser
from ....enums import PodRoleType
from ....flow import Flow
from ....helper import expand_env_var, ArgNamespace
from ....parsers import set_pod_parser, set_gateway_parser


def _get_taboo():
    """Get a set of keys that should not be dumped"""
    return {k.dest for k in set_pod_parser()._actions if k.help == argparse.SUPPRESS}


class V1Parser(VersionedYAMLParser):
    """V1Parser introduces new syntax and features:

        - It has a top-level field ``version``
        - ``pods`` is now a List of Dict (rather than a Dict as prev.)
        - ``name`` is now optional
        - new field ``method`` can be used to specify how to add this Pod into the Flow, availables are:
            - ``add``: (default) equal to `Flow.add(...)`
            - ``needs``: (default) equal to `Flow.needs(...)`
            - ``inspect``: (default) equal to `Flow.inspect(...)`

    An example V1 YAML config can be found below:
        .. highlight:: yaml
        .. code-block:: yaml

            !Flow
            version: '1.0'
            pods:
              - name: pod0  # notice the change here, name is now an attribute
                method: add  # by default method is always add, available: add, needs, inspect
                uses: _pass
                needs: gateway
              - name: pod1  # notice the change here, name is now an attribute
                method: add  # by default method is always add, available: add, needs, inspect
                uses: _pass
                needs: gateway
              - method: inspect  # add an inspect node on pod1
              - method: needs  # let's try something new in Flow YAML v1: needs
                needs: [pod1, pod0]


    """
    version = '1'  # the version number this parser designed for

    def parse(self, cls: type, data: Dict) -> 'Flow':
        """Return the Flow YAML parser given the syntax version number

        :param data: flow yaml file loaded as python dict
        """
        envs = data.get('env', {})  # type: Dict[str, str]
        p = data.get('with', {})  # type: Dict[str, Any]
        a = p.pop('args') if 'args' in p else ()
        k = p.pop('kwargs') if 'kwargs' in p else {}
        # maybe there are some hanging kwargs in "parameters"
        tmp_a = (expand_env_var(v) for v in a)
        tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
        obj = cls(*tmp_a, env=envs, **tmp_p)

        pp = data.get('pods', [])
        for pods in pp:
            p_pod_attr = {kk: expand_env_var(vv) for kk, vv in pods.items()}
            # in v1 YAML, flow is an optional argument
            if p_pod_attr.get('name', None) != 'gateway':
                # ignore gateway when reading, it will be added during build()
                method = p_pod_attr.get('method', 'add')
                # support methods: add, needs, inspect
                getattr(obj, method)(**p_pod_attr, copy_flow=False)
        return obj

    def dump(self, data: 'Flow') -> Dict:
        """Return the dictionary given a versioned flow object

        :param data: versioned flow object
        """
        r = {}
        if data._version:
            r['version'] = data._version

        if data._env:
            r['env'] = data._env

        if data._kwargs:
            r['with'] = data._kwargs

        if data._pod_nodes:
            r['pods'] = []

        last_name = 'gateway'
        for k, v in data._pod_nodes.items():
            if k == 'gateway':
                continue
            kwargs = {}
            # only add "needs" when the value is not the last pod name
            if list(v.needs) != [last_name]:
                kwargs = {'needs': list(v.needs)}

            # get nondefault kwargs
            parser = set_pod_parser()
            if v.role == PodRoleType.GATEWAY:
                parser = set_gateway_parser()

            non_default_kw = ArgNamespace.get_non_defaults_args(v.args, parser)

            kwargs.update(non_default_kw)

            for t in _get_taboo():
                if t in kwargs:
                    kwargs.pop(t)
            last_name = kwargs['name']
            r['pods'].append(kwargs)
        return r
