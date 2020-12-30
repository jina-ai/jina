import pytest

from jina import Document
from jina.drivers.querylang.queryset.dunderkey import (
    dunderkey,
    dunder_init,
    dunder_get,
    dunder_partition,
    undunder_keys,
    dunder_truncate,
)


def test_dunderkey():
    assert dunderkey('a', 'b', 'c') == 'a__b__c'

def test_dunder_init():
    assert dunder_init('a__b__c') == 'a__b'

def test_dunder_get():
    assert dunder_get({'a': {'b': 5}}, 'a__b') == 5
    assert dunder_get({'a': {'b': 8, 'c': {'d': 8}}}, 'a__c__d') == 8
    assert dunder_get([1, 2, 3, [4, 5, [6]]], '3__1') == 5

    class B:
        c = 5

    class A:
        b = B

    assert dunder_get(A, 'b__c') == 5

    with Document() as d:
        d.tags['a'] = 'hello'
        assert dunder_get(d, 'tags__a') == 'hello'

    # Error on invalid key

    assert dunder_get({'a': {'b': 5}}, 'a__c') is None
    # Error if key is too nested
    with pytest.raises(Exception):
        dunder_get({'a': {'b': 5}, 'c': 8}, 'a__b__c')
    # Error using str keys on list
    with pytest.raises(Exception):
        dunder_get([[1, 2], [3, 4]], 'a')


def test_dunder_partition():
    assert dunder_partition('a') == ('a', None)
    assert dunder_partition('a__b') == ('a', 'b')
    assert dunder_partition('a__b__c') == ('a__b', 'c')


def test_undunder_keys():
    assert undunder_keys({'a__b': 5, 'a__c': 6, 'x': 7}) == {'a': {'b': 5, 'c': 6}, 'x': 7}
    assert undunder_keys({'a__b__c__d': 5}) == {'a': {'b': {'c': {'d': 5}}}}

    # Error when value should be both dict and int
    with pytest.raises(Exception):
        undunder_keys({'a__b__c': 5, 'a__b': 4})
    with pytest.raises(Exception):
        undunder_keys({'a__b': 5, 'a__b__c': 4})


def test_dunder_truncate():
    '''
    test with unique keys
    test with nonunique keys
    test with nonunique keys that are nested lvl 3
    '''
    assert dunder_truncate({'a__b': 5, 'a__c': 6}) == {'b': 5, 'c': 6}
    assert dunder_truncate({'a__b': 5, 'c__b': 6}) == {'a__b': 5, 'c__b': 6}

    # Does not partially truncate keys
    assert dunder_truncate({'a__b__c': 5, 'a__d__c': 6}) == {'a__b__c': 5, 'a__d__c': 6}
