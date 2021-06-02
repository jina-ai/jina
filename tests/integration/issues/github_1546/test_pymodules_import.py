import pytest

from jina.executors import BaseExecutor


def test_import_with_abs_namespace_should_pass():
    """
    This is a valid structure:
        - "my_cust_module" is not a python module (lack of __init__.py under the root)
        - to import ``foo.py``, you must to use ``from jinahub.foo import bar``
        - ``jinahub`` is a common namespace for all plugin-modules, not changeable.
        - ``helper.py`` needs to be put BEFORE `my_cust.py` in YAML ``py_modules``

    File structure:

         my_cust_module
           |- my_cust.py
           |- helper.py
           |- config.yml
                |- py_modules
                       |- helper.py
                       |- my_cust.py
    """

    b = BaseExecutor.load_config('good1/crafter.yml')
    assert b.__class__.__name__ == 'GoodCrafter1'


def test_import_with_module_structure_should_pass():
    """
    This is a valid structure and it is RECOMMENDED:
        - "my_cust_module" is a python module
        - all core logic of your customized executor goes to ``__init__.py``
        - to import ``foo.py``, you can use relative import, e.g. ``from .foo import bar``
        - ``helper.py`` needs to be put BEFORE `__init__.py` in YAML ``py_modules``

    This is also the structure given by ``jina hub new`` CLI.

    File structure:

         my_cust_module
           |- __init__.py
           |- helper.py
           |- config.yml
                |- py_modules
                       |- helper.py
                       |- __init__.py
    """
    b = BaseExecutor.load_config('good2/crafter.yml')
    assert b.__class__.__name__ == 'GoodCrafter2'


def test_import_with_hub_structure_should_pass():
    """
    copy paste from hub module structure should work
    this structure is copy-paste from: https://github.com/jina-ai/jina-hub/tree/master/crafters/image/FiveImageCropper

    File structure:
        my_cust_modul
          |
          |- __init__.py
          |- helper.py
          |- config.yml
                |- py_modules
                       |- helper.py
                       |- __init.py
    :return:
    """
    b = BaseExecutor.load_config('good3/config.yml')
    assert b.__class__.__name__ == 'GoodCrafter3'


def test_import_casual_structure_should_fail():
    # this structure is a copy-paste from
    # https://github.com/jina-ai/jina/issues/1546#issuecomment-751481422
    with pytest.raises(ImportError):
        BaseExecutor.load_config('bad1/crafter.yml')
