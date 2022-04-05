from typing import TYPE_CHECKING, Any, Dict, Optional, Union

if TYPE_CHECKING:
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
