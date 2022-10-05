from typing import Dict


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
        'py_modules': '',  #: a list of strings, the python dependencies of the executor
    }


def get_executor_taboo():
    """
    Returns a set of executor meta variables
    :return: set of executor meta variables
    """
    taboo = {'self', 'args', 'kwargs', 'metas', 'requests', 'runtime_args'}
    _defaults = get_default_metas()
    taboo.update(_defaults.keys())
    return taboo
