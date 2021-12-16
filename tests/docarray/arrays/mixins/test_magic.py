import pytest

from docarray import DocumentArray, DocumentArrayMemmap

N = 100


def da_and_dam():
    da = DocumentArray.empty(N)
    dam = DocumentArrayMemmap.empty(N)
    return da, dam


@pytest.mark.parametrize('da', da_and_dam())
def test_iter_len_bool(da):
    j = 0
    for _ in da:
        j += 1
    assert j == N
    assert j == len(da)
    assert da
    da.clear()
    assert not da


@pytest.mark.parametrize('da', da_and_dam())
def test_repr(da):
    assert f'length={N}' in repr(da)


@pytest.mark.parametrize('da', da_and_dam())
def test_iadd(da):
    oid = id(da)
    dap = DocumentArray.empty(10)
    da += dap
    assert len(da) == N + len(dap)
    nid = id(da)
    assert nid == oid


@pytest.mark.parametrize('da', da_and_dam())
def test_add(da):
    oid = id(da)
    dap = DocumentArray.empty(10)
    da = da + dap
    assert len(da) == N + len(dap)
    nid = id(da)
    assert nid != oid
