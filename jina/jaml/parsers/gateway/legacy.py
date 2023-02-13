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
        :param data: gateway yaml file loaded as python dict
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        :return: the Gateway YAML parser given the syntax version number
        """
        from jina.logging.predefined import default_logger

        data['metas'] = {}

        cls._init_from_yaml = True
        # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}

        for key in {
            'name',
            'port',
            'protocol',
            'host',
            'tracing',
            'graph_description',
            'graph_conditions',
            'deployments_addresses',
            'deployments_metadata',
            'deployments_no_reduce',
            'timeout_send',
            'retries',
            'compression',
            'runtime_name',
            'prefetch',
            'meter',
            'log_config',
        }:
            if runtime_args and not runtime_args.get(key) and data.get(key):
                runtime_args[key] = data.get(key)
        if runtime_args.get('default_port'):
            yaml_port = data.get('port')
            if isinstance(yaml_port, int):
                yaml_port = [yaml_port]
            runtime_args['port'] = yaml_port or runtime_args.get('port')

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
        :return: the dictionary given a versioned gateway object
        """
        a = {k: v for k, v in data._init_kwargs_dict.items()}
        r = {}
        if a:
            r['with'] = a

        return r
