import pytest

from jina.enums import SocketType
from jina.executors import BaseExecutor
from jina.jaml import JAML
from jina import __default_executor__


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


def test_enum_dump():
    assert JAML.dump(SocketType.PUSH_CONNECT).strip() == '"PUSH_CONNECT"'
