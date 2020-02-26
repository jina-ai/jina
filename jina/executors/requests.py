from typing import Dict


def get_default_reqs() -> Dict:
    """Get a copy of default meta variables"""
    import copy

    from pkg_resources import resource_stream

    from ..helper import yaml

    with resource_stream('jina', '/'.join(('resources', 'executors.requests.default.yml'))) as fp:
        _defaults = yaml.load(fp)  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

    return copy.deepcopy(_defaults)
