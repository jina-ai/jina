from types import SimpleNamespace

from jina.serve.executors import BaseExecutor


def test_exec_from_python():
    be = BaseExecutor(metas={'name': 'hello', 'random_name': 'random_value'})
    assert be.metas.name == 'hello'
    assert be.metas.random_name == 'random_value'


def test_runtime_args():
    b = BaseExecutor.load_config(
        'BaseExecutor', metas={'name': 'b123'}, runtime_args={'hello': 'world'}
    )

    assert b.runtime_args.hello == 'world'
    assert b.metas.name == 'b123'


def test_default_args_from_load_config():
    b = BaseExecutor.load_config('!BaseExecutor {}')

    assert isinstance(b.runtime_args, SimpleNamespace)
    assert isinstance(b.metas, SimpleNamespace)
    # name is always auto-assigned
    assert b.metas.name


def test_runtime_args_from_load_config():
    y = '''
!BaseExecutor
metas:
  name: my-mwu-encoder
  workspace: ./
    '''

    b = BaseExecutor.load_config(y)

    assert b.metas.workspace == './'
    assert b.metas.name == 'my-mwu-encoder'


def test_default_args_from_python():
    b = BaseExecutor()

    assert isinstance(b.runtime_args, SimpleNamespace)
    assert isinstance(b.metas, SimpleNamespace)
    # name is always auto-assigned
    assert b.metas.name


def test_name_python_jaml_identical():
    # There are two different ways of importing the executors in jina 2.0.
    # We want the executors to have the same metas.name field regardless of
    # the way they were imported!

    # First way of import using py_modules argument in jaml file
    from jina.jaml.helper import load_py_modules

    load_py_modules({'py_modules': ['metas_executors.py']})
    from metas_executors import TestExecutor

    jaml_executor = TestExecutor()
    jaml_metas_name = jaml_executor.metas.name

    # Second way of importing directly via path in python
    from .metas_executors import TestExecutor

    py_executor = TestExecutor()
    py_metas_name = py_executor.metas.name

    # Make sure that the executor meta name is equal to only the class name
    assert jaml_metas_name == 'TestExecutor'
    assert py_metas_name == 'TestExecutor'

    # Make sure that the executor can be loaded from a native python module path as well
    load_py_modules({'py_modules': ['metas_executors']})
