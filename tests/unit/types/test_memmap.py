import pytest

from jina import Document
from jina.types.arrays.memmap import DocumentArrayMemmap
from tests import random_docs


def test_memmap_append_extend(tmpdir):
    dam = DocumentArrayMemmap(tmpdir)
    docs = list(random_docs(100))
    assert len(dam) == 0
    for d in docs[:40]:
        dam.append(d)
    assert len(dam) == 40
    for d1, d2 in zip(docs[:40], dam):
        assert d1.proto == d2.proto
    dam.extend(docs[40:])
    assert len(dam) == 100
    for d1, d2 in zip(docs, dam):
        assert d1.proto == d2.proto


@pytest.mark.parametrize('idx1, idx99', [(1, 99), ('id_1', 'id_99')])
def test_memmap_delete_clear(tmpdir, mocker, idx1, idx99):
    dam = DocumentArrayMemmap(tmpdir)
    candidates = list(random_docs(100))
    for d in candidates:
        d.id = f'id_{d.id}'
    dam.extend(candidates)
    assert len(dam) == 100
    del dam[idx1]
    assert len(dam) == 99
    del dam[idx99]
    assert len(dam) == 98
    for d in dam:
        assert d.id != idx1
        assert d.id != idx99
    dam.clear()
    assert len(dam) == 0
    mock = mocker.Mock()
    for _ in dam:
        mock()
    mock.assert_not_called()


@pytest.mark.parametrize('idx1, idx99', [(1, 99), ('id_1', 'id_99')])
def test_get_set_item(tmpdir, idx1, idx99):
    dam = DocumentArrayMemmap(tmpdir)
    candidates = list(random_docs(100))
    for d in candidates:
        d.id = f'id_{d.id}'
    dam.extend(candidates)
    dam[idx1] = Document(text='hello')
    assert len(dam) == 100
    with pytest.raises(IndexError):
        dam[100] = Document(text='world')
    dam[idx99] = Document(text='world')
    assert len(dam) == 100
    assert dam[1].text == 'hello'
    assert dam[99].text == 'world'
    for idx, d in enumerate(dam):
        if idx == 1:
            assert d.text == 'hello'
        if idx == 99:
            assert d.text == 'world'
    dam['unknown_new'] = Document()
    assert len(dam) == 101


def test_traverse(tmpdir, mocker):
    dam = DocumentArrayMemmap(tmpdir)
    dam.extend(random_docs(100))
    mock = mocker.Mock()
    for c in dam.traverse_flat('c'):
        assert c.granularity == 1
        mock()
    mock.assert_called()


@pytest.mark.parametrize('content_field', ['embedding', 'text'])
def test_get_attributes(tmpdir, content_field):
    dam = DocumentArrayMemmap(tmpdir)
    dam.extend(random_docs(100))
    contents, docs = dam.get_attributes_with_docs(content_field)
    assert len(contents) == 100
    assert len(docs) == 100


def test_error(tmpdir):
    dam = DocumentArrayMemmap(tmpdir)
    dam.clear()
    with pytest.raises(KeyError):
        dam['12']
    with pytest.raises(IndexError):
        dam[1]
    with pytest.raises(IndexError):
        del dam[1]
    with pytest.raises(KeyError):
        del dam['12']


def test_persist(tmpdir):
    dam = DocumentArrayMemmap(tmpdir)
    dam.extend(random_docs(100))

    dam2 = DocumentArrayMemmap(tmpdir)
    assert len(dam2) == 100

    for d1, d2 in zip(dam, dam2):
        assert d1.proto == d2.proto

    dam.clear()
    assert len(dam2) == 100
    dam2.reload()
    assert len(dam2) == 0
