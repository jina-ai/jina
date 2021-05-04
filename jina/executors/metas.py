from typing import Dict, Union, List

_defaults = None


def get_default_metas() -> Dict:
    """
    Get a copy of default meta variables.

    :return: default metas
    """
    import copy

    global _defaults

    if _defaults is None:
        from ..jaml import JAML
        from pkg_resources import resource_stream

        with resource_stream(
            'jina', '/'.join(('resources', 'executors.metas.default.yml'))
        ) as fp:
            _defaults = JAML.load(
                fp
            )  # do not expand variables at here, i.e. DO NOT USE expand_dict(yaml.load(fp))

    return copy.deepcopy(_defaults)


def fill_metas_with_defaults(d: Dict) -> Dict:
    """Fill the incomplete ``metas`` field with complete default values

    :param d: the loaded YAML map
    :return: dictionary with injected metas
    """

    def _scan(sub_d: Union[Dict, List]):
        if isinstance(sub_d, Dict):
            for k, v in sub_d.items():
                if k == 'metas':
                    _tmp = get_default_metas()
                    _tmp.update(v)
                    sub_d[k] = _tmp
                elif isinstance(v, dict):
                    _scan(v)
                elif isinstance(v, list):
                    _scan(v)
        elif isinstance(sub_d, List):
            for idx, v in enumerate(sub_d):
                if isinstance(v, dict):
                    _scan(v)
                elif isinstance(v, list):
                    _scan(v)

    _scan(d)
    return d
