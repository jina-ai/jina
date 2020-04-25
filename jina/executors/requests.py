__copyright__ = "Copyright (c) 2020 Jina AI Limited. All rights reserved."
__license__ = "Apache-2.0"

from typing import Dict, List

_defaults = {}


def get_default_reqs(cls_mro: List[type]) -> Dict:
    """Get a copy of default meta variables

    :param cls_mro: the MRO inherited order followed.
    """
    import copy

    global _defaults
    from ..helper import yaml

    for cls in cls_mro:
        try:
            if cls.__name__ not in _defaults:
                from pkg_resources import resource_stream
                with resource_stream('jina',
                                     '/'.join(('resources', 'executors.requests.%s.yml' % cls.__name__))) as fp:
                    _defaults[cls.__name__] = \
                        yaml.load(fp)  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

            if cls.__name__ != cls_mro[0].__name__:
                from ..logging import default_logger
                default_logger.debug(f'"requests.on" setting of {cls_mro[0]} fallback to general {cls} setting, '
                                     f'because you did not specify {cls_mro[0]}')
            return copy.deepcopy(_defaults[cls.__name__])
        except FileNotFoundError:
            pass

    raise ValueError('not able to find any default settings along this chain %r' % cls_mro)
