import pytest

from jina import Flow, Executor


class MyExecutor(Executor):
    def __init__(self, foo=50, *args, **kwargs):
        print(foo)
        super().__init__(*args, **kwargs)


def test_flow_warnings():
    yaml = '''jtype: Flow
version: 1
foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow().load_config(yaml)
    assert len(record) == 1
    assert record[0].message.args[0].startswith('ignored unknown')


def test_flow_with_warnings():
    yaml = '''jtype: Flow
version: 1
with:
    foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow().load_config(yaml)
    assert len(record) == 2
    assert record[0].message.args[0].startswith('ignored unknown')


def test_executor_warnings():
    yaml = '''jtype: Flow
version: 1
executors:
    - foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow().load_config(yaml)
    assert len(record) == 2
    assert record[0].message.args[0].startswith('ignored unknown')


def test_executor_with_warnings():
    yaml = '''jtype: Flow
version: 1
executors:
    - with:
        foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow().load_config(yaml)
    assert len(record) == 2
    assert record[0].message.args[0].startswith('ignored unknown')


def test_executor_uses_with_works():
    yaml = '''jtype: Flow
version: 1
executors:
    - uses_with:
        foo: bar
    '''
    with pytest.warns(None, match='ignored unknown') as record:
        Flow().load_config(yaml)
    assert len(record) == 0
