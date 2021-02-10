from typing import Dict, Type

from ..base import VersionedYAMLParser
from ....drivers import BaseDriver


class LegacyParser(VersionedYAMLParser):
    version = 'legacy'  # the version number this parser designed for

    def parse(self, cls: Type['BaseDriver'], data: Dict) -> 'BaseDriver':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :return: the Flow YAML parser given the syntax version number
        """

        obj = cls(**data.get('with', {}))
        return obj

    def dump(self, data: 'BaseDriver') -> Dict:
        """
        :param data: versioned flow object
        :return: dictionary given a versioned flow object
        """
        a = {k: v for k, v in data._init_kwargs_dict.items()}
        r = {}
        if a:
            r['with'] = a
        return r
