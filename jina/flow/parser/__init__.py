import warnings
from typing import Dict, List

from ...excepts import BadFlowYAMLVersion

if False:
    from .. import Flow

loader_prefix = 'load_v_'
dumper_prefix = 'dump_v_'


def parse(data: Dict) -> 'Flow':
    """Return the Flow YAML parser given the syntax version number

    :param data: flow yaml file loaded as python dict
    """
    from . import loader

    version = data.get('version', 'legacy')
    v = version.replace('.', '_')
    p = getattr(loader, loader_prefix + v, None)
    if not p:
        p = getattr(loader, loader_prefix + v.split('_')[0], None)
        warnings.warn(f'can not find the parser for {version}, '
                      f'will use the parser for version: "{v.split("_")[0]}"', UserWarning)
    if not p:
        raise BadFlowYAMLVersion(f'{version} is not a valid version number')
    obj = p(data)
    obj._version = version
    obj.logger.success(f'successfully built a Flow from a YAML version: {version}')
    return obj


def dump(data: 'Flow') -> Dict:
    """Return the dictionary given a versioned flow object

    :param data: versioned flow object
    """
    from . import dumper
    version = data._version
    v = version.replace('.', '_')
    p = getattr(dumper, dumper_prefix + v, None)
    if not p:
        p = getattr(dumper, dumper_prefix + v.split('_')[0], None)
        warnings.warn(f'can not find the dumper for {version}, '
                      f'will use the dumper for version: "{v.split("_")[0]}"', UserWarning)
    if not p:
        raise BadFlowYAMLVersion(f'{version} is not a valid version number')
    return p(data)


def get_support_versions() -> List[str]:
    """List all supported versions

    :return: supported versions sorted alphabetically
    """
    from . import loader
    result = []
    for v in dir(loader):
        if v.startswith(loader_prefix):
            result.append(v.replace(loader_prefix, '').replace('_', '.'))
    return list(sorted(result))
