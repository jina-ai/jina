import pytest

from jina import DocumentArray, Document, DocumentArrayMemmap


def da_for_batching():
    da = DocumentArray.empty(100)
    dam = DocumentArrayMemmap.empty(100)
    return da, dam


def docarray_for_split():
    da = DocumentArray()
    da.append(Document(tags={'category': 'c'}))
    da.append(Document(tags={'category': 'c'}))
    da.append(Document(tags={'category': 'b'}))
    da.append(Document(tags={'category': 'a'}))
    da.append(Document(tags={'category': 'a'}))
    dam = DocumentArrayMemmap()
    dam.extend(da)
    return da, dam


def docarray_for_split_at_zero():
    da = DocumentArray()
    da.append(Document(tags={'category': 0.0}))
    da.append(Document(tags={'category': 0.0}))
    da.append(Document(tags={'category': 1.0}))
    da.append(Document(tags={'category': 2.0}))
    da.append(Document(tags={'category': 2.0}))
    dam = DocumentArrayMemmap()
    dam.extend(da)
    return da, dam


def docarray_for_nest_split():
    da = DocumentArray()
    da.append(Document(tags={'nest': {'category': 'c'}}))
    da.append(Document(tags={'nest': {'category': 'c'}}))
    da.append(Document(tags={'nest': {'category': 'b'}}))
    da.append(Document(tags={'nest': {'category': 'a'}}))
    da.append(Document(tags={'nest': {'category': 'a'}}))
    dam = DocumentArrayMemmap()
    dam.extend(da)
    return da, dam


@pytest.mark.parametrize('da', docarray_for_split())
def test_split(da):
    rv = da.split('category')
    assert isinstance(rv, dict)
    assert sorted(list(rv.keys())) == ['a', 'b', 'c']
    # assure order is preserved c, b, a
    assert list(rv.keys()) == ['c', 'b', 'a']
    # original input c, c, b, a, a
    assert len(rv['c']) == 2
    assert len(rv['b']) == 1
    assert len(rv['a']) == 2
    rv = da.split('random')
    assert not rv  # wrong tag returns empty dict


@pytest.mark.parametrize('da', docarray_for_split_at_zero())
def test_split_at_zero(da):
    rv = da.split('category')
    assert isinstance(rv, dict)
    assert sorted(list(rv.keys())) == [0.0, 1.0, 2.0]


@pytest.mark.parametrize('da', docarray_for_nest_split())
def test_dunder_split(da):
    rv = da.split('nest__category')
    assert isinstance(rv, dict)
    assert sorted(list(rv.keys())) == ['a', 'b', 'c']
    # assure order is preserved c, b, a
    assert list(rv.keys()) == ['c', 'b', 'a']
    # original input c, c, b, a, a
    assert len(rv['c']) == 2
    assert len(rv['b']) == 1
    assert len(rv['a']) == 2

    assert len(da.split('nest__random')) == 1


@pytest.mark.parametrize('da', da_for_batching())
@pytest.mark.parametrize('batch_size', [1, 5, 100, 200])
@pytest.mark.parametrize('shuffle', [True, False])
def test_batching(da, batch_size, shuffle):
    all_ids = []
    for v in da.batch(batch_size=batch_size, shuffle=shuffle):
        assert len(v) <= batch_size
        all_ids.extend(v.get_attributes('id'))

    if shuffle:
        assert all_ids != da.get_attributes('id')
    else:
        assert all_ids == da.get_attributes('id')
