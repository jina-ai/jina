from typing import Dict

from .. import Flow


class VersionedYamlParser:
    """ Flow YAML parser for specific version

    Every :class:`VersionedYamlParser` must implement two methods and one class attribute:
        - :meth:`parse`: to load data (in :class:`dict`) into a :class:`Flow` object
        - :meth:`dump`: to dump a :class:`Flow` object into a :class:`dict`
        - :attr:`version`: version number in :class:`str` in format ``MAJOR.[MINOR]``
    """

    version = 'legacy'  #: the version number this parser designed for

    def parse(self, data: Dict) -> 'Flow':
        """Return the Flow YAML parser given the syntax version number

        :param data: flow yaml file loaded as python dict
        """
        raise NotImplementedError

    def dump(self, data: 'Flow') -> Dict:
        """Return the dictionary given a versioned flow object

        :param data: versioned flow object
        """
        raise NotImplementedError
