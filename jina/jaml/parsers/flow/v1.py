import argparse
import os
from typing import Any, Dict, Optional

from jina import Flow
from jina.enums import DeploymentRoleType
from jina.helper import ArgNamespace, expand_env_var
from jina.jaml.parsers.base import VersionedYAMLParser
from jina.parsers import set_deployment_parser, set_gateway_parser


def _get_taboo(parser: argparse.ArgumentParser):
    """
    :param parser: deployment or gateway parser
    :return: set of keys that should not be dumped
    """
    return {k.dest for k in parser._actions if k.help == argparse.SUPPRESS}


class V1Parser(VersionedYAMLParser):
    """V1Parser introduces new syntax and features:

        - It has a top-level field ``version``
        - ``deployments`` is now a List of Dict (rather than a Dict as prev.)
        - ``name`` is now optional
        - new field ``method`` can be used to specify how to add this Deployment into the Flow, availables are:
            - ``add``: (default) equal to `Flow.add(...)`
            - ``needs``: (default) equal to `Flow.needs(...)`
            - ``inspect``: (default) equal to `Flow.inspect(...)`

    An example V1 YAML config can be found below:
        .. highlight:: yaml
        .. code-block:: yaml

            !Flow
            version: '1.0'
            deployments:
              - name: executor0  # notice the change here, name is now an attribute
                method: add  # by default method is always add, available: add, needs, inspect
                needs: gateway
              - name: executor1  # notice the change here, name is now an attribute
                method: add  # by default method is always add, available: add, needs, inspect
                needs: gateway
              - method: inspect  # add an inspect node on executor1
              - method: needs  # let's try something new in Flow YAML v1: needs
                needs: [executor1, executor0]


    """

    version = '1'  # the version number this parser designed for

    def parse(
        self, cls: type, data: Dict, runtime_args: Optional[Dict[str, Any]] = None
    ) -> 'Flow':
        """
        :param cls: the class registered for dumping/loading
        :param data: flow yaml file loaded as python dict
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        :return: the Flow YAML parser given the syntax version number
        """
        p = data.get('with', {})  # type: Dict[str, Any]

        a = p.pop('args') if 'args' in p else ()
        k = p.pop('kwargs') if 'kwargs' in p else {}
        # maybe there are some hanging kwargs in "parameters"
        tmp_a = (expand_env_var(v) for v in a)
        tmp_p = {kk: expand_env_var(vv) for kk, vv in {**k, **p}.items()}
        obj = cls(*tmp_a, **tmp_p)

        pp = data.get('executors', data.get('deployments', []))
        for deployments in pp:
            p_deployment_attr = {
                kk: expand_env_var(vv) for kk, vv in deployments.items()
            }
            # in v1 YAML, flow is an optional argument
            if p_deployment_attr.get('name', None) != 'gateway':
                # ignore gateway when reading, it will be added during build()
                method = p_deployment_attr.get('method', 'add')
                # support methods: add, needs, inspect
                getattr(obj, method)(**p_deployment_attr, copy_flow=False)

        return obj

    def dump(self, data: 'Flow') -> Dict:
        """
        :param data: versioned flow object
        :return: the dictionary given a versioned flow object
        """
        r = {}
        if data._version:
            r['version'] = data._version

        # to maintain order - version -> with -> executors
        r['with'] = {}
        if data._kwargs:
            r['with'].update(data._kwargs)

        if data._common_kwargs:
            r['with'].update(data._common_kwargs)

        if data._deployment_nodes:
            r['executors'] = []

        last_name = 'gateway'
        for k, v in data._deployment_nodes.items():
            kwargs = {}
            # only add "needs" when the value is not the last deployment name
            if list(v.needs) != [last_name]:
                kwargs = {'needs': list(v.needs)}

            # get nondefault kwargs
            parser = set_deployment_parser()
            if v.role == DeploymentRoleType.GATEWAY:
                parser = set_gateway_parser()

            non_default_kw = ArgNamespace.get_non_defaults_args(v.args, parser)

            kwargs.update(non_default_kw)

            for t in _get_taboo(parser):
                if t in kwargs:
                    kwargs.pop(t)
            if k == 'gateway':
                if 'JINA_FULL_CLI' in os.environ:
                    r['with'].update(kwargs)
                else:
                    continue
            else:
                last_name = kwargs['name']
                r['executors'].append(kwargs)

        return r
