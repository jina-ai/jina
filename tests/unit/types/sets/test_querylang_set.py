import pytest

def test_init():
    """The test function to initialize the :class:`QueryLangSet`"""
    pass

def test_insert():
    """Test insert :attr:`ql` to :attr:`_querylangs_proto` at :attr:`index`."""
    pass

def test_get_set_success():
    """Test :meth:`__setitem__` and :meth:`__getitem__`  in :class`QueryLangSet`.
    If the key is instance of int, update :attr:`_querylangs_proto`, else, update :attr:`_querylangs_map`.
    """
    pass

def test_set_fail():
    """Test :meth:`__setitem__` and :meth:`__getitem__`  in :class`QueryLangSet`.
    Should raise `IndexError` given invalid key.
    """
    pass

def test_delete():
    """Test :meth:`__del__`, should remove value from :attr:`_querylangs_proto` given an index."""
    pass

def test_length():
    """Test :meth:`__len__`, should return the length of :attr:`_querylangs_proto`."""
    pass

def test_iter():
    """Test :meth:`__iter__`, should yield an instance of :class:`QueryLang`."""
    pass

def test_append_success():
    """Test :meth:`append`. Expect test three cases depends on the type of :attr:`value`.
    Such as :class:`BaseDriver`, :class:`QueryLangProto` and :class:`QueryLang`.

    .. note::
            Please parameterize this test with pytest.mark.parameterize.
    """
    pass

def test_extend():
    """Test :meth:`extend`, extend an iterable to :class:`QueryLangSet`."""
    pass

def test_clear():
    """Test :meth:`clear`, ensure length of :attr:`_querylangs_proto` is 0."""
    pass

def test_reverse():
    """Test :meth:`reverse`, reverse the items in :attr:`_querylangs_proto`.

    .. note::
        reverse the same :attr:`_querylangs_proto` twice and assert they're identical.
    """
    pass

def test_build():
    """Test :meth:`build`.
    Ensure the built result :attr:`_docs_map` is `dict` and the values are correct.
    """
    pass
