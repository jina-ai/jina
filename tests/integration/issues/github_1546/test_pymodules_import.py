import pytest

from jina.serve.executors import BaseExecutor


def test_import_with_new_module_structure_should_pass():
    """
    This is a valid and **RECOMMENDED** structure:
        - python code for the executor organized in a package structure inside
          the ``executor/`` folder
        - core logic in ``executor/my_executor.py``
        - the ``executor/__init__.py`` contains
          ``from .my_executor import GoodCrafterNew``, which makes sure the
          custom executor class gets registered
        - all imports are relative - so in ``executor/my_executor.py`` the ``helper``
          module is imported as ``from .helper import foo``

    File structure:

         my_cust_module/
           |- executor/
                |- __init__.py
                |- my_executor.py
                |- helper.py
           |- config.yml
                |- py_modules
                       |- executor/__init__.py
    """

    b = BaseExecutor.load_config('good_new/crafter.yml')
    assert b.__class__.__name__ == 'GoodCrafterNew'


def test_import_with_old_module_structure_should_pass():
    """
    This is a valid structure, but not recommended:
        - "my_cust_module" is a python module
        - all core logic of your customized executor goes to ``__init__.py``
        - to import ``foo.py``, you should use relative import, e.g. ``from .foo import bar``

    This is not a recommended structure because:
        - putting core logic inside ``__init__.py`` is not how python packages
          are usually written
        - Importing from the workspace disables you from trying out the executor in
          the console, or test files at the root of the workspace, making development
          more cumbersome
        - the main directory is now cluttered with python files
        - extracting all python files to a separate directory is how python packages
          are usually composed

    File structure:

         my_cust_module
           |- __init__.py
           |- helper.py
           |- config.yml
                |- py_modules
                       |- __init__.py
    """
    b = BaseExecutor.load_config('good_old/crafter.yml')
    assert b.__class__.__name__ == 'GoodCrafterOld'


def test_import_casual_structure_should_fail():
    # this structure is a copy-paste from
    # https://github.com/jina-ai/jina/issues/1546#issuecomment-751481422
    with pytest.raises(ImportError):
        BaseExecutor.load_config('bad1/crafter.yml')
