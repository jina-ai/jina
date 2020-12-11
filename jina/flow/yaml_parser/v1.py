import argparse
from typing import Dict, Any

from .base import VersionedYamlParser
from .. import Flow
from ...helper import expand_env_var
from ...parser import set_pod_parser


def _get_taboo():
    """Get a set of keys that should not be dumped"""
    return {k.dest for k in set_pod_parser()._actions if k.help == argparse.SUPPRESS}


class V1Parser(VersionedYamlParser):
    version = '1'  # the version number this parser designed for

    def parse(self, data: Dict) -> 'Flow':
        """Return the Flow YAML parser given the syntax version number

        :param data: flow yaml file loaded as python dict
        """
        p = data.get('with', {})  # type: Dict[str, Any]
        a = p.pop('args') if 'args' in p else ()
        k = p.pop('kwargs') if 'kwargs' in p else {}
        # maybe there are some hanging kwargs in "parameters"
        tmp_a = (expand_env_var(v) for v in a)
        tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
        obj = Flow(*tmp_a, **tmp_p)

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
            kwargs.update(v._kwargs)
            for t in _get_taboo():
                if t in kwargs:
                    kwargs.pop(t)
            last_name = kwargs['name']
            r['pods'].append(kwargs)
        return r
