from typing import Dict, List


def get_default_reqs(cls_mro: List[type]) -> Dict:
    """Get a copy of default meta variables

    :param cls_mro: the MRO inherited order followed.
    """
    import copy

    from pkg_resources import resource_stream

    from ..helper import yaml

    for cls in cls_mro:
        try:
            with resource_stream('jina',
                                 '/'.join(('resources', 'executors.requests.%s.yml' % cls.__name__))) as fp:
                _defaults = yaml.load(fp)  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

            return copy.deepcopy(_defaults)
        except FileNotFoundError:
            pass

    raise ValueError('not able to find any default settings along this chain %r' % cls_mro)
