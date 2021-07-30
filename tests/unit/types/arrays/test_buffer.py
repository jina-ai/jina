import pytest

from jina.types.arrays.memmap import DocumentArrayMemmap
from tests import random_docs


def test_buffer_getitem(tmpdir):
    dam = DocumentArrayMemmap(tmpdir)
    docs = list(random_docs(10))
    dam.extend(docs)
    for i, doc in enumerate(docs):
        # assert same doc when getting by key
        assert dam.buffer_pool[doc.id].content_hash == doc.content_hash
        assert dam.buffer_pool[doc.id].id == doc.id

        # assert same doc when getting by index
        assert dam.buffer_pool[i].content_hash == doc.content_hash
        assert dam.buffer_pool[i].id == doc.id

    with pytest.raises(TypeError):
        dam.buffer_pool[1:5]


def test_buffer_delete(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=5)
    docs = list(random_docs(6))
    dam.extend(docs)

    first_doc = docs[0]

    # the first element should be out of buffer
    with pytest.raises(KeyError):
        del dam.buffer_pool[first_doc.id]

    # no exception raised
    dam.buffer_pool.delete_if_exists(first_doc.id)


def test_buffer_lru(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=5)
    docs = list(random_docs(6))
    dam.extend(docs[:5])

    # make the first doc most recently used, the second doc is the LRU
    doc1 = dam[0]
    assert next(reversed(dam.buffer_pool.doc_map.keys())) == doc1.id
    assert next(iter(dam.buffer_pool.doc_map.keys())) == docs[1].id

    doc2 = docs[1]

    assert doc1.id == docs[0].id
    dam.append(docs[5])

    # doc1 was not LRU, doc2 was LRU
    assert doc1.id in dam.buffer_pool
    assert doc2.id not in dam.buffer_pool
    assert docs[5].id in dam.buffer_pool


def test_buffer_clear(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=5)
    docs = list(random_docs(5))
    dam.extend(docs)

    dam.buffer_pool.clear()
    for doc in docs:
        assert doc.id not in dam.buffer_pool


def test_buffer_add_or_update(tmpdir):
    dam = DocumentArrayMemmap(tmpdir, buffer_pool_size=6)
    docs = list(random_docs(8))
    dam.extend(docs[:5])

    doc1 = docs[0]
    doc1.content = 'new'

    # doc1 already exists => update
    dam.buffer_pool.add_or_update(doc1.id, doc1)
    assert dam[0].content == doc1.content
    assert len(dam.buffer_pool.buffer) == 5

    # doc does not exist => add to buffer
    dam.buffer_pool.add_or_update(docs[5].id, docs[5])
    assert len(dam.buffer_pool.buffer) == 6

    # buffer is full => remove the LRU (docs[1], because docs[0] was used before)
    dam.buffer_pool.add_or_update(docs[6].id, docs[6])
    assert docs[6].id in dam.buffer_pool
    assert docs[1].id not in dam.buffer_pool

    del dam.buffer_pool[docs[4].id]

    # sport number 4 becomes empty
    assert 4 in dam.buffer_pool._empty
    dam.buffer_pool.add_or_update(docs[7].id, docs[7])
    assert dam.buffer_pool.doc_map[docs[7].id][0] == 4
