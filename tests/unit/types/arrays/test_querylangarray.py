import pytest

from jina.proto.jina_pb2 import RequestProto, QueryLangProto
from jina.types.querylang import QueryLang
from jina.types.arrays.querylang import QueryLangArray


@pytest.fixture(scope='function')
def querylang_protos():
    """:return:: A :class:`RepeatedCompositeContainer` consist list of :class:`QueryLangProto`."""
    req = RequestProto()
    for _ in range(3):
        req.queryset.extend([QueryLangProto()])
    return req.queryset


@pytest.fixture(scope='function')
def querylang_array(querylang_protos):
    """:return:: A :class:`RepeatedCompositeContainer` consist list of :class:`QueryLangProto`."""
    return QueryLangArray(querylang_protos=querylang_protos)


@pytest.fixture(scope='function')
def querylang_instance():
    """:return:: An instance of :class:`QueryLang`."""
    query_lang = QueryLang()
    query_lang.name = 'test'
    query_lang.priority = 5
    return query_lang


def test_init(querylang_protos):
    """The test function to initialize the :class:`QueryLangArray`"""
    assert QueryLangArray(querylang_protos=querylang_protos)


def test_insert(querylang_array, querylang_instance):
    """Test insert :attr:`ql` to :class:`QueryLangArray` at :attr:`index`."""
    querylang_array.insert(index=0, ql=querylang_instance)
    assert len(querylang_array) == 4
    assert querylang_array[0].name == 'test'
    assert querylang_array[0].priority == 5


def test_get_array_success(querylang_array, querylang_instance):
    """
    Test :meth:`__listitem__` and :meth:`__getitem__`  in :class`QueryLangArray`.
    :attr:`key` might blongs to type `int` or `str`.
    """
    querylang_array[0] = querylang_instance
    assert querylang_array[0].name == 'test'
    assert querylang_array[0].priority == 5
    querylang_array.build()
    querylang_array['test'] = querylang_instance
    assert querylang_array['test'].name == 'test'
    assert querylang_array['test'].priority == 5


def test_get_array_fail(querylang_array):
    """Test :meth:`__listitem__` and :meth:`__getitem__`  in :class`QueryLangArray`.

    .. note::
            Please assert pytest.rases `IndexError`
    """
    with pytest.raises(IndexError):
        querylang_array[10]
        querylang_array['not_exist']


def test_delete(querylang_array):
    """Test :meth:`__del__`, should remove value from :class:`QueryLangArray` given an index."""
    del querylang_array[0]
    assert len(querylang_array) == 2


def test_length(querylang_array):
    """Test :meth:`__len__`, should return the length of :class:`QueryLangArray`."""
    assert len(querylang_array) == 3


def test_iter(querylang_array):
    """Test :meth:`__iter__`, should yield an instance of :class:`QueryLang`."""
    for querylang in querylang_array:
        assert isinstance(querylang, QueryLang)


@pytest.mark.parametrize(
    'querylang_item',
    [QueryLangProto(), QueryLang(), {'name': 'Driver', 'parameters': {'key': 'value'}}],
)
def test_append_success_proto(querylang_array, querylang_item):
    """Test :meth:`append`. Expect test three cases depends on the type of :attr:`value`.
    Such as :class:`BaseDriver`, :class:`QueryLangProto` and :class:`QueryLang`.

    .. note::
            Please parameterize this test with pytest.mark.parameterize.
    """
    querylang_array.append(querylang_item)
    assert len(querylang_array) == 4


def test_append_fail(querylang_array):
    """Test :meth:`append` with an invalid input.

    .. note::
            Please assert pytest.rases `TypeError`
    """
    with pytest.raises(TypeError):
        querylang_array.append('invalid type')


def test_extend(querylang_array, querylang_instance):
    """Test :meth:`extend`, extend an iterable to :class:`QueryLangArray`."""
    querylang_array.extend([querylang_instance])
    assert len(querylang_array) == 4
    assert querylang_array[3].name == querylang_instance.name


def test_clear(querylang_array):
    """Test :meth:`clear`, ensure length of :attr:`_querylangs_proto` is 0 after clear."""
    querylang_array.clear()
    assert len(querylang_array) == 0


def test_reverse(querylang_array, querylang_instance):
    """Test :meth:`reverse`, reverse the items in :class:`QueryLangArray`.

    .. note::
        reverse the same :class:`QueryLangArray` twice and assert they're identical.
    """
    querylang_array.append(querylang_instance)
    querylang_array.reverse()
    assert querylang_array[0].name == querylang_instance.name
    querylang_array.reverse()
    assert querylang_array[3].name == querylang_instance.name


def test_build(querylang_array):
    """Test :meth:`build`.
    Ensure the built result :attr:`_docs_map` is `dict` and the values are correct.
    """
    querylang_array.build()
