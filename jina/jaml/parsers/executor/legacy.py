import inspect
from functools import reduce
from typing import Dict, Type, Set

from ..base import VersionedYAMLParser
from ....executors import BaseExecutor
from ....executors.metas import get_default_metas


class LegacyParser(VersionedYAMLParser):
    """Legacy parser for executor."""

    version = 'legacy'  # the version number this parser designed for

    @staticmethod
    def _get_all_arguments(class_):
        """

        :param class_: target class from which we want to retrieve arguments
        :return: all the arguments of all the classes from which `class_` inherits
        """

        def get_class_arguments(class_):
            """
            :param class_: the class to check
            :return: a list containing the arguments from `class_`
            """
            signature = inspect.signature(class_.__init__)
            class_arguments = [p.name for p in signature.parameters.values()]
            return class_arguments

        def accumulate_classes(cls) -> Set[Type]:
            """
            :param cls: the class to check
            :return: all classes from which cls inherits from
            """

            def _accumulate_classes(c, cs):
                cs.append(c)
                if cls == object:
                    return cs
                for base in c.__bases__:
                    _accumulate_classes(base, cs)
                return cs

            classes = []
            _accumulate_classes(cls, classes)
            return set(classes)

        all_classes = accumulate_classes(class_)
        args = list(map(lambda x: get_class_arguments(x), all_classes))
        return set(reduce(lambda x, y: x + y, args))

    def parse(self, cls: Type['BaseExecutor'], data: Dict) -> 'BaseExecutor':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :return: the Flow YAML parser given the syntax version number
        """
        from ....logging import default_logger

        _meta_config = get_default_metas()
        _meta_config.update(data.get('metas', {}))
        if _meta_config:
            data['metas'] = _meta_config

        cls._init_from_yaml = True
        # tmp_p = {kk: expand_env_var(vv) for kk, vv in data.get('with', {}).items()}
        obj = cls(
            **data.get('with', {}),
            metas=data.get('metas', {}),
            requests=data.get('requests', {}),
            runtime_args=data.get('runtime_args', {}),
        )
        cls._init_from_yaml = False

        # check if the yaml file used to instanciate 'cls' has arguments that are not in 'cls'
        arguments_from_cls = LegacyParser._get_all_arguments(cls)
        arguments_from_yaml = set(data.get('with', {}))
        difference_set = arguments_from_yaml - arguments_from_cls
        if any(difference_set):
            default_logger.warning(
                f'The arguments {difference_set} defined in the YAML are not expected in the '
                f'class {cls.__name__}'
            )

        default_logger.success(f'successfully built {cls.__name__} from a yaml config')

        # if node.tag in {'!CompoundExecutor'}:
        #     os.environ['JINA_WARN_UNNAMED'] = 'YES'

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

        if hasattr(data, 'components'):
            r['components'] = data.components
        return r
