from jina import Document
from jina.types.document.set import DocumentSet
from tests import random_docs


def test_docset_init():
    # we need low-level protobuf generation for testing
    docs = list(random_docs(10))[0].chunks
    ds = DocumentSet(docs)
    assert len(docs) == len(ds)
    for d, od in zip(ds, docs):
        assert isinstance(d, Document)
        assert d.id == od.id
        assert d.text == od.text
        # they should be the same object
        assert id(d.as_pb_object) == id(od)


def test_docset_append_extend_delete():
    # we need low-level protobuf generation for testing
    docs = list(random_docs(10))[0].chunks
    old_len = len(docs)
    ds = DocumentSet(docs)
    d = Document()
    ds.append(d)
    assert len(docs) == old_len + 1
    del ds[-1]
    assert len(docs) == old_len
    ds.clear()
    assert len(ds) == 0
    assert len(docs) == 0
    ds.extend(Document() for _ in range(10))
    assert len(docs) == 10


def test_docset_iterate_twice():
    docs = list(random_docs(10))[0].chunks
    ds = DocumentSet(docs)
    j = 0
    for _ in ds:
        for _ in ds:
            j += 1
    assert j == len(ds) ** 2

def test_docset_reverse():
    docs = list(random_docs(10))[0].chunks
    ids = [d.id for d in docs]
    ds = DocumentSet(docs)
    ds.reverse()
    ids2 = [d.id for d in ds]
    assert list(reversed(ids)) == ids2


