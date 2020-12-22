from typing import Dict, Union

if False:
    from ...flow.base import BaseFlow
    from ...executors import BaseExecutor
    from ...drivers import BaseDriver


class VersionedYAMLParser:
    """ Flow YAML parser for specific version

    Every :class:`VersionedYAMLParser` must implement two methods and one class attribute:
        - :meth:`parse`: to load data (in :class:`dict`) into a :class:`BaseFlow` or :class:`BaseExecutor` object
        - :meth:`dump`: to dump a :class:`BaseFlow` or :class:`BaseExecutor` object into a :class:`dict`
        - :attr:`version`: version number in :class:`str` in format ``MAJOR.[MINOR]``
    """

    version = 'legacy'  #: the version number this parser designed for

    def parse(self, cls: type, data: Dict) -> Union['BaseFlow', 'BaseExecutor', 'BaseDriver']:
        """Return the Flow YAML parser given the syntax version number

        :param data: flow yaml file loaded as python dict
        """
        raise NotImplementedError

    def dump(self, data: Union['BaseFlow', 'BaseExecutor', 'BaseDriver']) -> Dict:
        """Return the dictionary given a versioned flow object

        :param data: versioned flow object
        """
        raise NotImplementedError
