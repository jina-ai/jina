from typing import Dict, Type

from ..base import VersionedYAMLParser
from ... import JAMLCompatible, JAML


class V1Parser(VersionedYAMLParser):
    """V1 default parser, used as the default parser for objects."""

    version = '1'  # the version number this parser designed for

    def parse(self, cls: Type['JAMLCompatible'], data: Dict) -> 'JAMLCompatible':
        """
        :param cls: target class type to parse into, must be a :class:`JAMLCompatible` type
        :param data: flow yaml file loaded as python dict
        :return: the YAML parser given the syntax version number
        """
        expanded_data = JAML.expand_dict(data, None)
        if 'with' in data:
            obj = cls(**expanded_data.get('with', {}))
        else:
            obj = cls(**expanded_data)
        return obj

    def dump(self, data: 'JAMLCompatible') -> Dict:
        """
        :param data: versioned flow object
        :return: the dictionary given a versioned flow object
        """
        a = V1Parser._dump_instance_to_yaml(data)
        r = {}
        if a:
            r['with'] = a
        return r

    @staticmethod
    def _dump_instance_to_yaml(instance):
        import inspect

        attributes = inspect.getmembers(instance, lambda a: not (inspect.isroutine(a)))
        return {
            a[0]: a[1]
            for a in attributes
            if not (a[0].startswith('__') and a[0].endswith('__'))
        }
