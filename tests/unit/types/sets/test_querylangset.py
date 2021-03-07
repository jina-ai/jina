import pytest

from jina.proto.jina_pb2 import RequestProto, QueryLangProto
from jina.types.querylang import QueryLang
from jina.types.sets.querylang import QueryLangSet


@pytest.fixture(scope='function')
def querylang_protos():
    """:returns: A :class:`RepeatedCompositeContainer` consist list of :class:`QueryLangProto`."""
    req = RequestProto()
    for _ in range(3):
        req.queryset.extend([QueryLangProto()])
    return req.queryset


@pytest.fixture(scope='function')
def querylang_set(querylang_protos):
    """:returns: A :class:`RepeatedCompositeContainer` consist list of :class:`QueryLangProto`."""
    return QueryLangSet(querylang_protos=querylang_protos)


@pytest.fixture(scope='function')
def querylang_instance():
    """:returns: An instance of :class:`QueryLang`."""
    query_lang = QueryLang()
    query_lang.name = 'test'
    query_lang.priority = 5
    return query_lang


def test_init(querylang_protos):
    """The test function to initialize the :class:`QueryLangSet`"""
    assert QueryLangSet(querylang_protos=querylang_protos)


def test_insert(querylang_set, querylang_instance):
    """Test insert :attr:`ql` to :class:`QueryLangSet` at :attr:`index`."""
    querylang_set.insert(index=0, ql=querylang_instance)
    assert len(querylang_set) == 4
    assert querylang_set[0].name == 'test'
    assert querylang_set[0].priority == 5


def test_get_set_success(querylang_set, querylang_instance):
    """
    Test :meth:`__setitem__` and :meth:`__getitem__`  in :class`QueryLangSet`.
    :attr:`key` might blongs to type `int` or `str`.
    """
    querylang_set[0] = querylang_instance
    assert querylang_set[0].name == 'test'
    assert querylang_set[0].priority == 5
    querylang_set.build()
    querylang_set['test'] = querylang_instance
    assert querylang_set['test'].name == 'test'
    assert querylang_set['test'].priority == 5


def test_get_set_fail(querylang_set):
    """Test :meth:`__setitem__` and :meth:`__getitem__`  in :class`QueryLangSet`.

    .. note::
            Please assert pytest.rases `IndexError`
    """
    with pytest.raises(IndexError):
        querylang_set[10]
        querylang_set['not_exist']


def test_delete(querylang_set):
    """Test :meth:`__del__`, should remove value from :class:`QueryLangSet` given an index."""
    del querylang_set[0]
    assert len(querylang_set) == 2


def test_length(querylang_set):
    """Test :meth:`__len__`, should return the length of :class:`QueryLangSet`."""
    assert len(querylang_set) == 3


def test_iter(querylang_set):
    """Test :meth:`__iter__`, should yield an instance of :class:`QueryLang`."""
    for querylang in querylang_set:
        assert isinstance(querylang, QueryLang)


@pytest.mark.parametrize(
    'querylang_item',
    [QueryLangProto(), QueryLang(), {'name': 'Driver', 'parameters': {'key': 'value'}}],
)
def test_append_success_proto(querylang_set, querylang_item):
    """Test :meth:`append`. Expect test three cases depends on the type of :attr:`value`.
    Such as :class:`BaseDriver`, :class:`QueryLangProto` and :class:`QueryLang`.

    .. note::
            Please parameterize this test with pytest.mark.parameterize.
    """
    querylang_set.append(querylang_item)
    assert len(querylang_set) == 4


def test_append_fail(querylang_set):
    """Test :meth:`append` with an invalid input.

    .. note::
            Please assert pytest.rases `TypeError`
    """
    with pytest.raises(TypeError):
        querylang_set.append('invalid type')


def test_extend(querylang_set, querylang_instance):
    """Test :meth:`extend`, extend an iterable to :class:`QueryLangSet`."""
    querylang_set.extend([querylang_instance])
    assert len(querylang_set) == 4
    assert querylang_set[3].name == querylang_instance.name


def test_clear(querylang_set):
    """Test :meth:`clear`, ensure length of :attr:`_querylangs_proto` is 0 after clear."""
    querylang_set.clear()
    assert len(querylang_set) == 0


def test_reverse(querylang_set, querylang_instance):
    """Test :meth:`reverse`, reverse the items in :class:`QueryLangSet`.

    .. note::
        reverse the same :class:`QueryLangSet` twice and assert they're identical.
    """
    querylang_set.append(querylang_instance)
    querylang_set.reverse()
    assert querylang_set[0].name == querylang_instance.name
    querylang_set.reverse()
    assert querylang_set[3].name == querylang_instance.name


def test_build(querylang_set):
    """Test :meth:`build`.
    Ensure the built result :attr:`_docs_map` is `dict` and the values are correct.
    """
    querylang_set.build()
