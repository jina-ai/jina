from typing import Dict

from pkg_resources import resource_stream

from ..helper import yaml

with resource_stream('jina', '/'.join(('resources', 'executors.requests.default.yml'))) as fp:
    defaults = yaml.load(fp)  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))


def get_default_requests() -> Dict:
    """Get a copy of default meta variables"""
    return {k: v for k, v in defaults.items()}
