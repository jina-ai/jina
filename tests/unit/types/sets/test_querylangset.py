import pytest

def test_init():
    """The test function to initialize the :class:`QueryLangSet`"""
    pass

def test_insert():
    """Test insert :attr:`ql` to :class:`QueryLangSet` at :attr:`index`."""
    pass

def test_get_set_success():
    """
    Test :meth:`__setitem__` and :meth:`__getitem__`  in :class`QueryLangSet`.
    :attr:`key` might blongs to type `int` or `str`.

    .. note::
            Please parameterize this test with pytest.mark.parameterize.
    """
    pass

def test_get_set_fail():
    """Test :meth:`__setitem__` and :meth:`__getitem__`  in :class`QueryLangSet`.

    .. note::
            Please assert pytest.rases `IndexError`
    """
    pass

def test_delete():
    """Test :meth:`__del__`, should remove value from :class:`QueryLangSet` given an index."""
    pass

def test_length():
    """Test :meth:`__len__`, should return the length of :class:`QueryLangSet`."""
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

def test_append_fail():
    """Test :meth:`append` with an invalid input.

    .. note::
            Please assert pytest.rases `TypeError`
    """
    pass

def test_extend():
    """Test :meth:`extend`, extend an iterable to :class:`QueryLangSet`."""
    pass

def test_clear():
    """Test :meth:`clear`, ensure length of :attr:`_querylangs_proto` is 0 after clear."""
    pass

def test_reverse():
    """Test :meth:`reverse`, reverse the items in :class:`QueryLangSet`.

    .. note::
        reverse the same :class:`QueryLangSet` twice and assert they're identical.
    """
    pass

def test_build():
    """Test :meth:`build`.
    Ensure the built result :attr:`_docs_map` is `dict` and the values are correct.
    """
    pass
