from typing import Any, Dict, Optional, Type

from jina.jaml.parsers.base import BaseLegacyParser
from jina.serve.gateway import BaseGateway


class GatewayLegacyParser(BaseLegacyParser):
    """Legacy parser for gateway."""

    def parse(
        self,
        cls: Type['BaseGateway'],
        data: Dict,
        runtime_args: Optional[Dict[str, Any]] = None,
    ) -> 'BaseGateway':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        :return: the Flow YAML parser given the syntax version number
        """
        from jina.logging.predefined import default_logger

        data['metas'] = {}

        cls._init_from_yaml = True
        # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}

        obj = cls(
            **data.get('with', {}),
            metas=data.get('metas', {}),
            requests=data.get('requests', {}),
            runtime_args=runtime_args,
        )
        cls._init_from_yaml = False

        obj.is_updated = False
        return obj

    def dump(self, data: 'BaseGateway') -> Dict:
        """
        :param data: versioned gateway object
        :return: the dictionary given a versioned flow object
        """
        a = {k: v for k, v in data._init_kwargs_dict.items()}
        r = {}
        if a:
            r['with'] = a

        return r
