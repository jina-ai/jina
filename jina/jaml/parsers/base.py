from typing import Dict, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from ...flow.base import Flow
    from ...executors import BaseExecutor


class VersionedYAMLParser:
    """Flow YAML parser for specific version

    Every :class:`VersionedYAMLParser` must implement two methods and one class attribute:
        - :meth:`parse`: to load data (in :class:`dict`) into a :class:`BaseFlow` or :class:`BaseExecutor` object
        - :meth:`dump`: to dump a :class:`BaseFlow` or :class:`BaseExecutor` object into a :class:`dict`
        - :attr:`version`: version number in :class:`str` in format ``MAJOR.[MINOR]``
    """

    version = 'legacy'  #: the version number this parser designed for

    def parse(self, cls: type, data: Dict) -> Union['Flow', 'BaseExecutor']:
        """Return the Flow YAML parser given the syntax version number


        .. # noqa: DAR401
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        """
        raise NotImplementedError

    def dump(self, data: Union['Flow', 'BaseExecutor']) -> Dict:
        """Return the dictionary given a versioned flow object


        .. # noqa: DAR401
        :param data: versioned flow object
        """
        raise NotImplementedError
