import warnings
from typing import List, Optional

from .base import VersionedYamlParser
from ...excepts import BadFlowYAMLVersion


def _get_all_parser():
    from .legacy import LegacyParser
    from .v1 import V1Parser
    return [V1Parser, LegacyParser]


def get_parser(version: Optional[str]) -> 'VersionedYamlParser':
    """ Get parser given the YAML version

    :param version: yaml version number in "MAJOR[.MINOR]" format
    :return:
    """
    all_parsers = _get_all_parser()
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
        from .legacy import LegacyParser
        return LegacyParser()


def get_supported_versions() -> List[str]:
    """List all supported versions

    :return: supported versions sorted alphabetically
    """
    all_parsers = _get_all_parser()
    return list(sorted(p.version for p in all_parsers))
