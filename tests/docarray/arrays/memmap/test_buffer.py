import pytest

from docarray import DocumentArrayMemmap
from docarray.memmap import BufferPoolManager
from tests import random_docs


@pytest.mark.parametrize('pool_size', [10, 100, 1000])
def test_buffer_pool_size(pool_size):
    buffer_pool = BufferPoolManager(pool_size=int(pool_size / 2))
    docs = list(random_docs(pool_size))

    # in the first half, the buffer pool is empty
    for doc in docs[: int(pool_size / 2)]:
        to_persist = buffer_pool.add_or_update(doc.id, doc)
        doc.content = 'new'
        assert not to_persist

    # in the second half, the buffer pool becames full
    for i, doc in enumerate(docs[int(pool_size / 2) :]):
        to_persist = buffer_pool.add_or_update(doc.id, doc)
        assert to_persist is not None
        assert to_persist[0] == docs[i].id
        assert to_persist[1].id == docs[i].id


def test_buffer_add_or_update(tmpdir):
    buffer_pool = BufferPoolManager(pool_size=6)
    docs = list(random_docs(9))
    for doc in docs[:5]:
        buffer_pool.add_or_update(doc.id, doc)

    doc1 = docs[0]
    doc1.content = 'new'

    # doc1 already exists => update
    assert not buffer_pool.add_or_update(doc1.id, doc1)
    assert buffer_pool[doc1.id].content == doc1.content
    assert len(buffer_pool.buffer) == 5

    # doc does not exist => add to buffer
    assert not buffer_pool.add_or_update(docs[5].id, docs[5])
    assert len(buffer_pool.buffer) == 6

    # buffer is full => remove the least recently used (docs[1], because docs[0] was used before)
    # docs[1] was not changed so it will not be persisted
    assert not buffer_pool.add_or_update(docs[6].id, docs[6])
    assert docs[6].id in buffer_pool
    assert docs[1].id not in buffer_pool

    del buffer_pool[docs[4].id]

    # spot number 4 becomes empty
    assert 4 in buffer_pool._empty
    assert not buffer_pool.add_or_update(docs[7].id, docs[7])
    assert buffer_pool.doc_map[docs[7].id][0] == 4

    docs[2].content = 'new'
    key, doc = buffer_pool.add_or_update(docs[8].id, docs[8])
    assert key == docs[2].id


def test_buffer_dam_delete(tmpdir):
    buffer_pool = BufferPoolManager(pool_size=5)
    docs = list(random_docs(6))
    for doc in docs:
        buffer_pool.add_or_update(doc.id, doc)

    first_doc = docs[0]

    # the first element should be out of buffer
    with pytest.raises(KeyError):
        del buffer_pool[first_doc.id]

    # no exception
    buffer_pool.delete_if_exists(first_doc.id)
    del buffer_pool[docs[5].id]
    assert docs[5].id not in buffer_pool


def test_buffer_docs_to_flush():
    buffer_pool = BufferPoolManager(pool_size=5)
    docs = list(random_docs(10))
    for doc in docs:
        buffer_pool.add_or_update(doc.id, doc)

    docs[3].content = 'new'
    docs[7].content = 'new'
    docs[9].content = 'new'

    docs_to_flush = buffer_pool.docs_to_flush()
    assert len(docs_to_flush) == 2
    assert (docs[7].id, docs[7]) in docs_to_flush
    assert (docs[9].id, docs[9]) in docs_to_flush


def test_buffer_clear():
    buffer_pool = BufferPoolManager(pool_size=5)
    docs = list(random_docs(10))
    for doc in docs:
        buffer_pool.add_or_update(doc.id, doc)
    buffer_pool.clear()
    for doc in docs:
        assert doc.id not in buffer_pool


def test_buffer_dam_getitem(tmpdir):
    dam = DocumentArrayMemmap(tmpdir)
    docs = list(random_docs(10))
    dam.extend(docs)
    for i, doc in enumerate(docs):
        # assert same doc when getting by key
        assert dam._buffer_pool[doc.id].content_hash == doc.content_hash
        assert dam._buffer_pool[doc.id].id == doc.id

    with pytest.raises(TypeError):
        dam._buffer_pool[1:5]

    with pytest.raises(TypeError):
        dam._buffer_pool[0]


def test_buffer_dam_delete(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=5)
    docs = list(random_docs(6))
    dam.extend(docs)

    first_doc = docs[0]

    # the first element should be out of buffer
    with pytest.raises(KeyError):
        del dam._buffer_pool[first_doc.id]

    # no exception raised
    dam._buffer_pool.delete_if_exists(first_doc.id)


def test_buffer_dam_lru(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=5)
    docs = list(random_docs(6))
    dam.extend(docs[:5])

    # make the first doc most recently used, the second doc is the LRU
    doc1 = dam[0]
    assert next(reversed(dam._buffer_pool.doc_map.keys())) == doc1.id
    assert next(iter(dam._buffer_pool.doc_map.keys())) == docs[1].id

    doc2 = docs[1]

    assert doc1.id == docs[0].id
    dam.append(docs[5])

    # doc1 was not LRU, doc2 was LRU
    assert doc1.id in dam._buffer_pool
    assert doc2.id not in dam._buffer_pool
    assert docs[5].id in dam._buffer_pool


def test_buffer_dam_clear(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=5)
    docs = list(random_docs(5))
    dam.extend(docs)

    dam._buffer_pool.clear()
    for doc in docs:
        assert doc.id not in dam._buffer_pool


def test_buffer_dam_add_or_update(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=6)
    docs = list(random_docs(8))
    dam.extend(docs[:5])

    doc1 = docs[0]
    doc1.content = 'new'

    # doc1 already exists => update
    dam._buffer_pool.add_or_update(doc1.id, doc1)
    assert dam[0].content == doc1.content
    assert len(dam._buffer_pool.buffer) == 5

    # doc does not exist => add to buffer
    dam._buffer_pool.add_or_update(docs[5].id, docs[5])
    assert len(dam._buffer_pool.buffer) == 6

    # buffer is full => remove the LRU (docs[1], because docs[0] was used before)
    dam._buffer_pool.add_or_update(docs[6].id, docs[6])
    assert docs[6].id in dam._buffer_pool
    assert docs[1].id not in dam._buffer_pool

    del dam._buffer_pool[docs[4].id]

    # spot number 4 becomes empty
    assert 4 in dam._buffer_pool._empty
    dam._buffer_pool.add_or_update(docs[7].id, docs[7])
    assert dam._buffer_pool.doc_map[docs[7].id][0] == 4
