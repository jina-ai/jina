import pytest

from jina import Executor, Flow


class MyExecutor(Executor):
    def __init__(self, foo=50, *args, **kwargs):
        print(foo)
        super().__init__(*args, **kwargs)


def test_flow_with_warnings():
    yaml = '''jtype: Flow
version: 1
with:
    foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow.load_config(yaml)
    assert len(record) == 1
    assert record[0].message.args[0].startswith('ignored unknown')


def test_executor_warnings():
    yaml = '''jtype: Flow
version: 1
executors:
    - foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow.load_config(yaml)
    assert len(record) == 1
    assert record[0].message.args[0].startswith('ignored unknown')


def test_executor_with_warnings():
    yaml = '''jtype: Flow
version: 1
executors:
    - with:
        foo: bar
    '''
    with pytest.warns(UserWarning, match='ignored unknown') as record:
        Flow.load_config(yaml)
    assert len(record) == 1
    assert record[0].message.args[0].startswith('ignored unknown')


def test_executor_uses_with_works():
    yaml = '''jtype: Flow
version: 1
executors:
    - uses_with:
        foo: bar
    '''
    with pytest.warns(None, match='ignored unknown') as record:
        Flow.load_config(yaml)
    assert len(record) == 0


def test_executor_override_with_warnings():
    yaml = '''jtype: Flow
version: 1
executors:
    - override_with: 1
    '''
    with pytest.warns(None, match='ignored unknown') as record:
        Flow.load_config(yaml)
    assert len(record) == 1


def test_executor_metas_works():
    yaml = '''jtype: Flow
version: 1
executors:
    - uses:
        jtype: BaseExecutor
        metas:
            name: MyExecutor
    '''
    with pytest.warns(None, match='ignored unknown') as record:
        with Flow.load_config(yaml):
            pass
    assert len(record) == 0


def test_children_should_not_warn_inherited_kwargs_from_parent():
    with pytest.warns(None, match='ignored unknown') as record:
        with Flow(protocol='http', description='test').add():
            pass
    assert len(record) == 0


def test_parent_should_not_warn_inheriting_kwargs_to_children():
    with pytest.warns(None, match='ignored unknown') as record:
        with Flow(gpus='all').add():
            pass
    assert len(record) == 0


def test_warn_real_unknown_kwargs():
    with pytest.warns(None, match='ignored unknown') as record:
        with Flow(abcdefg='http').add():
            pass
    # two times warnings, 1. in Flow.init, second time in .add()
    assert len(record) == 2

    with pytest.warns(None, match='ignored unknown') as record:
        with Flow(abcdefg='http').add().add():
            pass
    # same here but three times warnings
    assert len(record) == 3
