import inspect
from functools import reduce
from typing import Any, Dict, Optional, Set, Type

from jina.jaml.parsers.base import VersionedYAMLParser
from jina.serve.gateway import BaseGateway


# TODO: unify code with jina/jaml/parsers/executor/legacy.py
class LegacyParser(VersionedYAMLParser):
    """Legacy parser for gateway."""

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
