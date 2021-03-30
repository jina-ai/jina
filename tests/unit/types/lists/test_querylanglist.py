import pytest

from jina.proto.jina_pb2 import RequestProto, QueryLangProto
from jina.types.querylang import QueryLang
from jina.types.lists.querylang import QueryLangList


@pytest.fixture(scope='function')
def querylang_protos():
    """:return:: A :class:`RepeatedCompositeContainer` consist list of :class:`QueryLangProto`."""
    req = RequestProto()
    for _ in range(3):
        req.queryset.extend([QueryLangProto()])
    return req.queryset


@pytest.fixture(scope='function')
def querylang_list(querylang_protos):
    """:return:: A :class:`RepeatedCompositeContainer` consist list of :class:`QueryLangProto`."""
    return QueryLangList(querylang_protos=querylang_protos)


@pytest.fixture(scope='function')
def querylang_instance():
    """:return:: An instance of :class:`QueryLang`."""
    query_lang = QueryLang()
    query_lang.name = 'test'
    query_lang.priority = 5
    return query_lang


def test_init(querylang_protos):
    """The test function to initialize the :class:`QueryLangList`"""
    assert QueryLangList(querylang_protos=querylang_protos)


def test_insert(querylang_list, querylang_instance):
    """Test insert :attr:`ql` to :class:`QueryLangList` at :attr:`index`."""
    querylang_list.insert(index=0, ql=querylang_instance)
    assert len(querylang_list) == 4
    assert querylang_list[0].name == 'test'
    assert querylang_list[0].priority == 5


def test_get_list_success(querylang_list, querylang_instance):
    """
    Test :meth:`__listitem__` and :meth:`__getitem__`  in :class`QueryLangList`.
    :attr:`key` might blongs to type `int` or `str`.
    """
    querylang_list[0] = querylang_instance
    assert querylang_list[0].name == 'test'
    assert querylang_list[0].priority == 5
    querylang_list.build()
    querylang_list['test'] = querylang_instance
    assert querylang_list['test'].name == 'test'
    assert querylang_list['test'].priority == 5


def test_get_list_fail(querylang_list):
    """Test :meth:`__listitem__` and :meth:`__getitem__`  in :class`QueryLangList`.

    .. note::
            Please assert pytest.rases `IndexError`
    """
    with pytest.raises(IndexError):
        querylang_list[10]
        querylang_list['not_exist']


def test_delete(querylang_list):
    """Test :meth:`__del__`, should remove value from :class:`QueryLangList` given an index."""
    del querylang_list[0]
    assert len(querylang_list) == 2


def test_length(querylang_list):
    """Test :meth:`__len__`, should return the length of :class:`QueryLangList`."""
    assert len(querylang_list) == 3


def test_iter(querylang_list):
    """Test :meth:`__iter__`, should yield an instance of :class:`QueryLang`."""
    for querylang in querylang_list:
        assert isinstance(querylang, QueryLang)


@pytest.mark.parametrize(
    'querylang_item',
    [QueryLangProto(), QueryLang(), {'name': 'Driver', 'parameters': {'key': 'value'}}],
)
def test_append_success_proto(querylang_list, querylang_item):
    """Test :meth:`append`. Expect test three cases depends on the type of :attr:`value`.
    Such as :class:`BaseDriver`, :class:`QueryLangProto` and :class:`QueryLang`.

    .. note::
            Please parameterize this test with pytest.mark.parameterize.
    """
    querylang_list.append(querylang_item)
    assert len(querylang_list) == 4


def test_append_fail(querylang_list):
    """Test :meth:`append` with an invalid input.

    .. note::
            Please assert pytest.rases `TypeError`
    """
    with pytest.raises(TypeError):
        querylang_list.append('invalid type')


def test_extend(querylang_list, querylang_instance):
    """Test :meth:`extend`, extend an iterable to :class:`QueryLangList`."""
    querylang_list.extend([querylang_instance])
    assert len(querylang_list) == 4
    assert querylang_list[3].name == querylang_instance.name


def test_clear(querylang_list):
    """Test :meth:`clear`, ensure length of :attr:`_querylangs_proto` is 0 after clear."""
    querylang_list.clear()
    assert len(querylang_list) == 0


def test_reverse(querylang_list, querylang_instance):
    """Test :meth:`reverse`, reverse the items in :class:`QueryLangList`.

    .. note::
        reverse the same :class:`QueryLangList` twice and assert they're identical.
    """
    querylang_list.append(querylang_instance)
    querylang_list.reverse()
    assert querylang_list[0].name == querylang_instance.name
    querylang_list.reverse()
    assert querylang_list[3].name == querylang_instance.name


def test_build(querylang_list):
    """Test :meth:`build`.
    Ensure the built result :attr:`_docs_map` is `dict` and the values are correct.
    """
    querylang_list.build()
