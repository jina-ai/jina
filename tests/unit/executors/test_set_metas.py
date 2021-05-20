from types import SimpleNamespace

from jina.executors import BaseExecutor


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
