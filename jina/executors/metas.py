from typing import Dict, Union, List


def get_default_metas() -> Dict:
    """
    Get a copy of default meta variables.

    NOTE: DO NOT ADD MORE ENTRIES HERE!

    :return: a deep copy of the default metas in a new dict
    """

    # NOTE: DO NOT ADD MORE ENTRIES HERE!
    return {
        'name': '',  #: a string, the name of the executor
        'description': '',  #: a string, the description of this executor. It will be used in automatics docs UI
        'workspace': '',  #: a string, the workspace of the executor
        'py_modules': '',
    }  #: a list of strings, the python dependencies of the executor


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
