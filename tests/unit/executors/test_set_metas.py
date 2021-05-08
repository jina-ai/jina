from jina.executors import BaseExecutor


def test_exec_from_python():
    be = BaseExecutor(metas={'name': 'hello', 'random_name': 'random_value'})
    assert be.metas.name == 'hello'
    assert be.metas.random_name == 'random_value'
