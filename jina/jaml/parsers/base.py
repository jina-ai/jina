import inspect
from abc import ABC
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, Optional, Set, Type, Union

if TYPE_CHECKING: # pragma: no cover
    from jina.orchestrate.flow.base import Flow
    from jina.serve.executors import BaseExecutor


class VersionedYAMLParser:
    """Flow YAML parser for specific version

    Every :class:`VersionedYAMLParser` must implement two methods and one class attribute:
        - :meth:`parse`: to load data (in :class:`dict`) into a :class:`BaseFlow` or :class:`BaseExecutor` object
        - :meth:`dump`: to dump a :class:`BaseFlow` or :class:`BaseExecutor` object into a :class:`dict`
        - :attr:`version`: version number in :class:`str` in format ``MAJOR.[MINOR]``
    """

    version = 'legacy'  #: the version number this parser designed for

    def parse(
        self, cls: type, data: Dict, runtime_args: Optional[Dict[str, Any]]
    ) -> Union['Flow', 'BaseExecutor']:
        """Return the Flow YAML parser given the syntax version number


        .. # noqa: DAR401
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :param runtime_args: Optional runtime_args to be directly passed without being parsed into a yaml config
        """
        raise NotImplementedError

    def dump(self, data: Union['Flow', 'BaseExecutor']) -> Dict:
        """Return the dictionary given a versioned flow object


        .. # noqa: DAR401
        :param data: versioned flow object
        """
        raise NotImplementedError


class BaseLegacyParser(VersionedYAMLParser, ABC):
    """
    BaseLegacyParser for classes that need parameter injection and that will be managed inside a runtime
    for instance, :class:`BaseExecutor` and :class:`BaseGateway`
    """

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
