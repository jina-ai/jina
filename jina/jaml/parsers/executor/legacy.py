import dataclasses
from typing import Any, Dict, Optional, Type

from jina.jaml.parsers.base import BaseLegacyParser
from jina.serve.executors import BaseExecutor
from jina.serve.executors.metas import get_default_metas


class ExecutorLegacyParser(BaseLegacyParser):
    """Legacy parser for executor."""

    def parse(
        self,
        cls: Type['BaseExecutor'],
        data: Dict,
        runtime_args: Optional[Dict[str, Any]] = None,
    ) -> 'BaseExecutor':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        :return: the Flow YAML parser given the syntax version number
        """
        from jina.logging.predefined import default_logger

        _meta_config = get_default_metas()
        _meta_config.update(data.get('metas', {}))
        if _meta_config:
            data['metas'] = _meta_config

        cls._init_from_yaml = True
        # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}
        if dataclasses.is_dataclass(cls):
            obj = cls(
                **data.get('with', {}),
            )
            cls.__bases__[0].__init__(
                obj,
                **data.get('with', {}),
                metas=data.get('metas', {}),
                requests=data.get('requests', {}),
                dynamic_batching=data.get('dynamic_batching', {}),
                runtime_args=runtime_args,
            )
        else:
            obj = cls(
                **data.get('with', {}),
                metas=data.get('metas', {}),
                requests=data.get('requests', {}),
                dynamic_batching=data.get('dynamic_batching', {}),
                runtime_args=runtime_args,
            )
        cls._init_from_yaml = False

        # check if the yaml file used to instanciate 'cls' has arguments that are not in 'cls'
        arguments_from_cls = ExecutorLegacyParser._get_all_arguments(cls)
        arguments_from_yaml = set(data.get('with', {}))
        difference_set = arguments_from_yaml - arguments_from_cls
        # only log warnings about unknown args for main Pod
        if any(difference_set) and not ExecutorLegacyParser.is_tail_or_head(data):
            default_logger.warning(
                f'The given arguments {difference_set} are not defined in `{cls.__name__}.__init__`'
            )

        if not _meta_config:
            default_logger.warning(
                '"metas" config is not found in this yaml file, '
                'this map is important as it provides an unique identifier when '
                'persisting the executor on disk.'
            )

        # for compound executor
        if 'components' in data:
            obj.components = lambda: data['components']

        obj.is_updated = False
        return obj

    @staticmethod
    def is_tail_or_head(data: Dict) -> bool:
        """Based on name, compute if this is a tail/head Pod or a main Pod

        :param data: the data for the parser
        :return: True if it is tail/head, False otherwise
        """
        try:
            name = data.get('runtime_args', {}).get('name', '')
            return 'head' in name or 'tail' in name
        except Exception as _:
            pass  # name can be None in tests since it's not passed

    def dump(self, data: 'BaseExecutor') -> Dict:
        """
        :param data: versioned executor object
        :return: the dictionary given a versioned flow object
        """
        # note: we only save non-default property for the sake of clarity
        _defaults = get_default_metas()
        p = (
            {
                k: getattr(data.metas, k)
                for k, v in _defaults.items()
                if getattr(data.metas, k) != v
            }
            if hasattr(data, 'metas')
            else {}
        )
        a = {k: v for k, v in data._init_kwargs_dict.items() if k not in _defaults}
        r = {}
        if a:
            r['with'] = a
        if p:
            r['metas'] = p

        if hasattr(data, 'requests'):
            r['requests'] = {k: v.__name__ for k, v in data.requests.items()}

        if hasattr(data, 'dynamic_batching'):
            r['dynamic_batching'] = data.dynamic_batching

        if hasattr(data, 'components'):
            r['components'] = data.components
        return r
