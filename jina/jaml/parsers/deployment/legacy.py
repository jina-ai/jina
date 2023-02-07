from typing import TYPE_CHECKING, Any, Dict, Optional, Type

from jina.helper import ArgNamespace
from jina.jaml.parsers.base import BaseLegacyParser
from jina.jaml.parsers.flow.v1 import _get_taboo
from jina.parsers import set_deployment_parser

if TYPE_CHECKING:
    from jina.orchestrate.deployments import Deployment


class DeploymentLegacyParser(BaseLegacyParser):
    """Legacy parser for gateway."""

    def parse(
        self,
        cls: Type['Deployment'],
        data: Dict,
        runtime_args: Optional[Dict[str, Any]] = None,
    ) -> 'Deployment':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: deployment yaml file loaded as python dict
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        :return: the Deployment YAML parser given the syntax version number
        """
        cls._init_from_yaml = True
        # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}

        obj = cls(
            **data.get('with', {}),
            needs=data.get('needs'),
            runtime_args=runtime_args,
        )
        cls._init_from_yaml = False

        obj.is_updated = False
        return obj

    def dump(self, data: 'Deployment') -> Dict:
        """
        :param data: versioned deployment object
        :return: the dictionary given a versioned deployment object
        """
        r = {}
        r['with'] = {}
        parser = set_deployment_parser()
        non_default_kw = ArgNamespace.get_non_defaults_args(data.args, parser)
        for t in _get_taboo(parser):
            if t in non_default_kw:
                non_default_kw.pop(t)

        if non_default_kw:
            r['with'].update(non_default_kw)
        if data._gateway_kwargs:
            r['with'].update(data._gateway_kwargs)

        return r
