import warnings
from typing import List, Optional, Type

from .base import VersionedYAMLParser
from .. import JAMLCompatible
from ...excepts import BadYAMLVersion


def _get_all_parser(cls: Type['JAMLCompatible']):
    """Get all parsers and legacy parser of a class

    :param cls: target class
    :return: a tuple of two elements; first is a list of all parsers, second is the legacy parser for default fallback
    """
    from ...executors import BaseExecutor
    from ...flow.base import Flow

    if issubclass(cls, Flow):
        return _get_flow_parser()
    elif issubclass(cls, BaseExecutor):
        return _get_exec_parser()
    else:
        return _get_default_parser()


def _get_flow_parser():
    from .flow.legacy import LegacyParser
    from .flow.v1 import V1Parser

    return [V1Parser, LegacyParser], V1Parser


def _get_exec_parser():
    from .executor.legacy import LegacyParser

    return [LegacyParser], LegacyParser


def _get_default_parser():
    from .default.v1 import V1Parser

    return [V1Parser], V1Parser


def get_parser(
    cls: Type['JAMLCompatible'], version: Optional[str]
) -> 'VersionedYAMLParser':
    """


    .. # noqa: DAR401
    :param cls: the target class to parse
    :param version: yaml version number in "MAJOR[.MINOR]" format
    :return: parser given the YAML version
    """
    all_parsers, legacy_parser = _get_all_parser(cls)
    if version:
        if isinstance(version, (float, int)):
            version = str(version)
        for p in all_parsers:
            if p.version == version:
                return p()
        for p in all_parsers:
            # fallback to major
            if version.split('.')[0] == p.version:
                warnings.warn(
                    f'can not find parser for version: {version}, '
                    f'fallback to parser for version: {p.version}',
                    UserWarning,
                )
                return p()
        raise BadYAMLVersion(f'{version} is not a valid version number')
    else:
        if version is not None:
            warnings.warn(
                f'can not find parser for version: {version}, '
                f'fallback to legacy parser. '
                f'this usually mean you are using a depreciated YAML format.',
                DeprecationWarning,
            )
        # fallback to legacy parser
        return legacy_parser()


def get_supported_versions(cls) -> List[str]:
    """List all supported versions

    :param cls: the class to check
    :return: supported versions sorted alphabetically
    """
    all_parsers, _ = _get_all_parser(cls)
    return list(sorted(p.version for p in all_parsers))
