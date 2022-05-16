import os

import pytest

from jina import Flow, __default_executor__, requests
from jina.excepts import BadConfigSource
from jina.jaml import JAML, JAMLCompatible
from jina.serve.executors import BaseExecutor


class MyExecutor(BaseExecutor):
    pass


def test_non_empty_reg_tags():
    assert JAML.registered_tags()
    assert __default_executor__ in JAML.registered_tags()


@pytest.mark.parametrize(
    'include_unk, expected',
    [
        (
            True,
            '''
jtype: BaseExecutor {}
jtype: Blah {}
''',
        ),
        (
            False,
            '''
jtype: BaseExecutor {}
!Blah {}
''',
        ),
    ],
)
def test_include_unknown(include_unk, expected):
    y = '''
!BaseExecutor {}
!Blah {}
    '''
    assert JAML.escape(y, include_unknown_tags=include_unk).strip() == expected.strip()


@pytest.mark.parametrize(
    'original, escaped',
    [
        (
            '''
!BaseExecutor {}
!Blah {}
!MyExecutor {}
                                 ''',
            '''
jtype: BaseExecutor {}
!Blah {}
jtype: MyExecutor {}
                                 ''',
        ),
        (
            '''
!BaseExecutor
with:
    a: 123
    b: BaseExecutor
    jtype: unknown-blah
                                 ''',
            '''
jtype: BaseExecutor
with:
    a: 123
    b: BaseExecutor
    jtype: unknown-blah
                                 ''',
        ),
    ],
)
def test_escape(original, escaped):
    assert JAML.escape(original, include_unknown_tags=False).strip() == escaped.strip()
    assert (
        JAML.unescape(
            JAML.escape(original, include_unknown_tags=False),
            include_unknown_tags=False,
        ).strip()
        == original.strip()
    )


class MyExec(BaseExecutor):
    @requests
    def foo(self, **kwargs):
        pass


def test_cls_from_tag():
    assert JAML.cls_from_tag('MyExec') == MyExec
    assert JAML.cls_from_tag('!MyExec') == MyExec
    assert JAML.cls_from_tag('BaseExecutor') == BaseExecutor
    assert JAML.cls_from_tag('Nonexisting') is None


@pytest.mark.parametrize(
    'field_name, override_field',
    [
        ('with', None),
        ('metas', None),
        ('requests', None),
        ('with', {'a': 456, 'b': 'updated-test'}),
        (
            'metas',
            {'name': 'test-name-updated', 'workspace': 'test-work-space-updated'},
        ),
        ('requests', {'/foo': 'baz'}),
        # assure py_modules only occurs once #3830
        (
            'metas',
            {
                'name': 'test-name-updated',
                'workspace': 'test-work-space-updated',
                'py_modules': 'test_module.py',
            },
        ),
    ],
)
def test_override_yml_params(field_name, override_field):
    original_raw_yaml = {
        'jtype': 'SimpleIndexer',
        'with': {'a': 123, 'b': 'test'},
        'metas': {'name': 'test-name', 'workspace': 'test-work-space'},
        'requests': {'/foo': 'bar'},
    }
    updated_raw_yaml = original_raw_yaml
    JAMLCompatible()._override_yml_params(updated_raw_yaml, field_name, override_field)
    if override_field:
        assert updated_raw_yaml[field_name] == override_field
    else:
        assert original_raw_yaml == updated_raw_yaml
    # assure we don't create py_modules twice
    if override_field == 'metas' and 'py_modules' in override_field:
        assert 'py_modules' in updated_raw_yaml['metas']
        assert 'py_modules' not in updated_raw_yaml


class EnvironmentVarCtxtManager:
    def __init__(self, envs):
        self._env_keys_added = envs

    def __enter__(self):
        for key, val in self._env_keys_added.items():
            os.environ[key] = str(val)

    def __exit__(self, exc_type, exc_val, exc_tb):
        for key in self._env_keys_added.keys():
            os.unsetenv(key)


def test_parsing_brackets_in_envvar():
    flow_yaml = '''
    jtype: Flow
    executors:
    - name: a
      env:
        var1: ${{ env.VAR1 }}
        var4: -${{ env.VAR1 }}
        var2: ${{root.executors[0].name}}
        var3: ${{ env.VAR1 }}-${{root.executors[0].name}}

    '''

    with EnvironmentVarCtxtManager(
        envs={
            'VAR1': '{"1": "2"}',
        }
    ):

        b = JAML.load(flow_yaml, substitute=True)
        assert b['executors'][0]['env']['var1'] == '{"1": "2"}'
        assert b['executors'][0]['env']['var2'] == 'a'
        assert b['executors'][0]['env']['var3'] == '{"1": "2"}-a'
        assert b['executors'][0]['env']['var4'] == '-{"1": "2"}'


def test_exception_invalid_yaml():
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    yaml = os.path.join(cur_dir, 'invalid.yml')
    with pytest.raises(BadConfigSource):
        BaseExecutor.load_config(yaml)

    with pytest.raises(BadConfigSource):
        Flow.load_config(yaml)
