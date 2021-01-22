import warnings
from typing import List, Optional, Type

from .base import VersionedYAMLParser
from .. import JAMLCompatible
from ...excepts import BadFlowYAMLVersion


def _get_all_parser(cls: Type['JAMLCompatible']):
    """ Get all parsers and legacy parser of a class

    :param cls: target class
    :return: a tuple of two elements; first is a list of all parsers, second is the legacy parser for default fallback
    """
    from ...executors import BaseExecutor
    from ...flow import BaseFlow
    from ...drivers import BaseDriver
    if issubclass(cls, BaseFlow):
        return _get_flow_parser()
    elif issubclass(cls, BaseDriver):
        return _get_driver_parser()
    elif issubclass(cls, BaseExecutor):
        return _get_exec_parser()
    else:
        return _get_default_parser()


def _get_flow_parser():
    from .flow.legacy import LegacyParser
    from .flow.v1 import V1Parser
    return [V1Parser, LegacyParser], LegacyParser


def _get_exec_parser():
    from .executor.legacy import LegacyParser
    return [LegacyParser], LegacyParser


def _get_driver_parser():
    from .driver.legacy import LegacyParser
    return [LegacyParser], LegacyParser


def _get_default_parser():
    from .default.v1 import V1Parser
    return [V1Parser], V1Parser


def get_parser(cls: Type['JAMLCompatible'], version: Optional[str]) -> 'VersionedYAMLParser':
    """ Get parser given the YAML version

    :param cls: the target class to parse
    :param version: yaml version number in "MAJOR[.MINOR]" format
    :return:
    """
    all_parsers, legacy_parser = _get_all_parser(cls)
    if version:
        if isinstance(version, float) or isinstance(version, int):
            version = str(version)
        for p in all_parsers:
            if p.version == version:
                return p()
        for p in all_parsers:
            # fallback to major
            if version.split('.')[0] == p.version:
                warnings.warn(f'can not find parser for version: {version}, '
                              f'fallback to parser for version: {p.version}', UserWarning)
                return p()
        raise BadFlowYAMLVersion(f'{version} is not a valid version number')
    else:
        # fallback to legacy parser
        warnings.warn(f'can not find parser for version: {version}, '
                      f'fallback to legacy parser. '
                      f'this usually mean you are using a depreciated YAML format.', DeprecationWarning)
        return legacy_parser()


def get_supported_versions(cls) -> List[str]:
    """List all supported versions

    :return: supported versions sorted alphabetically
    """
    all_parsers, _ = _get_all_parser(cls)
    return list(sorted(p.version for p in all_parsers))
